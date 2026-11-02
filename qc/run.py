import asyncio, json, sys, time, pathlib
from playwright.async_api import async_playwright
from mock import Backend, session

URL = 'https://school-of-st-joseph.netlify.app/'
HARNESS = pathlib.Path('/home/claude/qc/harness.js').read_text()
OUT = pathlib.Path('/home/claude/qc/out'); OUT.mkdir(exist_ok=True)
PHONE = dict(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
             user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1')
SMALL = dict(PHONE, viewport={'width': 360, 'height': 640})   # small Android
LAPTOP = dict(viewport={'width': 1440, 'height': 900})
results = []

def log(kind, name, ok, detail=''):
    results.append(dict(kind=kind, name=name, ok=ok, detail=detail)); print(('PASS' if ok else 'FAIL'), kind, name, detail[:200], flush=True)

async def ctx(br, dev, signed_in=True, tour_done=True, **bk):
    b = Backend(**bk); c = await br.new_context(**dev); await c.route('**/*', b.handle)
    init = ''
    if signed_in: init += f"localStorage.setItem('ssj-auth', JSON.stringify({json.dumps(session(bk.get('new_man', False)))}));"
    if tour_done: init += "localStorage.setItem('ssj_tour_v1','1');"
    if init: await c.add_init_script(f"try{{ if(!sessionStorage.getItem('_init')){{ {init} sessionStorage.setItem('_init','1'); }} }}catch(e){{}}")
    p = await c.new_page(); errs = []
    p.on('pageerror', lambda e: errs.append(str(e)[:200]))
    p.on('console', lambda m: errs.append('console.error: ' + m.text[:200]) if m.type == 'error' and 'status of 403' not in m.text and 'status of 429' not in m.text else None)
    return c, p, b, errs

async def signin_suite(br):
    for label, dev in (('phone', PHONE), ('small-android', SMALL), ('laptop', LAPTOP)):
        # existing brother, code flow incl. mistakes
        c, p, b, errs = await ctx(br, dev, signed_in=False)
        await p.goto(URL); await p.wait_for_timeout(800)
        log('signin', f'{label}: lands on sign-in', await p.is_visible('#si-step-email'))
        await p.fill('#login-email', 'joe@gmail'); await p.click('#si-send-btn'); await p.wait_for_timeout(300)
        log('signin', f'{label}: bad email shows plain error', await p.is_visible('#si-err-email'), await p.inner_text('#si-err-email'))
        await p.fill('#login-email', '  TestBrother@Example.com '); await p.click('#si-send-btn'); await p.wait_for_timeout(600)
        log('signin', f'{label}: code screen after send', await p.is_visible('#si-step-code'), await p.inner_text('#si-sent-to'))
        await p.fill('#si-code', '000000'); await p.wait_for_timeout(800)
        log('signin', f'{label}: wrong code -> friendly error, stays on code', await p.is_visible('#si-err-code') and await p.is_visible('#si-step-code'))
        await p.fill('#si-code', ''); await p.type('#si-code', '12 34-56'); await p.wait_for_timeout(1500)
        home = await p.is_visible('#panel-home')
        log('signin', f'{label}: correct code (typed with spaces/dash) -> Home', home)
        await p.reload(); await p.wait_for_timeout(1200)
        log('signin', f'{label}: stays signed in after reopening', await p.is_visible('#panel-home'))
        log('signin', f'{label}: no JS errors', not errs, ' | '.join(errs[:3])); await c.close()
        # new man -> welcome screen
        c, p, b, errs = await ctx(br, dev, signed_in=False, tour_done=False, new_man=True)
        await p.goto(URL); await p.wait_for_timeout(600)
        await p.fill('#login-email', 'testbrother@example.com'); await p.click('#si-send-btn'); await p.wait_for_timeout(500)
        await p.fill('#si-code', '123456'); await p.wait_for_timeout(1500)
        log('signin', f'{label}: new man sees Welcome screen', await p.is_visible('#screen-signup'))
        await p.fill('#signup-name', 'Bob'); await p.click('#signup-btn'); await p.wait_for_timeout(300)
        log('signin', f'{label}: one-word name asks for first & last', await p.is_visible('#signup-err'))
        await p.fill('#signup-name', 'Bob  Smith'); await p.click('#signup-btn'); await p.wait_for_timeout(2600)
        log('signin', f'{label}: welcome -> Home, greeting uses name', await p.is_visible('#panel-home') and 'Bob' in (await p.inner_text('#home-greeting')))
        log('signin', f'{label}: tour auto-starts for first-timer', await p.is_visible('#tour'))
        await c.close()
        # rate limited
        c, p, b, errs = await ctx(br, dev, signed_in=False, otp_mode='ratelimit')
        await p.goto(URL); await p.wait_for_timeout(600)
        await p.fill('#login-email', 'testbrother@example.com'); await p.click('#si-send-btn'); await p.wait_for_timeout(600)
        log('signin', f'{label}: rate-limit message is friendly', 'wait' in (await p.inner_text('#si-err-email')).lower())
        await p.click('text=Use a password instead'); await p.wait_for_timeout(300)
        log('signin', f'{label}: password option opens with email carried over', await p.input_value('#login-email-pw') == 'testbrother@example.com')
        await c.close()

AUDIT_JS = """() => { const vw=innerWidth, out={overflow:[],tiny:[],smallTap:[]};
  const vis=e=>{const r=e.getBoundingClientRect(); const s=getComputedStyle(e); return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'&&r.bottom>0&&r.top<innerHeight;};
  for(const e of document.querySelectorAll('body *')){ if(!vis(e)) continue; const r=e.getBoundingClientRect();
    if(r.right>vw+2 && getComputedStyle(e).position!=='fixed') out.overflow.push((e.id||e.className||e.tagName).toString().slice(0,40));
    if(e.children.length===0 && e.textContent.trim() && parseFloat(getComputedStyle(e).fontSize)<14) out.tiny.push(e.textContent.trim().slice(0,30)+' '+getComputedStyle(e).fontSize);
    if((e.tagName==='BUTTON'||e.getAttribute('onclick')) && (r.height<36 || r.width<36) && e.textContent.trim()) out.smallTap.push(e.textContent.trim().slice(0,25)+` ${Math.round(r.width)}x${Math.round(r.height)}`);}
  for(const k in out) out[k]=[...new Set(out[k])].slice(0,8); return out; }"""

async def audit_suite(br):
    views = [('home', "showTab('home',document.getElementById('nav-home'))"), ('about', "showTab('about',document.getElementById('nav-about'))"),
             ('formation', "showTab('formations',document.getElementById('nav-formations'))"), ('serve', "showTab('serve',document.getElementById('nav-serve'))"),
             ('calendar-list', "openEventsPanel()"), ('calendar-month', "openEventsPanel();setEventsView('calendar',document.getElementById('toggle-cal'));selectCalDay('2026-11-21')"),
             ('roster', "openRosterPanel()"), ('archive', "showTab('archive',null)"), ('deeper', "openDeeperPanel()"), ('photos', "openPhotosPanel()"),
             ('account', "showTab('account',null)"), ('more-menu', "showTab('home',document.getElementById('nav-home'));openMenu()"),
             ('aar-viewer', "closeMenu();openDoc('aar/2026-11-after-action-report.pdf','After Action Report')"),
             ('video', "closeDoc();openVideo()"), ('tour', "closeVideo();startTour()"), ('serve-detail', "endTour();openServeDetail('00000000-0000-4000-8000-000000000502')")]
    for label, dev in (('phone', PHONE), ('small-android', SMALL), ('laptop', LAPTOP)):
        c, p, b, errs = await ctx(br, dev)
        await p.goto(URL); await p.wait_for_timeout(1500)
        for name, js in views:
            try: await p.evaluate(js)
            except Exception as e: log('audit', f'{label}/{name}: opens', False, str(e)[:150]); continue
            await p.wait_for_timeout(1800 if name in ('aar-viewer', 'photos', 'archive') else 700)
            a = await p.evaluate(AUDIT_JS)
            await p.screenshot(path=str(OUT / f'{label}-{name}.png'))
            log('audit', f'{label}/{name}: nothing runs off screen', not a['overflow'], ', '.join(a['overflow']))
            log('audit', f'{label}/{name}: no text under 14px', not a['tiny'], ', '.join(a['tiny']))
            if a['smallTap']: log('audit', f'{label}/{name}: tap targets >=36px', False, ', '.join(a['smallTap']))
        log('audit', f'{label}: no JS errors across all screens', not errs, ' | '.join(errs[:4]))
        log('audit', f'{label}: no writes to data', not b.writes, ', '.join(b.writes)); await c.close()

async def persona_suite(br, sessions, steps):
    for persona in ('teen', 'twenties', 'forties', 'elders'):
        for label, dev in (('phone', PHONE), ('laptop', LAPTOP)):
            c, p, b, errs = await ctx(br, dev)
            await p.goto(URL); await p.wait_for_timeout(1500); await p.evaluate(HARNESS)
            r = await p.evaluate(f"window.__qc('{persona}', {sessions}, {steps})")
            log('persona', f'{persona} on {label}: {r["sessions"]} sessions / {r["actions"]} taps', r['nFails'] == 0, ' || '.join(r['fails'][:6]))
            log('persona', f'{persona} on {label}: no JS errors', not errs, ' | '.join(sorted(set(errs))[:3]))
            log('persona', f'{persona} on {label}: no data writes', not b.writes, ', '.join(b.writes[:5]))
            results[-3]['covered'] = r['covered']; await c.close()

async def main(which):
    async with async_playwright() as pw:
        br = await pw.chromium.launch(args=['--no-proxy-server', '--autoplay-policy=no-user-gesture-required'])
        if 'signin' in which: await signin_suite(br)
        if 'audit' in which: await audit_suite(br)
        if 'persona' in which: await persona_suite(br, int(which.get('sessions', 13)), int(which.get('steps', 14)))
        await br.close()
    json.dump(results, open(OUT / f'results-{int(time.time())}.json', 'w'), indent=1)

if __name__ == '__main__':
    args = dict(a.split('=') if '=' in a else (a, '1') for a in sys.argv[1:])
    asyncio.run(main(args))
