(() => {
  'use strict';
  const source='https://github.com/AGENTROPOLIS-CITY-OF-AGENTS/AGENTROPOLIS-ATG/';
  const pages={
    overview:{id:'core',title:'A language for accountable agents.',label:'Overview',intro:'<strong>ATG is the Atralith agentic language.</strong> It gives agent messages a shared structure for identity, intent, permissions, and evidence. Explore the proposed mission flow, one step at a time.',path:'README.md'},
    identity:{id:'identity',title:'Identity',label:'01 · Identity',question:'Who is acting?',intro:'Start with an explicit agent identity. The message references the actor and the context of its mission, so later evidence can be traced back to the right agent.',note:'An identity reference identifies the actor. It does not authorize an action.',path:'docs/kernel-spec-v0.1.md'},
    mandate:{id:'mandate',title:'Mandate',label:'02 · Mandate',question:'What is the agent allowed to do?',intro:'Express the mission and reference its scoped authority. The execution envelope describes the boundaries that an authorized runtime must enforce.',note:'A mandate is a bounded instruction. Tool access and model confidence do not replace authority.',path:'contracts/core/execution-envelope.schema.json'},
    plan:{id:'capability',title:'Plan',label:'03 · Plan',question:'Which capabilities fit the mission?',intro:'Describe the intended work and the capabilities it requires. The capability contract lets adapters exchange structured meaning without redefining the language.',note:'A proposed plan is not an approval. Policy and authority checks precede material execution.',path:'contracts/core/capability-abi.md'},
    execute:{id:'mcp',title:'Execute',label:'04 · Execute',question:'How does authorized work reach tools?',intro:'An approved adapter or runtime carries out work within its execution envelope. MCP connects tools; ATG expresses the intent, constraints, and evidence requirements around their use.',note:'This view illustrates execution. No tool call, transaction, or agent run occurs here.',path:'docs/HERMES_EXECUTION_ENVELOPE_PROFILE.md'},
    receipt:{id:'receipt',title:'Receipt',label:'05 · Receipt',question:'What proof remains?',intro:'Retain the result, provenance, and evidence references. A receipt makes the work inspectable and links the outcome to the mission that requested it.',note:'The examples are reference material. This demo does not produce signed or verified receipts.',path:'examples/',tree:true},
    audit:{id:'verify',title:'Audit',label:'06 · Audit',question:'What actually happened?',intro:'Compare the claimed result with its supporting evidence. Verification and audit make gaps, conflicts, and unresolved claims visible for review.',note:'A verification claim requires evidence. An animation or success badge cannot establish it.',path:'docs/ATG-PROFILE-VERIFY.md'},
    policy:{id:'policy',title:'Policy gate',label:'Constraints',question:'What boundaries apply?',intro:'Policy and authority references constrain the execution envelope. Enforcement belongs to the authorized runtime, outside the language presentation.',note:'Access is not authority. Presentation, connectivity, and discovered tools do not grant permission.',path:'docs/COGNITIVE_RUNTIME_NAMESPACE_GUARD.md'},
    language:{id:'atranic',title:'Language profile',label:'Language',question:'How is structured meaning expressed?',intro:'The ATG language surface renders structured semantic meaning for humans and agents. Domain profiles extend the language within defined boundaries.',note:'ATG is the Atralith agentic language. The language profile defines how native expressions and human-readable translations relate to structured meaning.',path:'docs/ATG-PROFILE-LANGUAGE.md'},
    atralith:{id:'atralith',title:'Atralith implementation',label:'Implementation',question:'Where can builders inspect the code?',intro:'Explore the repository’s Atralith implementation and bridge modules. Implementation code consumes the language contracts without owning their semantics.',note:'Repository code and this concept demo do not establish production readiness.',path:'atralith/',tree:true}
  };
  const flow=['identity','mandate','plan','execute','receipt','audit'];
  const panel=document.getElementById('contentPanel');
  const tourButton=document.getElementById('tourBtn');
  const motionButton=document.getElementById('motionToggle');
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  let paused=reduced.matches,timer=null,tourIndex=0,touring=false,sceneReady=false,tourHash=null;
  const escape=s=>s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function current(){return Object.hasOwn(pages,location.hash.slice(1))?location.hash.slice(1):'overview'}
  function sourceLink(p){return source+(p.tree?'tree/':'blob/')+'main/'+p.path}
  function render(){
    const key=current(),p=pages[key];
    document.querySelectorAll('.nav a').forEach(a=>{const active=a.hash==='#'+key;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current')});
    document.getElementById('currentLocation').textContent=p.title==='A language for accountable agents.'?'Overview':p.title;
    document.title=(key==='overview'?'ATG':p.title+' | ATG')+' · AGENTROPOLIS';
    let html=`<p class="eyebrow">${escape(p.label)} · ATG</p><h1 id="pageTitle">${escape(p.title)}</h1>${p.question?`<p class="eyebrow">${escape(p.question)}</p>`:''}<p class="lead">${p.intro}</p>`;
    if(key==='overview'){
      html+=`<div class="actions"><button class="primary" id="beginFlow">Explore the mission flow →</button><a href="${sourceLink(p)}">Read the specification ↗</a></div><ol class="flow-list">${flow.map((k,i)=>`<li><a href="#${k}"><em>0${i+1}</em><span><strong>${pages[k].title}</strong><small>${['Who acts','What is allowed','How to proceed','Bounded action','Evidence retained','Claims checked'][i]}</small></span></a></li>`).join('')}</ol><div class="definition"><strong>Access is not authority.</strong><br>MCP provides tool connectivity. ATG expresses meaning and constraints. An authorized runtime enforces those constraints.</div>`;
    }else{
      html+=`<div class="definition">${escape(p.note)}</div><div class="actions"><a href="${sourceLink(p)}">Read source material ↗</a><a href="#overview">Back to overview</a></div>`;
      const i=flow.indexOf(key);if(i>=0)html+=`<nav class="step-controls" aria-label="Mission steps"><a href="#${i?flow[i-1]:'overview'}">← ${i?pages[flow[i-1]].title:'Overview'}</a><a href="#${i<5?flow[i+1]:'overview'}">${i<5?pages[flow[i+1]].title:'Overview'} →</a></nav>`;
    }
    panel.innerHTML=html;
    document.getElementById('beginFlow')?.addEventListener('click',()=>{location.hash='identity'});
    window.dispatchEvent(new CustomEvent('atg:focus',{detail:{id:p.id}}));
  }
  function stopTour(message='Explore at your own pace.'){
    touring=false;tourHash=null;clearInterval(timer);timer=null;tourButton.textContent='Start guided tour';tourButton.setAttribute('aria-pressed','false');document.getElementById('tourStatus').textContent=message;
  }
  function tourStep(){if(tourIndex>=flow.length){stopTour('Tour complete. Review the source or revisit any step.');return}tourHash='#'+flow[tourIndex];if(location.hash!==tourHash){location.hash=tourHash}else{tourHash=null;revealContent()}document.getElementById('tourStatus').textContent=`Step ${tourIndex+1} of 6 · ${pages[flow[tourIndex]].title}`;tourIndex++}
  tourButton.addEventListener('click',()=>{if(touring){stopTour();return}touring=true;tourIndex=0;tourButton.textContent='Stop guided tour';tourButton.setAttribute('aria-pressed','true');tourStep();timer=setInterval(tourStep,10000)});
  document.querySelector('.nav').addEventListener('click',e=>{if(e.target.closest('a'))stopTour()});
  panel.addEventListener('click',e=>{if(e.target.closest('a,button'))stopTour()});
  document.getElementById('resetView').addEventListener('click',()=>{stopTour();location.hash='overview';window.dispatchEvent(new CustomEvent('atg:focus',{detail:{id:'core'}}))});
  function motion(){motionButton.textContent=paused?'Resume motion':'Pause motion';motionButton.setAttribute('aria-pressed',String(paused));window.dispatchEvent(new CustomEvent('atg:motion',{detail:{paused}}))}
  motionButton.addEventListener('click',()=>{paused=!paused;motion()});reduced.addEventListener('change',e=>{paused=e.matches;motion()});
  addEventListener('atg:select',e=>{stopTour();const entry=Object.entries(pages).find(([,p])=>p.id===e.detail.id);if(entry){location.hash=entry[0];document.getElementById('content').focus({preventScroll:true})}});
  addEventListener('atg:ready',()=>{sceneReady=true;render();motion()});
  setTimeout(()=>{if(!sceneReady)document.getElementById('sceneStatus').textContent='3D view unavailable. Explore every step using the navigation.'},8000);
  function revealContent(){const content=document.getElementById('content');content.focus({preventScroll:true});content.scrollIntoView({block:'start',behavior:'instant'})}
  addEventListener('hashchange',()=>{if(tourHash===location.hash){tourHash=null}else{stopTour()}render();revealContent()});
  document.querySelector('.brand').addEventListener('click',()=>{stopTour();if(location.hash==='#overview')revealContent()});
  document.addEventListener('visibilitychange',()=>{if(document.hidden)stopTour('Tour paused while the page was hidden.')});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){stopTour();location.hash='overview'}});
  render();motion();
})();
