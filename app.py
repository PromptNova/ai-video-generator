/* AI Hook Generator — Luxe Hero v5 — Fully English — Works with FastAPI POST /upload */

const $ = s=>document.querySelector(s); const $$ = s=>Array.from(document.querySelectorAll(s));
const store = {get:(k,d)=>{try{return JSON.parse(localStorage.getItem(k))??d}catch{return d}}, set:(k,v)=>localStorage.setItem(k,JSON.stringify(v))};
const emojiSets = {none:[], few:['🔥','🚀','💡','⚠️','✅','⏱️','🎯','🤫','🧠'], many:['🔥','🚀','💡','⚠️','✅','⏱️','🎯','🤫','🧠','💥','🏆','📉','📈','🪄','🧪','🔒','🤑']};
const powerBase = ['secret','simple','fast','proven','lazy','hidden','weird','unfair','steal','free','instant','tiny','silent','dangerous','perfect'];

const state = store.get('HOOK_STATE',{niche:'',offer:'',platform:'shorts',tone:'Bold',length:'medium',emojis:'few',count:10,frameworks:['PAS','AIDA','Q','GAP'],power:'secret, fast, proven, steal, hidden',batch:''});
$('#year') && ($('#year').textContent = new Date().getFullYear());

/* ---------- Toast with icons ---------- */
function toast(msg, type='info'){ const t=$('#toast')||(()=>{const d=document.createElement('div'); d.id='toast'; d.className='toast'; document.body.appendChild(d); return d})(); const icon = {ok:'✅ ', warn:'⚠️ ', info:'💬 ', error:'⛔ '}[type]||''; t.textContent=icon+msg; t.setAttribute('data-type', type); t.setAttribute('data-show','true'); clearTimeout(window._tt); window._tt=setTimeout(()=>t.removeAttribute('data-show'),1800) }

