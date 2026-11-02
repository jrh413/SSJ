"""Offline mock of the SSJ backend for Playwright QC. No real data is touched."""
import json, re, time, base64, urllib.parse, pathlib

SITE = pathlib.Path('/home/claude/ssj-beta')
LIB = pathlib.Path('/home/claude/qc/lib')
AAR = SITE / 'aar' / '2026-11-after-action-report.pdf'
PHOTO = SITE / 'media' / 'carousel' / '2026-10-28-brothers.jpg'
ME = '2cb1e090-0000-4000-8000-00000000ab01'
LONG = 'Feast of Our Lady of Guadalupe — Rosary, Mass & CMF'

def uid(i): return f'00000000-0000-4000-8000-{i:012d}'

def fixtures(role='brother', new_man=False):
    names = ['Dennis Acasio','Mark Aguilar Jr.','Raul Anda','Brett Barker','James Bissin','Jesse Cano','Michael Capelle',
             'Virgilio (VG) Carlos','Jonathan Chavez','Robert Doughtery','Gerald John Domingues','Emanuel Garcia Quintana']
    prof = [dict(id=uid(100+i), email=f'brother{i}@example.com', full_name=n, phone='(805) 555-01%02d' % i, role='brother',
                 active=True, contact_share=i % 2 == 0, sms_consent=False, created_at='2026-05-25T00:00:00Z') for i, n in enumerate(names)]
    me = dict(id=ME, email='testbrother@example.com', full_name=('testbrother' if new_man else 'Joe Tester'), phone=None,
              role=role, active=True, contact_share=False, sms_consent=False, created_at='2026-05-25T00:00:00Z')
    prof.append(me)
    ev = [('Divine Mercy & First Friday Adoration','2026-11-06','7:00 PM','Saint Mary of the Assumption Catholic Church, Santa Maria','prayer'),
          ('Pray Without Ceasing — Rosary, Mass & CMF','2026-11-14','7:25 AM','Saint Louis de Montfort, Orcutt — Upper Room (Rosary & Mass), Mahan Room (CMF)','prayer'),
          ('Christ the King — Form Up for Mass','2026-11-21','4:20 PM','Our Lady of Guadalupe, Guadalupe CA','prayer'),
          (LONG,'2026-12-12','7:25 AM','Saint Louis de Montfort, Orcutt — Upper Room (Rosary & Mass), Mahan Room (CMF)','prayer'),
          ('Exodus 90 Kick-Off Meeting','2027-01-10',None,'Location to be announced','formation'),
          ('Parish Picnic - SLDM','2026-05-31','11:30','Pioneer Park - Orcut - Foster Rd and Blosser Rd.','social')]
    events = [dict(id=uid(200+i), title=t, event_date=d, end_date=None, start_time=tm, end_time=None, location=l,
                   description='Description text for testing. ' * 3, event_type=ty, url=None, created_by=ME, created_at='2026-11-02T00:00:00Z')
              for i, (t, d, tm, l, ty) in enumerate(ev)]
    events += [dict(id=uid(260+i), title='Catholic in Recovery', event_date=d, end_date=None, start_time='7:00 AM', end_time=None, location="McDonald's, 1150 E Clark Ave, Orcutt 93455", description='12 steps in the light of Church tradition. Questions? Call or text Joe: (805) 456-0353', event_type='recovery', url=('doc:recovery/2026-11-07-cir-reflection.pdf' if i==0 else None), created_by=ME, created_at='2026-11-02T00:00:00Z') for i, d in enumerate(['2026-11-07','2026-11-14','2026-11-21','2026-11-28'])]
    forms = [dict(id=uid(300), tasking_order='2026-016', title='Monthly Formation — October 28, 2026', formation_date='2026-10-28', start_time='6:30 PM', end_time='8:40 PM',
                  location='St. Mary of the Assumption Parish Hall', description='Normal Formation.', visible_to='apprentice', created_at='2026-05-15T00:00:00Z'),
             dict(id=uid(301), tasking_order=None, title='Monthly Formation — January 27, 2027', formation_date='2027-01-27', start_time='6:30 PM', end_time='8:40 PM',
                  location='St. Mary of the Assumption Parish Hall', description='First formation of 2027.', visible_to='apprentice', created_at='2026-11-02T00:00:00Z')]
    docs = [dict(id=uid(400+i), title=f'Tasking Order #2026-0{10+i}', description=None, category='formation', file_path=f'formations/to-{i}.pdf',
                 file_name=f'to-{i}.pdf', tasking_order=f'Tasking Order #2026-0{10+i}', visible_to='brother', uploaded_by=ME, created_at=f'2026-0{5+i}-01T00:00:00Z') for i in range(5)]
    serve = [dict(id=uid(500), number=3, title='Support Our Chaplain', detail='Pray for, encourage, and practically support the priests.', tag='ALWAYS', date=None,
                  location='In person, at the Formations', max_slots=None, active=True, fund_goal=153.0, venmo_handle=None, zelle_contact=None, description=None),
             dict(id=uid(501), number=5, title='Support SSJ', detail='Help cover the costs of formation materials, hospitality, and travel.', tag='ONGOING', date=None,
                  location='At each Formation', max_slots=None, active=True, fund_goal=500.0, venmo_handle=None, zelle_contact='805-555-0100', description=None),
             dict(id=uid(502), number=1, title='Christmas BBQ — Franciscan Novitiate', detail='Food, fellowship, and fraternity in action.', tag='UPCOMING', date='2026-12-19',
                  location='1352 Dale Way, Arroyo Grande, CA 93420', max_slots=None, active=True, fund_goal=300.0, venmo_handle=None, zelle_contact=None, description=None)]
    needs = [dict(id=uid(600+i), serve_id=uid(502), pillar=p, emoji=None, title=t, detail=dt, quantity=q, cost_each=None, template_key=None, sort_order=i, created_at='2026-11-01T00:00:00Z')
             for i, (p, t, dt, q) in enumerate([('time','Servers',None,2),('talent','Broccoli Salad','Serves 40',1),('talent','Potato Salad','Serves 40',1),('treasure','Tri-Tip Fund',None,1)])]
    claims = [dict(id=uid(700), need_id=uid(600), member_id=uid(101), quantity=1, note=None, in_spirit=False, pledged_amt=None, claimed_at='2026-11-01T00:00:00Z',
                   ssj_profiles={'full_name': names[1]})]
    photos = [dict(id=uid(800+i), file_path=f'photos/p{i}.jpg', file_name=f'p{i}.jpg', caption=c, event_id=None, formation_id=None, serve_id=None, album_label=a,
                   uploaded_by=ME, created_at=f'2026-{m}T0{i}:00:00Z', ssj_profiles={'full_name': 'Joe Tester'}, ssj_formations=None, ssj_serve=None)
              for i, (c, a, m) in enumerate([('Group photo','April 2026 Formation','05-25'),('Speaker','Monthly Formation - May 2026','05-28'),
                                              ('Announcements — Divine Mercy Holy Hour','Monthly Formation - October 2026','11-02'),
                                              ('Gospel Reflection — Tom O’Malley on the Beatitudes','Monthly Formation - October 2026','11-02'),
                                              ('Deacon Chris Hansen — “Patron and Teacher”','Monthly Formation - October 2026','11-02'),
                                              ('The brothers — October 28 formation','Monthly Formation - October 2026','11-02')])]
    deeper = [dict(id=uid(900+i), key=k, name=n, subtitle=s, quote='We are far too easily pleased.', body='Body text. ' * 40, sort_order=i, active=True)
              for i, (k, n, s) in enumerate([('lewis','C.S. Lewis','The Reluctant Convert · Oxford · 1898–1963'),('walshe','Fr. Sebastian Walshe, O.Praem.','Norbertines of St. Michael’s Abbey · California'),('augustine','St. Augustine of Hippo','Doctor of Grace · North Africa · 354–430')])]
    links = [dict(id=uid(950+i), deeper_id=uid(900+i % 3), icon='▶', title='Mere Christianity — Full Audiobook (YouTube)', subtitle='Start with Book 4', url='https://example.com/x', sort_order=i) for i in range(5)]
    return dict(ssj_profiles=prof, ssj_events=events, ssj_formations=forms, ssj_documents=docs, ssj_serve=serve, ssj_serve_needs=needs,
                ssj_serve_claims=claims, ssj_serve_signups=[], ssj_photos=photos, ssj_deeper=deeper, ssj_deeper_links=links, ssj_about=[], ssj_invites=[])

