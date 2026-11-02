// Sends a School of Saint Joseph announcement through Resend.
// Admin-only. mode "test" sends one copy to the caller; mode "send" requires confirm:"SEND TO ALL".
import 'jsr:@supabase/functions-js/edge-runtime.d.ts';
import { createClient } from 'npm:@supabase/supabase-js@2.45.4';

const RESEND_API_KEY = Deno.env.get('RESEND_API_KEY')!;
const FROM = 'School of Saint Joseph <noreply@formedtoserve.com>';
const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Authorization, Content-Type, apikey, x-client-info',
};
const json = (d: unknown, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { ...cors, 'Content-Type': 'application/json' } });

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors });
  try {
    const auth = req.headers.get('Authorization') ?? '';
    const userClient = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_ANON_KEY')!, { global: { headers: { Authorization: auth } } });
    const { data: { user } } = await userClient.auth.getUser();
    if (!user) return json({ error: 'Not signed in' }, 401);
    const { data: prof } = await userClient.from('ssj_profiles').select('role,email').eq('id', user.id).single();
    if (prof?.role !== 'admin') return json({ error: 'Admins only' }, 403);

    const { mode, subject, html, text, to, replyTo, confirm } = await req.json();
    if (!subject || !html) return json({ error: 'subject and html required' }, 400);

    let recipients: string[];
    if (mode === 'test') recipients = [prof.email];
    else if (mode === 'send') {
      if (confirm !== 'SEND TO ALL') return json({ error: 'confirm phrase missing' }, 400);
      recipients = [...new Set((to as string[]).map((e) => e.trim().toLowerCase()).filter((e) => /^[^\s@]+@[^\s@]+\.[a-z]{2,}$/.test(e)))];
    } else return json({ error: 'mode must be test or send' }, 400);

    const results: { email: string; ok: boolean; error?: string }[] = [];
    for (let i = 0; i < recipients.length; i += 90) {
      const chunk = recipients.slice(i, i + 90);
      const res = await fetch('https://api.resend.com/emails/batch', {
        method: 'POST',
        headers: { Authorization: `Bearer ${RESEND_API_KEY}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(chunk.map((email) => ({ from: FROM, to: [email], subject, html, text, reply_to: replyTo || undefined }))),
      });
      const body = await res.text();
      chunk.forEach((email) => results.push({ email, ok: res.ok, error: res.ok ? undefined : body.slice(0, 300) }));
      await new Promise((r) => setTimeout(r, 700));
    }
    return json({ sent: results.filter((r) => r.ok).length, failed: results.filter((r) => !r.ok), total: recipients.length });
  } catch (e) {
    return json({ error: String(e) }, 500);
  }
});