/* ---------- Helpers ---------- */
const rand = a=>a[Math.floor(Math.random()*a.length)];
const capitalize = s=>s.charAt(0).toUpperCase()+s.slice(1);
const lengthMap={short:[4,8], medium:[8,14], long:[14,20]};
function lengthClamp(txt){ const [min,max]=lengthMap[state.length]; let words=txt.split(/\s+/); if(words.length>max) words=words.slice(0,max); while(words.length<min) words.push('fast'); return words.join(' ') }
function uniq(arr){ return Array.from(new Set(arr.map(x=>x.toLowerCase().trim()))).map(k=>arr.find(x=>x.toLowerCase().trim()===k)) }
function score(h){ let s=0; const w=h.split(/\s+/).length; if(w>=4 && w<=14) s+=2; else if(w<=20) s+=1; if(/[0-9]/.test(h)) s+=1; if(/[?:]/.test(h)) s+=1; if(/\byou\b/i.test(h)) s+=1; if(/secret|proven|weird|fast|free|hidden|tiny|unfair|steal/i.test(h)) s+=1; if(/this|these|here's|step/i.test(h)) s+=1; return s }
function persist(){ state.niche=$('#niche')?.value?.trim()||state.niche; state.offer=$('#offer')?.value?.trim()||state.offer; state.platform=$('#platform')?.value||state.platform; state.tone=$('#tone')?.value||state.tone; state.length=$('#length')?.value||state.length; state.emojis=$('#emojis')?.value||state.emojis; state.count=parseInt($('#count')?.value||state.count,10); state.frameworks=$$('.fw:checked').map(x=>x.value); state.power=$('#power')?.value?.trim()||state.power; state.batch=$('#batch')?.value?.trim()||state.batch; store.set('HOOK_STATE', state) }

/* ---------- Hook engines ---------- */
function tPAS(who,what,pw){ const pains=['wasting hours','low views','no clicks','tiny watch time','burnout','creator block']; const solves=['fix it in 60s','double views fast','steal my template','copy this system','do this instead']; const e=rand(pw); return [ `${capitalize(e)} trick for ${who}: ${rand(pains)}? ${rand(solves)}.`, `${who}, stop ${rand(pains)} — try this ${e} ${what}.`, `${rand(['Sick of','Done with'])} ${rand(pains)}? ${capitalize(e)} ${what} below.` ] }
function tAIDA(who,what,pw){ const e=rand(pw); return [ `${capitalize(who)}: want ${rand(['explosive growth','instant trust','faster sales'])}? ${capitalize(e)} hooks that convert.`, `${rand(['Watch this','Do this'])} before your next post — ${e} ${what}.`, `${rand(['Proof:','Demo:'])} ${e} hook beats your old intro.` ] }
function tQ(){ return [ `What if your next 3 seconds did all the selling?`, `Be honest: why would your audience keep watching?`, `Which one hooks you faster — A or B?` ] }
function tGAP(_who,what,pw){ const e=rand(pw); return [ `You’re doing ${what} wrong — here’s the 1% tweak.`, `Everyone skips this ${e} step — don’t.`, `This looks boring… until you see step 2.` ] }
function tLIST(){ return [ `7 hooks I wish I had on day 1.`, `3 words that triple watch time.`, `5 brutal truths about your opening line.` ] }
function tMYTH(){ return [ `Hook myth: “Shorter is always better.” Wrong.`, `Stop saying “Hey guys” — say this instead.`, `You don’t need a fancy mic — you need this first line.` ] }
const engines = {PAS:tPAS,AIDA:tAIDA,Q:tQ,GAP:tGAP,LIST:tLIST,MYTH:tMYTH};

function decorate(txt){ if(state.platform==='x'){ txt = txt.replace(/\.$/, '') } if(state.tone==='Contrarian'){ txt = 'Unpopular opinion: ' + txt.replace(/^[A-Z]/, s=>s.toLowerCase()); } if(state.tone==='Authority'){ txt = 'Do this: ' + txt; } if(state.tone==='Minimal'){ txt = txt.replace(/[.!?]$/,''); }
  const es = emojiSets[state.emojis]; if(es.length){ const lead = Math.random()<.55 ? rand(es)+' ' : ''; const tail = Math.random()<.55 ? ' '+rand(es) : ''; txt = lead + txt + tail }
  return lengthClamp(txt)
}

function generateOnce(topic){ const who=state.niche||'creators'; const what=topic||state.offer||'your offer'; const pw=(state.power? state.power.split(',').map(x=>x.trim()).filter(Boolean):powerBase); const active=state.frameworks.length?state.frameworks:['PAS','AIDA','Q','GAP']; let pool=[]; active.forEach(fw=>{ pool=pool.concat( engines[fw](who, what, pw) )}); return pool.map(decorate) }
function render(hooks){ const out=$('#output'); if(!out) return; out.innerHTML=''; hooks.forEach(h=>{ const sc=score(h); const el=document.createElement('article'); el.className='hook card'; el.innerHTML=`<div class="line">${h}</div><div class="meta"><span class="badge">Score <strong class="score">${sc}</strong>/7</span><span class="badge">Len ${h.split(/\s+/).length}w</span></div><div class="actions"><button class="btn" data-act="copy">Copy</button><button class="btn" data-act="improve">Improve</button><button class="btn" data-act="save">Save</button></div>`; el.querySelector('[data-act="copy"]').onclick=()=>{ navigator.clipboard.writeText(h); toast('Copied hook','ok') }; el.querySelector('[data-act="save"]').onclick=()=>{ saveHook(h); toast('Saved to library','ok') }; el.querySelector('[data-act="improve"]').onclick=()=>{ const imp=improve(h); navigator.clipboard.writeText(imp); toast('Improved hook copied','ok') }; out.appendChild(el) }) }
function generate(){ persist(); let hooks=[]; const topics = state.batch? state.batch.split(/\n+/).filter(Boolean) : [state.offer||'your offer']; topics.forEach(t=> hooks = hooks.concat(generateOnce(t)) ); hooks = uniq(hooks); while(hooks.length < state.count){ hooks = uniq(hooks.concat(generateOnce())) } hooks.sort(()=>Math.random()-.5); hooks = hooks.slice(0,state.count); render(hooks); toast(`Generated ${hooks.length} hooks`,'ok') }
function improve(h){ let t=h.trim(); if(!/[0-9]/.test(t)) t = t.replace(/^(.*)$/,(m)=> (Math.random()<.5? '3 reasons ' + m.toLowerCase() : m)); if(!/[?:]/.test(t)) t = t.replace(/\.$/,'') + '?'; const words=t.split(/\s+/); if(words.length>16) t=words.slice(0,16).join(' ')+'…'; return t }
const LIB_KEY='HOOK_LIBRARY'; function lib(){ return store.get(LIB_KEY,[]) } function saveHook(h){ const l=lib(); if(!l.includes(h)){ l.push(h); store.set(LIB_KEY,l) } }

/* ---------- Live Preview (niche change) ---------- */
function renderPreview(){ const box=$('#hookPreview'); if(!box) return; const arr=generateOnce().slice(0,3); $('#previewCount').textContent = `${arr.length} suggestions`; box.innerHTML=''; arr.forEach(h=>{ const el=document.createElement('article'); el.className='hook card'; el.innerHTML=`<div class="line">${h}</div><div class="actions"><button class="btn" data-act="copy">Copy</button></div>`; el.querySelector('[data-act="copy"]').onclick=()=>{ navigator.clipboard.writeText(h); toast('Copied preview','ok') }; box.appendChild(el) }) }
['#niche','#presetLib','#tone','#length','#emojis'].forEach(sel=> $(sel)?.addEventListener('change', ()=>{ persist(); renderPreview() }))

/* ---------- List tools ---------- */
;(function(){ const out=$('#output'); if(!out) return; const minScore=$('#minScore'); const search=$('#searchHooks'); const selectAll=$('#selectAll'); const copySel=$('#copySelected'); const delSel=$('#deleteSelected'); const sortBtn=$('#sortByScore'); function items(){ return Array.from(out.querySelectorAll('.hook')) } function applyFilters(){ const q=(search.value||'').toLowerCase(); const ms=parseInt(minScore.value,10); items().forEach(h=>{ const sc=parseInt(h.querySelector('.score')?.textContent||'0',10); const line=h.querySelector('.line')?.textContent.toLowerCase()||''; h.style.display=(sc>=ms && (!q || line.includes(q))) ? '' : 'none' }) } minScore?.addEventListener('input',applyFilters); search?.addEventListener('input',applyFilters); selectAll?.addEventListener('click',()=> items().forEach(h=>{ let cb=h.querySelector('input[type=checkbox]'); if(!cb){ cb=document.createElement('input'); cb.type='checkbox'; h.insertBefore(cb,h.firstChild) } cb.checked=true })); copySel?.addEventListener('click',()=>{ const t=items().filter(h=>h.querySelector('input[type=checkbox]')?.checked).map(h=>h.querySelector('.line').textContent).join('\n'); if(t){ navigator.clipboard.writeText(t); toast('Copied selected','ok') }}); delSel?.addEventListener('click',()=>{ items().filter(h=>h.querySelector('input[type=checkbox]')?.checked).forEach(h=>h.remove()) }); sortBtn?.addEventListener('click',()=>{ items().sort((a,b)=> parseInt(b.querySelector('.score').textContent)-parseInt(a.querySelector('.score').textContent)).forEach(el=> out.appendChild(el)) }) })();

/* ---------- Shortcuts, Help, Scroll, Dock ---------- */
(function(){ const modal=$('#helpModal'); $('#helpBtn')?.addEventListener('click',()=> modal.style.display='grid'); $('#helpClose')?.addEventListener('click',()=> modal.style.display='none'); $('#scrollTop')?.addEventListener('click',()=> window.scrollTo({top:0,behavior:'smooth'})); $('#goUpload')?.addEventListener('click',()=> $('#uploaderAnchor').scrollIntoView({behavior:'smooth'})); $('#dockUpload')?.addEventListener('click',()=> $('#uploaderAnchor').scrollIntoView({behavior:'smooth'})); $('#dockGenerate')?.addEventListener('click',()=> $('#generate')?.click()); document.addEventListener('keydown',(e)=>{ if(e.key==='?') modal.style.display=(modal.style.display==='grid'?'none':'grid'); if(e.key.toLowerCase()==='g') $('#generate')?.click(); if(e.key.toLowerCase()==='c') $('#copyAll')?.click(); if(e.key.toLowerCase()==='v') $('#uSubmit')?.click(); if(e.key.toLowerCase()==='u') $('#uploaderAnchor').scrollIntoView({behavior:'smooth'}); }) })();

/* ---------- Theme + Network ---------- */
(function(){ const sel=$('#themeSel'); const badge=$('#netBadge'); function apply(v){ if(v==='default'){ document.documentElement.removeAttribute('data-theme') } else { document.documentElement.setAttribute('data-theme', v) } localStorage.setItem('THEME', v) } sel?.addEventListener('change',()=> apply(sel.value)); const saved=localStorage.getItem('THEME'); if(saved){ sel.value=saved; apply(saved) } function net(){ badge.textContent = navigator.onLine ? '🛜 Online' : '⚠️ Offline' } addEventListener('online',net); addEventListener('offline',net); net() })();

/* ---------- Presets ---------- */
(function(){ const map={ fitness:{niche:'fitness beginners', power:'fat-loss, lean, quick, proven, beginner, simple, no-gym, home, 10-min', tone:'Bold', fw:['PAS','AIDA','Q','LIST']}, ecom:{niche:'ecom store owners', power:'conversion, revenue, 7-figure, unfair, CTR, checkout, bundle, LTV, upsell', tone:'Authority', fw:['AIDA','GAP','LIST']}, agency:{niche:'SMMA owners', power:'outreach, loom, steal, plug-and-play, cold, appointment, proof, case study', tone:'Bold', fw:['PAS','AIDA','GAP']}, crypto:{niche:'crypto beginners', power:'100x, airdrop, hidden, alpha, risk, exit, cycle, pattern', tone:'Curious', fw:['Q','GAP','MYTH']}, motivation:{niche:'ambitious creators', power:'discipline, daily, small wins, now, identity, future self', tone:'Bold', fw:['PAS','Q','LIST']}, tech:{niche:'indie hackers', power:'ship, fast, automate, AI, prompt, tool, remove steps, build in public', tone:'Authority', fw:['AIDA','GAP','LIST']} }; const sel=$('#presetLib'); sel?.addEventListener('change',()=>{ const v=map[sel.value]; if(!v) return; $('#niche').value=v.niche; $('#power').value=v.power; $('#tone').value=v.tone; $$('.fw').forEach(cb=> cb.checked=v.fw.includes(cb.value)); persist(); renderPreview(); toast('Preset applied','ok') }); })();

/* ---------- Export / Import ---------- */
(function(){ const saveBtn=$('#saveSettings'); const imp=$('#importSettings'); saveBtn?.addEventListener('click',()=>{ const data=localStorage.getItem('HOOK_STATE')||'{}'; const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([data],{type:'application/json'})); a.download='hook-settings.json'; a.click(); URL.revokeObjectURL(a.href) }); imp?.addEventListener('change', async ()=>{ const f=imp.files?.[0]; if(!f) return; const txt=await f.text(); try{ const obj=JSON.parse(txt); localStorage.setItem('HOOK_STATE', JSON.stringify(obj)); location.reload() }catch{ toast('Invalid settings file','error') } }) })();

/* ---------- Footer helpers ---------- */
$('#libClear')?.addEventListener('click', (e)=>{ e.preventDefault(); localStorage.removeItem('HOOK_LIBRARY'); toast('Library cleared','ok') });
$('#copyAll')?.addEventListener('click', ()=>{ const t=$$('#output .line').map(x=>x.textContent).join('\n'); navigator.clipboard.writeText(t); toast('All hooks copied','ok') });
$('#exportCSV')?.addEventListener('click', ()=>{ const l=$$('#output .line').map(x=>`"${x.textContent.replace(/"/g,'""')}"`).join('\n'); download('hooks.csv', l) });
$('#exportJSON')?.addEventListener('click', ()=>{ const l=$$('#output .line').map(x=>x.textContent); download('hooks.json', JSON.stringify(l,null,2)) });
function download(name, content){ const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([content],{type:'text/plain'})); a.download=name; a.click(); URL.revokeObjectURL(a.href) }
$('#randomize')?.addEventListener('click', ()=>{ $('#tone').value = rand(['Bold','Curious','Contrarian','Friendly','Authority','Minimal']); $('#length').value = rand(['short','medium','long']); $('#emojis').value = rand(['none','few','many']); persist(); renderPreview(); toast('Randomized controls','ok') });
$('#clear')?.addEventListener('click', ()=>{ $('#output').innerHTML=''; toast('Cleared','ok') });
$('#repeatLast')?.addEventListener('click', ()=>{ const s=localStorage.getItem('HOOK_STATE'); if(s){ toast('Last settings restored','ok'); location.reload() } });
$('#generate')?.addEventListener('click', generate);