def jwt(sub):
    b = lambda o: base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip('=')
    return f"{b({'alg':'HS256','typ':'JWT'})}.{b({'sub':sub,'role':'authenticated','exp':int(time.time())+86400*30,'aud':'authenticated'})}.sig"

def user(new_man=False):
    return dict(id=ME, aud='authenticated', role='authenticated', email='testbrother@example.com', email_confirmed_at='2026-05-25T00:00:00Z',
                user_metadata={} if new_man else {'full_name': 'Joe Tester'}, app_metadata={'provider': 'email'}, created_at='2026-05-25T00:00:00Z')

def session(new_man=False):
    return dict(access_token=jwt(ME), token_type='bearer', expires_in=86400*30, expires_at=int(time.time())+86400*30,
                refresh_token='rt', user=user(new_man))

def _match(row, k, v):
    if v.startswith('not.is.null'): return row.get(k) is not None
    op, _, val = v.partition('.')
    x = row.get(k)
    if op == 'is': return x is None if val == 'null' else str(x).lower() == val
    if op == 'in':
        vals = [s.strip('"') for s in val.strip('()').split(',')]; return str(x) in vals
    if val in ('true', 'false'): val = val == 'true'
    if op == 'eq': return x == val or str(x) == str(val)
    if op == 'neq': return x != val
    if x is None: return False
    if op == 'gte': return str(x) >= val
    if op == 'lte': return str(x) <= val
    if op == 'gt': return str(x) > val
    if op == 'lt': return str(x) < val
    return True

