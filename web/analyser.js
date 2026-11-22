/* Native module inspection is independent of the editable project draft. */
window.ModuleAnalyser=(()=>{
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const active=j=>['copying','analysing','explaining','converting','profiling'].includes(j?.status);
  const state={id:'',report:null,tab:'overview',search:'',page:0};
  const tabs=['overview','areas','characters','encounters','quests','dialogue','scripts','dependencies'];
  const title=s=>s.charAt(0).toUpperCase()+s.slice(1);
  const source=s=>`<small class="analysis-source">${esc(s)}</small>`;
  const json=v=>`<pre>${esc(JSON.stringify(v,null,2))}</pre>`;
  const scriptLink=n=>`<button class="quiet" data-script="${esc(n)}">Inspect ${esc(n)}</button>`;
  const detail=(label,body)=>`<details><summary>${esc(label)}</summary>${body}</details>`;
  const text=s=>`<p class="analysis-text">${esc(s)}</p>`;
  function card(row,tab){
    let body='';
    if(tab==='areas')body=text(`${row.width??'?'} × ${row.height??'?'} tiles · Tileset: ${row.tileset}`)+text(`Resource: ${row.id} · Tag: ${row.tag}`);
    if(tab==='characters')body=text(`${row.kind} · ${row.area||'Blueprint'} · Tag: ${row.tag}`)+text(row.description||'No authored description.')+text(`Conversation: ${row.conversation||'None'} · Faction ID: ${row.faction_id??'Unknown'}`)+row.inferred_role.map(text).join('')+detail('Classes, inventory and position',json({classes:row.classes,inventory:row.inventory,position:row.position}))+detail('Linked scripts',row.script_refs.map(scriptLink).join('')||text('None found.'));
    if(tab==='encounters')body=text(`${row.kind} · ${row.area||'Blueprint'} · Min/max creatures: ${row.minimum??'?'} / ${row.maximum??'?'} · Difficulty: ${row.difficulty??'?'}`)+detail('Spawn definitions',json({active:row.active,respawns:row.respawns,creatures:row.creatures}));
    if(tab==='quests')body=text(`Journal tag: ${row.tag} · XP field: ${row.xp??'Unspecified'}`)+row.entries.map(e=>detail(`Entry ${e.id}${e.end?' · final entry':''}`,text(e.text)+source(e.source))).join('')+detail('Compiled-script evidence',row.script_evidence.map(e=>`<div>${scriptLink(e.script)}${text(e.finding)}${e.offset!==undefined?text(`Offset: 0x${e.offset.toString(16)} · Journal entry argument: ${e.journal_entry??'unresolved'}`):''}</div>`).join('')||text('No direct journal call could be linked. State may be handled dynamically.'));
    if(tab==='dialogue')body=text(`${row.lines.length} NPC/player nodes. EntryList = NPC; ReplyList = player. Links point to the opposite list.`)+detail('Conversation branches',text('Starting nodes: '+JSON.stringify(row.starts))+row.lines.map(l=>`<div class="analysis-line"><strong>${esc(l.id)} · ${esc(l.role)} ${esc(l.speaker)}</strong>${text(l.text)}${l.action?scriptLink(l.action):''}${source(l.source)}${text('Links: '+JSON.stringify(l.links))}${l.links.filter(x=>x.condition).map(x=>scriptLink(x.condition)).join('')}</div>`).join(''));
    if(tab==='scripts')body=text(`${row.status} · ${row.instructions??0} instructions · Source ${row.source_available?'included':'absent'} · Debug symbols ${row.debug_available?'present (not interpreted)':'absent'}`)+text(Object.entries(row.categories).map(([n,k])=>`${n}: ${k}`).join(' · ')||'No recognized story-related calls.')+row.warnings.map(w=>text(w)).join('')+scriptLink(row.id);
    if(tab==='dependencies')body=text(`${row.kind} · ${row.found?'Found locally':'Missing'}${row.resources?' · '+row.resources+' resources':''}`)+(row.error?text(row.error):'');
    return `<article class="analysis-card"><h3>${esc(row.name||row.id||row.tag||'Unnamed')}</h3>${source(row.source||'')}${body}</article>`;
  }
  function overview(r){
    const ai=r.ai_explanation;
    return `<div class="analysis-counts">${Object.entries(r.counts).map(([k,v])=>`<div><strong>${v}</strong><span>${esc(k.replaceAll('_',' '))}</span></div>`).join('')}</div>
      <h3>Recovered story evidence</h3>${text(r.story.overview)}${text(r.story.note)}
      ${detail(`Authored excerpts (${r.story.evidence.length} of ${r.story.evidence_total})`,r.story.evidence.map(e=>`<article><h4>${esc(e.kind)}</h4>${text(e.text)}${source(e.source)}</article>`).join('')||text('No narrative text found.'))}
      ${ai?`<h3>AI interpretation</h3>${text(ai.note)}${source(ai.provider+' · '+ai.model)}${ai.claims.map(c=>`<article class="analysis-card"><h4>${esc(c.topic)}</h4>${text(c.text)}${c.evidence_ids.map(id=>{const e=ai.evidence.find(x=>x.id===id);return e?detail(id+' · '+e.kind,source(e.source)+json(e.data)):'';}).join('')}</article>`).join('')}${detail('AI uncertainties',ai.uncertainties.map(text).join(''))}`:''}
      <h3>Coverage and limits</h3>${r.warnings.length?`<div class="analysis-warning">${r.warnings.map(text).join('')}</div>`:text('No missing resources or decoding warnings were reported. This does not verify gameplay.')}
      ${r.limitations.map(text).join('')}${detail('Module identity and resource counts',json(r.module)+json(r.resource_types))}${detail('Object descriptions and lore',r.lore.slice(0,100).map(l=>`<h4>${esc(l.name)}</h4>${text(l.text)}${source(l.source)}`).join('')+text('First 100 entries shown; the JSON report contains all recovered descriptions.'))}`;
  }
  function mount(host,api,getApp){
    host.innerHTML=`<div class="module-analyser"><div class="analysis-intro"><span class="eyebrow">MODULE IMPORT AND AI CONVERSION</span><h2>Explore an existing adventure</h2><p>Import a normal NWN 1 / Enhanced Edition .mod to review its story, characters, encounters, quests and compiled scripts. Analysis is read-only. After reviewing it, create a separate AI-enabled copy below.</p></div>
      <section class="analysis-import"><h3>Import a module</h3><label>Module file <input type="file" accept=".mod" id="analysisFile"></label><button id="analysisUpload" class="primary">Import and analyse</button>
      <details><summary>Or use a path on this computer</summary><label>Full path to .mod <input id="analysisPath" placeholder="C:\\…\\modules\\adventure.mod"></label><button id="analysisStart">Analyse local file</button></details><label>Dependency folder (optional) <input id="analysisDependencies" placeholder="Folder containing the required HAK and TLK files"></label><p class="muted">Subfolders are searched. Local-path imports also search beside the module. Local analysis needs no API key. Installed NWN resources, declared HAKs and talk tables are read using Local settings. Reports may contain story spoilers.</p></section>
      <div id="analysisError" role="alert" hidden></div><div id="analysisStatus" role="status"></div>
      <div class="analysis-controls"><label>Saved analyses <select id="analysisSelect"><option value="">Select a report</option></select></label><button id="analysisRefresh">Refresh</button><button id="analysisDelete" class="danger" disabled>Delete analysis</button></div>
      <section id="analysisReport"></section><section id="analysisScript" hidden></section></div>`;
    const root=host.querySelector('.module-analyser'),q=s=>root.querySelector(s);
    let job=null,timer=null,pending=false,selection=0;
    const alive=()=>root.isConnected;
    const error=e=>{if(alive()){q('#analysisError').hidden=!e;q('#analysisError').textContent=e?.message||String(e||'');}};
    function controls(){
      const busy=pending||active(job);
      for(const id of ['#analysisUpload','#analysisStart'])q(id).disabled=busy;
      q('#analysisDelete').disabled=busy||!state.id;
      const explain=q('#analysisExplain');if(explain)explain.disabled=busy;
    }
    async function safely(fn){error(null);pending=true;controls();try{await fn();}catch(e){error(e);}finally{pending=false;if(alive())controls();}}
    function status(){q('#analysisStatus').textContent=job?`${title(job.status)} · ${job.message}`:'';const option=q('#analysisSelect').selectedOptions[0];if(job&&option?.value===job.id)option.textContent=`${job.name||job.filename} · ${job.status}`;controls();if(job?.profile_error||job?.ai_error||job?.conversion_error)error(job.profile_error||job.conversion_error||job.ai_error);}
    async function list(){
      const data=await api('/api/analyser/list',{});if(!alive())return;
      q('#analysisSelect').innerHTML='<option value="">Select a report</option>'+data.analyses.map(j=>`<option value="${esc(j.id)}">${esc(j.name||j.filename)} · ${esc(j.status)}</option>`).join('');
      if(state.id&&!data.analyses.some(j=>j.id===state.id)){state.id='';state.report=null;}
      if(!state.id)state.id=(data.analyses.find(active)||data.analyses[0])?.id||'';
      q('#analysisSelect').value=state.id;
      return data;
    }
    async function watch(){
      const id=state.id,seq=++selection;
      if(!id){job=null;status();show();return;}
      const next=await api('/api/analyser/status',{id});if(!alive()||state.id!==id||seq!==selection)return;
      job=next;status();
      if(['complete','explaining','converting','profiling'].includes(job.status)){
        const report=await api('/api/analyser/report',{id});if(!alive()||state.id!==id||seq!==selection)return;
        state.report=report;show();
      }else if(state.report?.analysis_id!==id){state.report=null;show();}
      clearTimeout(timer);
      if(active(job))timer=setTimeout(()=>{if(alive())watch().catch(error);},1800);
    }
    function show(){
      const r=state.report,box=q('#analysisReport');q('#analysisScript').hidden=true;
      if(!r||r.analysis_id!==state.id){box.innerHTML='';return;}
      const provider=getApp().settings.provider,model=provider==='gemini'?getApp().settings.authoring_gemini_model:getApp().settings.authoring_model;
      box.innerHTML=`<div class="analysis-report-heading"><div><h2>${esc(r.module.name)}</h2><p>${esc(r.module.filename)} · Read-only snapshot</p></div><a href="/api/analyser/download?id=${encodeURIComponent(state.id)}" download>Download JSON report</a></div>
        <section id="analysisConversion"></section><details class="analysis-ai"><summary>Optional AI explanation</summary><p>Send selected recovered excerpts to ${esc(provider)} using ${esc(model)} for an interpretation with evidence references. This uses your saved key and counts as module-creation usage; provider charges or limits apply. The local report already works without AI.</p><button id="analysisExplain">Explain with AI</button></details>
        <div class="analysis-tabs" role="tablist" aria-label="Module analysis">${tabs.map(t=>`<button role="tab" aria-selected="${state.tab===t}" data-analysis-tab="${t}">${title(t)}</button>`).join('')}</div>
        <div id="analysisFilter" ${state.tab==='overview'?'hidden':''}><label>Search this section <input id="analysisSearch" type="search" value="${esc(state.search)}" placeholder="Name, tag, text or function…"></label></div><div id="analysisResults" role="tabpanel"></div>`;
      box.querySelectorAll('[data-analysis-tab]').forEach(b=>b.onclick=()=>{state.tab=b.dataset.analysisTab;state.search='';state.page=0;show();});
      q('#analysisSearch').oninput=e=>{state.search=e.target.value;state.page=0;rows();};
      q('#analysisExplain').onclick=()=>safely(async()=>{job=await api('/api/analyser/explain',{id:state.id});status();await watch();});
      window.ModuleConversion?.mount(q('#analysisConversion'),api,state.id,active(job),async next=>{job=next;status();await watch();});
      rows();controls();
    }
    function rows(){
      const r=state.report,box=q('#analysisResults');if(!r||!box)return;
      if(state.tab==='overview'){box.innerHTML=overview(r);return;}
      const key=state.tab==='dialogue'?'dialogues':state.tab;
      const items=(r[key]||[]).filter(x=>!state.search||JSON.stringify(x).toLowerCase().includes(state.search.toLowerCase()));
      const max=Math.max(0,Math.ceil(items.length/12)-1);state.page=Math.min(state.page,max);
      box.innerHTML=(state.tab==='encounters'?text('Native encounter triggers and blueprints. Script-created creatures and fixed placed monsters also appear under Characters and Scripts.'):state.tab==='scripts'?text('Disassembly and conservative static analysis, not recovered original source. A call can be conditional or unreachable. Null arguments mean unresolved.'):state.tab==='dependencies'?text('HAKs and custom TLKs declared by the module. Other resources may come from overrides, NWSync or external databases that this report does not simulate.'):'')+
        `<p>${items.length} matching records · Page ${state.page+1} of ${max+1}</p>`+items.slice(state.page*12,state.page*12+12).map(x=>card(x,state.tab)).join('')+(items.length?'':text('No records found in this section.'))+
        `<div class="analysis-paging"><button id="analysisPrevious" ${state.page?'':'disabled'}>Previous</button><button id="analysisNext" ${state.page<max?'':'disabled'}>Next</button></div>`;
      q('#analysisPrevious').onclick=()=>{state.page--;rows();};q('#analysisNext').onclick=()=>{state.page++;rows();};
      box.querySelectorAll('[data-script]').forEach(b=>b.onclick=()=>safely(()=>inspect(b.dataset.script)));
    }
    async function inspect(name){
      const id=state.id,data=await api('/api/analyser/script',{id,script:name});if(!alive()||id!==state.id)return;
      const panel=q('#analysisScript');panel.hidden=false;
      panel.innerHTML=`<div class="analysis-report-heading"><h2>${esc(name)}.ncs</h2><button id="analysisCloseScript">Close script</button></div>${text(data.interpretation)}${data.warnings.map(text).join('')}<a href="/api/analyser/disassembly?id=${encodeURIComponent(id)}&script=${encodeURIComponent(name)}" download>Download full disassembly</a>
        ${detail(`Call sites (${data.calls.length})`,text('First 200 shown. Null = unresolved. The disassembly download contains every decoded instruction.')+json(data.calls.slice(0,200)))}
        ${detail(`Branches (${data.branches.length})`,json(data.branches.slice(0,200)))}${detail('String constants',json(data.strings.slice(0,200)))}
        <h3>Disassembly</h3><p>First 1,000 lines shown. Download for the full decoded listing.</p><pre>${esc(data.disassembly.split('\n').slice(0,1000).join('\n'))}</pre>`;
      q('#analysisCloseScript').onclick=()=>{panel.hidden=true;};panel.scrollIntoView({behavior:'smooth',block:'start'});
    }
    async function imported(j){state.id=j.id;state.report=null;state.page=0;state.tab='overview';job=j;await list();await watch();}
    q('#analysisStart').onclick=()=>safely(async()=>imported(await api('/api/analyser/start',{path:q('#analysisPath').value,dependency_folder:q('#analysisDependencies').value})));
    q('#analysisUpload').onclick=()=>safely(async()=>{
      const file=q('#analysisFile').files[0];if(!file)throw Error('Choose a .mod file first.');
      q('#analysisStatus').textContent='Uploading a private analysis snapshot…';
      const response=await fetch('/api/analyser/upload?filename='+encodeURIComponent(file.name)+'&dependencies='+encodeURIComponent(q('#analysisDependencies').value),{method:'POST',headers:{'Content-Type':'application/octet-stream','X-Studio-Token':getApp().csrf},body:file});
      const result=await response.json();if(!response.ok)throw Error(result.error||'Module upload failed');if(alive())await imported(result);
    });
    q('#analysisSelect').onchange=()=>safely(async()=>{state.id=q('#analysisSelect').value;state.report=null;state.page=0;await watch();});
    q('#analysisRefresh').onclick=()=>safely(async()=>{await list();await watch();});
    q('#analysisDelete').onclick=()=>safely(async()=>{
      if(!confirm('Delete this analysis report and its private imported snapshot? Your original module and Studio projects will remain unchanged.'))return;
      await api('/api/analyser/delete',{id:state.id,confirm:true});state.id='';state.report=null;await list();await watch();
    });
    safely(async()=>{await list();await watch();});
  }
  return {mount};
})();