/* ---------- Dev console toggle ---------- */
(function(){ const t=$('#devToggle'), log=$('#devLog'); t?.addEventListener('change',()=>{ log.style.display = t.checked ? 'block' : 'none' }) })();

/* ---------- History ---------- */
(function(){ const KEY='VO_HISTORY'; function read(){ return JSON.parse(localStorage.getItem(KEY)||'[]') } function write(v){ localStorage.setItem(KEY, JSON.stringify(v)); render() } function add(entry){ const v=read(); v.unshift(entry); write(v.slice(0,20)) } function render(){ const box=$('#history'); if(!box) return; box.innerHTML=''; read().forEach(h=>{ const el=document.createElement('article'); el.className='hook card'; el.innerHTML=`<div class="line">${h.name}</div><div class="meta"><span class="badge">${new Date(h.time).toLocaleString()}</span></div><div class="actions"><a class="btn" href="${h.mp4}" download>Download</a><a class="btn" href="${h.srt}" download>SRT</a></div>`; box.appendChild(el) }) } $('#clearHistory')?.addEventListener('click', ()=>{ localStorage.removeItem(KEY); render(); toast('History cleared','ok') }); window.__hist = {add}; render() })();

/* ---------- Voice population + preview ---------- */
const VOICE_KEY='VOICE_SEL';
(function(){
  const sel=$('#uVoice'); if(!sel) return;
  function populate(){
    const voices = window.speechSynthesis?.getVoices?.()||[];
    // Add concrete voices below auto entries
    const existing = new Set(Array.from(sel.options).map(o=>o.value));
    voices.forEach(v=>{
      const val = `voice_${v.name.replace(/[^a-z0-9]+/gi,'_')}`;
      if(!existing.has(val)){
        const o=document.createElement('option'); o.value=val; o.textContent=`${v.name} (${v.lang})`; sel.appendChild(o);
      }
    });
    // restore last
    const saved = localStorage.getItem(VOICE_KEY);
    if(saved && Array.from(sel.options).some(o=>o.value===saved)) sel.value = saved;
  }
  populate();
  window.speechSynthesis?.addEventListener('voiceschanged', populate);
  sel.addEventListener('change', ()=> localStorage.setItem(VOICE_KEY, sel.value));
  $('#cycleVoice')?.addEventListener('click', ()=>{
    const opts = Array.from(sel.options);
    const i = Math.max(0, opts.findIndex(o=>o.value===sel.value));
    sel.value = opts[(i+1)%opts.length].value;
    localStorage.setItem(VOICE_KEY, sel.value);
    previewSpeak();
  });
  $('#voicePreview')?.addEventListener('click', previewSpeak);
  function previewSpeak(){
    const bars=$('#voiceBars'); bars?.classList.add('active'); setTimeout(()=>bars?.classList.remove('active'),1200);
    const s=new SpeechSynthesisUtterance('This is a preview of the AI voice over.');
    const list = speechSynthesis.getVoices();
    const pickAuto = (gender)=> list.find(v=> new RegExp(gender,'i').test(v.name)) || list.find(v=> /en/i.test(v.lang)) || list[0];
    let pick;
    if(sel.value==='auto_male') pick = pickAuto('male|alex|daniel');
    else if(sel.value==='auto_female') pick = pickAuto('female|samantha|victoria|karen');
    else pick = list.find(v=> ('voice_'+v.name.replace(/[^a-z0-9]+/gi,'_'))===sel.value) || list[0];
    if(pick) s.voice = pick;
    speechSynthesis.speak(s);
  }
})();

