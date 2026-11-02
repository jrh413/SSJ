import asyncio, pathlib, urllib.parse
from playwright.async_api import async_playwright
from mock import Backend
from run import PHONE, SMALL, LAPTOP, AUDIT_JS
WEB = pathlib.Path('/home/claude/website'); OUT = pathlib.Path('/home/claude/qc/out')

class WebBackend(Backend):
    async def handle(self, route, request):
        u = urllib.parse.urlparse(request.url)
        if u.netloc == 'ssj-website.test':
            f = WEB / (urllib.parse.unquote(u.path.lstrip('/')) or 'index.html')
            if f.is_file():
                ct = {'.html': 'text/html', '.png': 'image/png', '.jpg': 'image/jpeg'}.get(f.suffix, 'application/octet-stream')
                return await route.fulfill(status=200, path=str(f), content_type=ct)
            return await route.fulfill(status=404, body='nf')
        return await super().handle(route, request)

async def main():
    async with async_playwright() as pw:
        br = await pw.chromium.launch(args=['--no-proxy-server'])
        for label, dev in (('phone', PHONE), ('small-android', SMALL), ('laptop', LAPTOP)):
            b = WebBackend(); c = await br.new_context(**dev); await c.route('**/*', b.handle)
            p = await c.new_page(); errs = []
            p.on('pageerror', lambda e: errs.append(str(e)[:150]))
            p.on('console', lambda m: errs.append(m.text[:150]) if m.type == 'error' else None)
            await p.goto('https://ssj-website.test/'); await p.wait_for_timeout(1500)
            n = await p.evaluate("document.querySelectorAll('#events .ev').length")
            full = await p.evaluate("(()=>{document.querySelectorAll('section').forEach(s=>s.scrollIntoView());return document.body.scrollHeight})()")
            await p.evaluate('scrollTo(0,0)')
            a = await p.evaluate(AUDIT_JS.replace('r.bottom>0&&r.top<innerHeight', 'true'))
            await p.screenshot(path=str(OUT / f'web-{label}.png'), full_page=True)
            links = await p.evaluate("[...document.querySelectorAll('a[href^=\"#\"]')].map(a=>a.getAttribute('href')).filter(h=>h.length>1&&!document.querySelector(h))")
            print(label, '| events shown:', n, '| page height:', full, '| overflow:', a['overflow'], '| tiny:', a['tiny'][:4], '| smallTap:', a['smallTap'][:4], '| broken anchors:', links, '| errors:', errs[:3])
            await c.close()
        await br.close()
asyncio.run(main())
