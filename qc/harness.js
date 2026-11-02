
// QC harness: random "brother" sessions against the preview iframe. Read-only actions only.
const w=window, d=document;
const W=ms=>new Promise(r=>setTimeout(r,ms));
w.HTMLMediaElement.prototype.play=function(){return Promise.resolve();}; // no sound at night
if(!w.__errs){ w.__errs=[]; const ce=w.console.error.bind(w.console);
  w.console.error=(...a)=>{w.__errs.push(a.map(String).join(' ').slice(0,160)); ce(...a);};
  w.addEventListener('error',e=>w.__errs.push('ERR '+(e.message||'')+' @'+(e.lineno||'')));
  w.addEventListener('unhandledrejection',e=>w.__errs.push('REJ '+String(e.reason).slice(0,160))); }
const vis=el=>el&&el.offsetParent!==null;
const OVS=['doc-viewer','vid-overlay','photo-lightbox','prayer-overlay','tour','menu-drawer'];
const openOvs=()=>OVS.filter(id=>d.getElementById(id)?.classList.contains('show')).concat(d.getElementById('screen-serve-detail')?.classList.contains('active')?['serve-detail']:[]);
const click=sel=>{const el=typeof sel==='string'?d.querySelector(sel):sel; if(el){el.click();return true;} return false;};
const rnd=a=>a[Math.floor(Math.random()*a.length)];
const A={
  nav:()=>click('#nav-'+rnd(['home','about','formations','serve'])),
  more:async()=>{ click('#nav-more'); await W(350); const items=[...d.querySelectorAll('#menu-drawer .menu-item')].filter(m=>vis(m)&&m.id!=='menu-admin-item'); click(rnd(items)); },
  backBtn:()=>{ const b=d.getElementById('hdr-back'); if(vis(b)) b.click(); else { const ob=[...d.querySelectorAll('.ov-back,.vid-box .si-btn,.prayer-amen,.tour-skip')].find(vis); if(ob) ob.click(); } },
  phoneBack:()=>{ const s=w.history.state; if(s&&(s.ov||(s.tab&&s.tab!=='home'))) w.history.back(); },
  aar:async()=>{ if(w._curTab!=='home') click('#nav-home'); await W(200); click('#home-aar'); },
  video:async()=>{ if(w._curTab!=='home') click('#nav-home'); await W(200); click('.hm-video-btn'); },
  calendar:async()=>{ w.openEventsPanel(); await W(400); click(rnd(['#toggle-cal','#toggle-list'])); await W(250);
    if(vis(d.getElementById('events-cal-view'))){ click(rnd(['.cal-arrow','.cal-arrow:last-child'])); await W(150); const days=[...d.querySelectorAll('#cal-days .cal-day:not(.other-month)')]; click(rnd(days)); } },
  comingUp:async()=>{ if(w._curTab!=='home') click('#nav-home'); await W(200); click(rnd([...d.querySelectorAll('.hm-ev')])); },
  tour:async()=>{ w.startTour(); for(let i=0,n=Math.floor(Math.random()*10);i<n;i++){ await W(120); click('#tour-next'); } },
  photos:async()=>{ w.openPhotosPanel(); await W(1200); const t=[...d.querySelectorAll('.photo-thumb')]; if(t.length){ click(rnd(t)); await W(300); w.lightboxNext(); w.lightboxPrev(); } },
  prayer:()=>{ if(w._curTab==='home') w.openPrayer(); },
  serve:async()=>{ click('#nav-serve'); await W(500); const it=[...d.querySelectorAll('#panel-serve [onclick*="openServeDetail"]')]; if(it.length) click(rnd(it)); },
  doc:async()=>{ w.showTab('archive',null); await W(1200); const it=[...d.querySelectorAll('.doc-item[data-url]')]; if(it.length) click(rnd(it)); },
  account:()=>w.showTab('account',null),
};
const P={ // persona: pace(ms), action weights, double-tap chance, back style
  teen:{pace:90, dbl:.25, acts:['nav','nav','more','phoneBack','phoneBack','phoneBack','tour','video','photos','calendar','backBtn','aar','comingUp']},
  twenties:{pace:160, dbl:.12, acts:['nav','more','phoneBack','phoneBack','calendar','comingUp','aar','video','photos','doc','backBtn','serve']},
  forties:{pace:300, dbl:.06, acts:['nav','more','backBtn','phoneBack','calendar','aar','doc','serve','account','comingUp','prayer']},
  elders:{pace:600, dbl:.15, acts:['nav','more','backBtn','backBtn','aar','calendar','comingUp','video','prayer','doc','tour']},
};
async function check(tag){
  const bad=[]; const act=[...d.querySelectorAll('#screen-app .tab-panel.active')];
  if(!d.getElementById('screen-app').classList.contains('active') && !d.getElementById('screen-serve-detail').classList.contains('active')) bad.push('left app: '+d.querySelector('.screen.active')?.id);
  if(act.length!==1) bad.push('active panels='+act.length);
  const ovs=openOvs().filter(o=>o!=='menu-drawer'); if(ovs.length>1) bad.push('stacked overlays '+ovs.join('+'));
  const b=d.getElementById('hdr-back'); if(b?.classList.contains('show')) bad.push('header back showing on '+w._curTab);
  if(act[0] && act[0].id!=='panel-'+w._curTab) bad.push('tab state '+w._curTab+' vs '+act[0].id);
  return bad;
}
async function run(persona, sessions, steps){
  const p=P[persona], fails=[], seen=new Set(); let actions=0;
  for(let s=0;s<sessions;s++){
    // reset to home, clean
    for(const o of openOvs()) ({'doc-viewer':()=>w.closeDoc(),'vid-overlay':()=>w.closeVideo(),'photo-lightbox':()=>w.closeLightbox(),'prayer-overlay':()=>w.closePrayer(),'tour':()=>w.endTour(),'menu-drawer':()=>w.closeMenu(),'serve-detail':()=>w.closeServeDetail()}[o]||(()=>{}))();
    w.showTab('home',d.getElementById('nav-home')); await W(150);
    const errs0=w.__errs.length; const trail=[];
    for(let i=0;i<steps;i++){
      const a=rnd(p.acts); trail.push(a);
      try{ await A[a](); if(Math.random()<p.dbl){ await W(40); await A[a](); trail.push(a+'(x2)'); } }catch(e){ fails.push(`${persona} s${s} ${a}: THREW ${String(e).slice(0,100)}`); }
      actions++; await W(p.pace);
      for(const x of await check()){ const k=a+'|'+x; if(!seen.has(k)){ seen.add(k); fails.push(`${persona} s${s} after [${trail.slice(-3).join(' > ')}]: ${x}`);} }
      seen.add('tab:'+w._curTab); for(const o of openOvs()) seen.add('ov:'+o);
    }
    // exit test: from wherever, pressing Back repeatedly must always lead Home without getting stuck
    for(let k=0;k<12;k++){ const st=w.history.state; if(!(st&&(st.ov||(st.tab&&st.tab!=='home')))) break; w.history.back(); await W(200); }
    if(openOvs().filter(o=>o!=='menu-drawer').length) fails.push(`${persona} s${s}: overlay stuck after backing out: ${openOvs()}`);
    if(w.__errs.length>errs0) fails.push(`${persona} s${s} JS errors: ${w.__errs.slice(errs0).slice(0,2).join(' | ')}`);
  }
  return {persona, sessions, actions, fails:fails.slice(0,12), nFails:fails.length, covered:[...seen].filter(x=>/^(tab|ov):/.test(x)).sort().join(',')};
}
window.__qc=run;