class Backend:
    def __init__(self, role='brother', new_man=False, otp_mode='ok'):
        self.db = fixtures(role, new_man); self.writes = []; self.new_man = new_man; self.otp_mode = otp_mode; self.requests = 0

    def rest(self, method, path, query, headers, body):
        table = path.split('/rest/v1/')[1].split('?')[0]
        rows = self.db.get(table, [])
        if method != 'GET':
            self.writes.append(f'{method} {table}')
            if table == 'ssj_profiles' and method == 'PATCH':  # welcome screen save
                upd = json.loads(body or '{}'); [r.update(upd) for r in rows if r['id'] == ME]
            return 200 if method != 'POST' else 201, []
        q = urllib.parse.parse_qs(query, keep_blank_values=True)
        out = list(rows)
        for k, vs in q.items():
            if k in ('select', 'order', 'limit', 'offset'): continue
            for v in vs: out = [r for r in out if _match(r, k, v)]
        for o in reversed((q.get('order', [''])[0]).split(',')):
            if not o: continue
            col, *mods = o.split('.')
            out.sort(key=lambda r: (r.get(col) is None, str(r.get(col) or '')), reverse='desc' in mods)
        if 'limit' in q: out = out[:int(q['limit'][0])]
        if 'vnd.pgrst.object' in headers.get('accept', ''):
            return (200, out[0]) if out else (406, {'code': 'PGRST116', 'message': 'no rows'})
        return 200, out

    async def handle(self, route, request):
        self.requests += 1
        url = request.url; u = urllib.parse.urlparse(url); h = {k.lower(): v for k, v in request.headers.items()}
        async def ok(status, obj=None, body=None, ctype='application/json'):
            await route.fulfill(status=status, body=body if body is not None else json.dumps(obj), content_type=ctype,
                          headers={'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*'})
        if request.method == 'OPTIONS': return await ok(200, {})
        if u.netloc == 'school-of-st-joseph.netlify.app':
            p = u.path.lstrip('/') or 'index.html'
            f = SITE / urllib.parse.unquote(p)
            if f.is_file():
                ct = {'.html':'text/html','.pdf':'application/pdf','.jpg':'image/jpeg','.mp4':'video/mp4','.png':'image/png'}.get(f.suffix,'application/octet-stream')
                return await route.fulfill(status=200, path=str(f), content_type=ct)
            return await ok(404, body='not found', ctype='text/plain')
        if 'cdn.jsdelivr.net' in u.netloc and 'supabase' in u.path:
            return await route.fulfill(status=200, path=str(LIB / 'supabase-supabase-js-2.45.4/dist/umd' / ('supabase.js' if u.path.endswith('supabase.min.js') else pathlib.Path(u.path).name)), content_type='application/javascript')
        if 'cdnjs.cloudflare.com' in u.netloc and 'pdf.js' in u.path:
            return await route.fulfill(status=200, path=str(LIB / 'pdfjs-dist-3.11.174/build' / pathlib.Path(u.path).name), content_type='application/javascript')
        if 'fonts.g' in u.netloc: return await ok(200, body='', ctype='text/css')
        if u.netloc.endswith('supabase.co'):
            if '/rest/v1/' in u.path:
                s, obj = self.rest(request.method, u.path, u.query, h, request.post_data); return await ok(s, obj)
            if '/storage/v1/object/sign/' in u.path and request.method == 'POST':
                rest = u.path.split('/storage/v1/object/sign/')[1]
                return await ok(200, {'signedURL': f'/object/sign/{rest}?token=t'})
            if '/storage/v1/object/sign/' in u.path:
                return await route.fulfill(status=200, path=str(AAR if u.path.endswith('.pdf') else PHOTO), content_type='application/pdf' if u.path.endswith('.pdf') else 'image/jpeg', headers={'access-control-allow-origin':'*'})
            if '/auth/v1/otp' in u.path:
                if self.otp_mode == 'ratelimit': return await ok(429, {'code': 429, 'msg': 'For security purposes, you can only request this after 37 seconds.'})
                return await ok(200, {})
            if '/auth/v1/verify' in u.path:
                tok = json.loads(request.post_data or '{}').get('token')
                if tok != '123456': return await ok(403, {'code': 403, 'error_code': 'otp_expired', 'msg': 'Token has expired or is invalid'})
                return await ok(200, session(self.new_man))
            if '/auth/v1/user' in u.path: return await ok(200, user(self.new_man))
            if '/auth/v1/logout' in u.path: return await ok(204, body='')
            if '/auth/v1/token' in u.path: return await ok(200, session(self.new_man))
            return await ok(200, {})
        if u.netloc.endswith('example.com'): return await ok(200, body='<html>external</html>', ctype='text/html')
        return await route.abort()