/* ---------- Niche chips (recent) ---------- */
(function(){
  const KEY='NICHE_RECENT'; const holder=$('#nicheChips'); if(!holder) return;
  const arr = JSON.parse(localStorage.getItem(KEY)||'[]');
  function render(){
    holder.innerHTML='';
    arr.slice(0,5).forEach(txt=>{
      const b=document.createElement('span'); b.className='badge'; b.textContent=txt; b.onclick=()=>{ $('#uNiche').value = txt; toast('Niche applied','ok') }; holder.appendChild(b);
    });
  }
  $('#uNiche')?.addEventListener('change', ()=>{ const v=$('#uNiche').value; if(v && !arr.includes(v)){ arr.unshift(v); localStorage.setItem(KEY, JSON.stringify(arr.slice(0,8))); render(); }});
  render();
})();

/* ---------- Confetti ---------- */
(function(){ const cvs=document.createElement('canvas'); cvs.id='confetti'; cvs.style.cssText='position:fixed; inset:0; pointer-events:none; z-index:70'; document.body.appendChild(cvs); const ctx=cvs.getContext('2d'); let W,H; function size(){ W=cvs.width=innerWidth; H=cvs.height=innerHeight } addEventListener('resize',size); size(); function shoot(){ const P=[]; for(let i=0;i<160;i++){ P.push({x:W/2, y:H/3, vx:(Math.random()-0.5)*6, vy:Math.random()*-8-4, g:0.15+Math.random()*0.1, r:2+Math.random()*3, a:1}) } let t=0; function frame(){ ctx.clearRect(0,0,W,H); P.forEach(p=>{ p.vx*=0.99; p.vy+=p.g; p.x+=p.vx; p.y+=p.vy; p.a-=0.008; ctx.globalAlpha=Math.max(0,p.a); ctx.fillStyle=`hsl(${(t*3+p.x)%360},100%,60%)`; ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2); ctx.fill() }); t++; if(P.some(p=>p.a>0)) requestAnimationFrame(frame); else ctx.clearRect(0,0,W,H) } frame() } window.__confetti={shoot} })();

