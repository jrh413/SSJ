// cir-publish: turns pending Catholic in Recovery reflections (table ssj_cir_reflections)
// into a one-page PDF, files it in Documents (like a Tasking Order / After Action Report),
// and links it from that Saturday's calendar entry. Idempotent: only rows with no file_path.
import { createClient } from 'npm:@supabase/supabase-js@2.45.4';
import { PDFDocument, StandardFonts, rgb } from 'npm:pdf-lib@1.17.1';

const sb = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!);
const OX = rgb(0.42, 0.12, 0.12), INK = rgb(0.1, 0.086, 0.07), BRASS = rgb(0.6, 0.47, 0.2), CREAM = rgb(0.957, 0.922, 0.839);

function wrap(text: string, font: any, size: number, width: number): string[] {
  const out: string[] = [];
  for (const para of String(text || '').split(/\n/)) {
    let line = '';
    for (const w of para.split(/\s+/).filter(Boolean)) {
      const t = line ? line + ' ' + w : w;
      if (font.widthOfTextAtSize(t, size) > width && line) { out.push(line); line = w; } else line = t;
    }
    out.push(line);
  }
  return out;
}
const clean = (s: string) => String(s || '').replace(/[‘’]/g, "'").replace(/[“”]/g, '"').replace(/[–—]/g, '-').replace(/…/g, '...').replace(/[^\x20-\x7E\n]/g, '');

async function build(r: any): Promise<Uint8Array> {
  const pdf = await PDFDocument.create();
  const page = pdf.addPage([612, 792]);
  const serif = await pdf.embedFont(StandardFonts.TimesRoman), bold = await pdf.embedFont(StandardFonts.TimesRomanBold), ital = await pdf.embedFont(StandardFonts.TimesRomanItalic);
  page.drawRectangle({ x: 0, y: 0, width: 612, height: 792, color: CREAM });
  page.drawRectangle({ x: 0, y: 742, width: 612, height: 50, color: INK });
  page.drawText('SCHOOL OF SAINT JOSEPH  ·  CATHOLIC IN RECOVERY'.replace('·', '-'), { x: 54, y: 762, size: 12, font: bold, color: rgb(0.91, 0.78, 0.47) });
  const sat = new Date(r.event_date + 'T12:00:00Z');
  const dateStr = sat.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
  let y = 700;
  const W = 504, X = 54;
  const draw = (lines: string[], font: any, size: number, color = INK, gap = 1.35) => { for (const l of lines) { page.drawText(l, { x: X, y, size, font, color }); y -= size * gap; } };
  draw(['Weekly Reflection'], bold, 28, OX);
  draw([clean(dateStr) + '  -  7:00 AM'], serif, 15, INK, 1.6);
  page.drawLine({ start: { x: X, y: y + 6 }, end: { x: X + W, y: y + 6 }, thickness: 1.2, color: BRASS }); y -= 18;
  draw(["SUNDAY'S GOSPEL  -  " + clean(r.gospel_ref) + (r.liturgical_day ? '  (' + clean(r.liturgical_day) + ')' : '')], bold, 13, OX, 1.7);
  draw(wrap(clean(r.summary), ital, 15, W), ital, 15); y -= 10;
  draw(wrap(clean(r.body), serif, 15, W), serif, 15); y -= 12;
  draw(['QUESTION FOR SATURDAY'], bold, 13, OX, 1.7);
  draw(wrap(clean(r.question), bold, 16, W), bold, 16); y -= 14;
  if (r.resource_title) {
    draw(['GO DEEPER'], bold, 13, OX, 1.7);
    draw(wrap('Catholic in Recovery: "' + clean(r.resource_title) + '"', serif, 14, W), serif, 14);
    if (r.resource_url) draw(wrap(clean(r.resource_url).replace(/^https?:\/\//, ''), serif, 12, W), serif, 12, BRASS);
  }
  page.drawLine({ start: { x: X, y: 70 }, end: { x: X + W, y: 70 }, thickness: 0.8, color: BRASS });
  page.drawText("Saturdays 7:00 AM - McDonald's, 1150 E Clark Ave, Orcutt (next door to St. Louis de Montfort)", { x: X, y: 52, size: 11, font: serif, color: INK });
  page.drawText('Questions? Call or text Joe: (805) 310-8740', { x: X, y: 36, size: 11, font: serif, color: INK });
  return await pdf.save();
}

Deno.serve(async () => {
  const { data: rows, error } = await sb.from('ssj_cir_reflections').select('*').is('file_path', null).order('event_date');
  if (error) return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  const done: string[] = [];
  for (const r of rows || []) {
    const bytes = await build(r);
    const path = `recovery/${r.event_date}-cir-reflection.pdf`;
    const up = await sb.storage.from('ssj-documents').upload(path, bytes, { contentType: 'application/pdf', upsert: true });
    if (up.error) { done.push(r.event_date + ': upload failed ' + up.error.message); continue; }
    const md = new Date(r.event_date + 'T12:00:00Z').toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
    const title = `CIR Reflection — Sat ${md}`;
    await sb.from('ssj_documents').delete().eq('file_path', path);
    await sb.from('ssj_documents').insert({ title, file_path: path, file_name: path.split('/')[1], category: 'Catholic in Recovery', visible_to: 'brother', description: r.gospel_ref, uploaded_by: r.created_by });
    await sb.from('ssj_events').update({ url: 'doc:' + path }).eq('event_type', 'recovery').eq('event_date', r.event_date);
    await sb.from('ssj_cir_reflections').update({ file_path: path }).eq('id', r.id);
    done.push(r.event_date + ': ' + path);
  }
  return new Response(JSON.stringify({ done }), { headers: { 'Content-Type': 'application/json' } });
});