/* ---------- Uploader + Trimming + Batch queue ---------- */
(function(){
  const drop=$('#dropZone'); const fileInput=$('#videoFile'); const chooseBtn=$('#chooseBtn');
  const btn=$('#uSubmit'); const queueBtn=$('#queueBtn'); const cancelBtn=$('#cancelBtn'); const stat=$('#uStatus'); const bar=$('#uProg'); const res=$('#uResult');
  const vid=$('#uVideo'); const aud=$('#uAudio'); const aDL=$('#uDownload'); const aSRT=$('#uSrt'); const aAUD=$('#uAudioLink'); const hook=$('#uHook');
  const niche=$('#uNiche'); const voice=$('#uVoice'); const offset=$('#uOffset'); const mix=$('#uMix');
  const trimToggle=$('#trimToggle'); const tVid=$('#trimVideo'); const tStart=$('#trimStart'); const tEnd=$('#trimEnd'); const markIn=$('#markIn'); const markOut=$('#markOut'); const durInfo=$('#durationInfo');
  const queueList=$('#queueList'); const devLog=$('#devLog'); const statusLine=$('#statusLine'); const heroStatus=$('#heroStatus');

  let controller = null; const Q=[];
  function log(obj){ if(devLog){ devLog.textContent = (devLog.textContent+"\n"+ (typeof obj==='string'?obj:JSON.stringify(obj,null,2))).trim() } }

  chooseBtn?.addEventListener('click', ()=> fileInput.click());
  ;['dragenter','dragover'].forEach(ev=> drop.addEventListener(ev, e=>{ e.preventDefault(); e.stopPropagation(); drop.setAttribute('data-active','true'); heroStatus.textContent='Drop to upload'; }));
  ;['dragleave','drop'].forEach(ev=> drop.addEventListener(ev, e=>{ e.preventDefault(); e.stopPropagation(); drop.removeAttribute('data-active'); heroStatus.innerHTML='<b>Ready</b> • drop a file'; }));
  drop.addEventListener('drop', e=>{ if(e.dataTransfer.files?.length){ fileInput.files = e.dataTransfer.files; loadTrimPreview(fileInput.files[0]); toast(`${fileInput.files.length} file(s) ready`,'ok'); step(2) } })
  fileInput?.addEventListener('change', ()=>{ if(fileInput.files?.length){ const f=fileInput.files[0]; if(f.size>500*1024*1024){ toast('File too large (>500MB)','warn'); return } loadTrimPreview(f); step(2) } });

  function step(n){ $$('#step1,.step').forEach(el=> el.classList.remove('active')); for(let i=1;i<=n;i++){ $('#step'+i)?.classList.add('active') } }
  function setStatus(txt){ statusLine.firstElementChild.textContent = txt }

  function loadTrimPreview(f){ const url=URL.createObjectURL(f); tVid.src=url; tVid.onloadedmetadata=()=>{ tEnd.value=tVid.duration.toFixed(1); durInfo.textContent=`Duration: ${tVid.duration.toFixed(1)}s` } }
  markIn?.addEventListener('click', ()=>{ tStart.value=tVid.currentTime.toFixed(1) });
  markOut?.addEventListener('click', ()=>{ tEnd.value=tVid.currentTime.toFixed(1) });

  function fakeProgress(){ let p=0; bar.style.width='0%'; return setInterval(()=>{ p=Math.min(96, p+Math.random()*6); bar.style.width=p.toFixed(0)+'%' }, 180) }
  function finishProgress(id){ bar.style.width='100%'; window.__confetti?.shoot(); stat.textContent='Done'; setStatus('✅ Completed'); updateQueueItem(id,'done'); step(3); setTimeout(()=> res?.scrollIntoView({behavior:'smooth'}), 150) }

  async function trimBlob(file, start, end){ if(!trimToggle.checked) return file; return new Promise(async (resolve)=>{ try{ const v=document.createElement('video'); v.src=URL.createObjectURL(file); await v.play().catch(()=>{}); v.pause(); v.currentTime=start||0; const stream=v.captureStream(); const mr=new MediaRecorder(stream,{mimeType:'video/webm'}); const chunks=[]; mr.ondataavailable=e=>chunks.push(e.data); mr.onstop=()=> resolve(new Blob(chunks,{type:'video/webm'})); mr.start(); v.play(); const tick=setInterval(()=>{ if(v.currentTime>=end){ clearInterval(tick); v.pause(); mr.stop() } }, 100) }catch(e){ console.warn('Trim failed, using original', e); resolve(file) } }) }

  function addToQueue(files){ Array.from(files).forEach(f=>{ const id=Math.random().toString(36).slice(2,9); Q.push({id,file:f,status:'queued'}); const row=document.createElement('article'); row.className='hook card'; row.dataset.id=id; row.innerHTML=`<div class="line">${f.name}</div><div class="meta"><span class="badge">queued</span> <span class="badge size">${(f.size/1e6).toFixed(1)}MB</span></div><div class="actions"><button data-act="start" class="btn">Start</button><button data-act="remove" class="btn">Remove</button></div>`; row.addEventListener('click',(e)=>{ const act=e.target.getAttribute('data-act'); if(act==='remove'){ row.remove(); const i=Q.findIndex(x=>x.id===id); if(i>-1) Q.splice(i,1) } if(act==='start'){ processItem(id) } }); queueList.appendChild(row) }) }
  function updateQueueItem(id,status){ const el=queueList.querySelector(`[data-id="${id}"] .meta .badge`); if(el) el.textContent=status }

  queueBtn?.addEventListener('click', ()=>{ if(fileInput.files?.length){ addToQueue(fileInput.files) } else toast('Select files first','info') });
  cancelBtn?.addEventListener('click', ()=>{ controller?.abort(); stat.textContent='Canceled'; setStatus('⏸️ Canceled'); bar.style.width='0%' });

  async function processItem(id){ const item=Q.find(x=>x.id===id); if(!item) return; await uploadFile(item.file, id) }

  async function uploadFile(file, id){
    btn.classList.add('loading'); btn.disabled=true; stat.textContent='Uploading…'; setStatus('⬆️ Uploading…'); const tick=fakeProgress(); res.style.display='none';
    try{
      const start=parseFloat(tStart.value||'0'); const end=parseFloat(tEnd.value||'0')||start; const useTrim=trimToggle.checked && end>start; const src=useTrim ? await trimBlob(file,start,end) : file;
      const fd = new FormData();
      fd.append('file', new File([src], file.name.replace(/\.[^.]+$/, '.webm')));
      fd.append('niche', niche.value);
      fd.append('voice', voice.value);
      fd.append('offset', offset.value || '0');
      fd.append('mix', String(mix.value || '80'));
      fd.append('lang', 'en');
      controller=new AbortController(); const r=await fetch('/upload',{method:'POST', body:fd, signal:controller.signal}); const j=await r.json(); log(j); clearInterval(tick); if(!r.ok){ throw new Error(j?.error || 'Upload failed') }
      const mp4 = j.download_url, srt = j.srt_url, ap = j.audio_preview_url || '';
      vid.src = mp4; aDL.href = mp4;
      if (srt) aSRT.href = srt;
      if (ap) { aAUD.href = ap; aud.src = ap; aAUD.style.display=''; } else { aAUD.style.display='none'; }
      hook.textContent=j.hook_text||''; res.style.display='grid'; finishProgress(id||'single'); window.__hist?.add({time:Date.now(), name:file.name, mp4, srt});
      toast('Render completed','ok');
    }catch(err){ console.error(err); stat.textContent = 'Error'; setStatus('⛔ Error'); toast('Error: '+ err.message,'error'); updateQueueItem(id,'error') }
    finally{ btn.classList.remove('loading'); btn.disabled=false }
  }

  $('#uSubmit')?.addEventListener('click', ()=>{ const f=fileInput.files?.[0]; if(f) uploadFile(f); else toast('Select a video first','warn') });
})();

/* ---------- Auto-generate on first load + preview ---------- */
if(!$('#output')?.children.length){ generate() }
renderPreview();
