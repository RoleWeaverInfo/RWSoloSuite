/* Independent runtime profiles for copies of community modules. */
window.ModuleConversion=(()=>{
  const drafts=new Map();
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const panels=new Map();
  function mount(host,api,id,busy,onStarted,onInspect=()=>{}){
    let current=null,selected=0,missionEditor=null,disposed=false,requestPending=false;
    const alive=()=>!disposed&&host.isConnected,q=s=>host.querySelector(s);
    host.innerHTML='<details class="analysis-conversion"><summary>Create an AI-enabled copy</summary><p>Loading conversion profile…</p></details>';
    const message=(s,error=false)=>{if(alive()){q('.conversion-message').textContent=s;q('.conversion-message').classList.toggle('analysis-warning',error);}};
    const remember=()=>drafts.set(id,{project:current.project,dependency_folder:current.dependency_folder});
    function setBusy(value){
      busy=value;
      if(!alive()||!current)return;
      host.querySelectorAll('button,input,textarea,select').forEach(el=>el.disabled=busy||requestPending);
      const progress=current.profile_generation;
      if(progress&&progress.completed>=progress.total)q('.conversion-profiles').disabled=true;
      missionEditor?.setDisabled(busy||requestPending);
    }
    function npc(){
      const n=current.project.npcs[selected];
      q('.conversion-npc').innerHTML=`<label><input type="checkbox" data-npc-field="ai_enabled" ${n.ai_enabled?'checked':''}> Enable AI conversation</label>
        <p class="muted">Native identity: ${esc(n.native_tag)} · ${esc(n.native_resref)}. The module keeps its original creature and scripts.</p>
        <label>Chat alias <input data-npc-field="alias" value="${esc(n.alias)}" maxlength="32"></label>
        <label>Role <input data-npc-field="role" value="${esc(n.role)}" maxlength="200"></label>
        <label>Personal background <textarea data-npc-field="background" maxlength="3000" rows="4">${esc(n.background||'')}</textarea></label>
        <label>Personality <textarea data-npc-field="personality" maxlength="3000" rows="3">${esc(n.personality)}</textarea></label>
        <label>Motivation <textarea data-npc-field="motivation" maxlength="2000" rows="3">${esc(n.motivation)}</textarea></label>
        <label>Public knowledge <textarea data-npc-field="knowledge" maxlength="6000" rows="4">${esc(n.knowledge)}</textarea></label>
        ${n.native_store?.detected?`<fieldset><legend>Native merchant</legend><label><input type="checkbox" data-merchant-field="enabled" ${n.merchant.enabled?'checked':''}> Enable AI merchant abilities</label><label><input type="checkbox" data-merchant-field="haggle_enabled" ${n.merchant.haggle_enabled?'checked':''}> Allow requests to negotiate through the original trading conversation</label><p class="muted">Enabled by default for detected stores. Browse the original shop once to let AI discuss its real current stock. Stock questions stay in chat. Explicit trading requests open the native store directly where a safe shortcut exists; required introductions and gated choices keep their original menus. Native prices, Appraise rules, gold and item transfers stay in control.</p><p class="analysis-source">Store links: ${esc(n.native_store.tags.join(', ')||'resolved from native variables during play')} · Scripts: ${esc(n.native_store.scripts.join(', '))}</p></fieldset>`:''}
        <p class="muted">${esc(n.profile_origin||'Creator profile')} Native dialogue memory: ${n.native_lines?.length||0} lines, available to AI only after that character and player reach them.</p>
        <details><summary>Profile evidence</summary>${(n.profile_sources||[]).map(s=>`<p class="analysis-source">${esc(s)}</p>`).join('')}</details>
        <label>Communication <select data-npc-field="communication"><option value="speech" ${n.behavior.communication==='speech'?'selected':''}>Speech</option><option value="nonverbal" ${n.behavior.communication==='nonverbal'?'selected':''}>Gestures and sounds</option></select></label>`;
      q('.conversion-npc').querySelectorAll('[data-npc-field]').forEach(el=>{el.disabled=busy;el.oninput=()=>{const k=el.dataset.npcField;if(k==='communication'){n.behavior.communication=el.value;n.companion.communication=el.value;}else n[k]=el.type==='checkbox'?el.checked:el.value;remember();};});
      q('.conversion-npc').querySelectorAll('[data-merchant-field]').forEach(el=>{el.disabled=busy;el.onchange=()=>{n.merchant[el.dataset.merchantField]=el.checked;remember();};});
    }
    function render(){
      missionEditor?.destroy();missionEditor=null;
      const p=current.project,b=current.build;
      const generation=current.profile_generation||{completed:0,total:p.npcs.length,remaining_requests:Math.ceil(p.npcs.length/6)};
      host.innerHTML=`${p.mission_editor?`<div class="analysis-controls conversion-views"><button class="conversion-show-missions">Missions & storyline</button><button class="conversion-show-profiles">AI profiles & build</button></div><section class="conversion-missions"></section>`:''}<div class="conversion-profile-panel"><details class="analysis-conversion" open><summary>Create an AI-enabled copy</summary>
        <p>Add free-form AI conversations, merchant support and companion tools to a separate module. Original quests remain in control unless you explicitly enable an available experimental Studio mission conversion. Review that choice in Missions & storyline. Maps and unrelated quests are retained. This requires NWN: Enhanced Edition.</p>
        <p class="muted">Profiles include authored descriptions and setting information. Generate richer personalities and everyday backgrounds with your authoring model, then review them. Generation uses your API key and is tracked as authoring usage. Original conversations are remembered as they happen; unseen story branches stay unavailable during gameplay.</p>
        <div class="analysis-controls"><label>Copy title <input class="conversion-title" value="${esc(p.title)}" maxlength="160"></label><label>New module filename <input class="conversion-name" value="${esc(p.module_name)}" maxlength="64" pattern="[a-z][a-z0-9_]{0,63}" aria-describedby="conversionFilenameHint"> .mod</label></div>
        <p id="conversionFilenameHint" class="muted">Up to 64 lowercase letters, digits or underscores, starting with a letter. Enter the filename without .mod. The copy title is the name shown in NWN.</p>
        <label>Required HAK/TLK folder <input class="conversion-deps" value="${esc(current.dependency_folder)}" placeholder="Folder containing the original module dependencies"></label>
        <label><input class="conversion-companions" type="checkbox" ${p.companions.enabled?'checked':''}> Companion conversations, controls, storage and errands for already recruited allies, familiars and summons</label>
        <p>${p.npcs.filter(n=>n.native_store?.detected).length} merchant profiles detected. AI merchant abilities default on; review or disable them per character below.</p>
        <label>Public setting and adventure premise <textarea class="conversion-summary" maxlength="3000" rows="4">${esc(p.summary)}</textarea></label>
        <div class="analysis-controls"><button class="conversion-profiles">${generation.completed>=generation.total?'All detailed profiles saved':generation.completed?'Resume detailed AI profiles':'Generate detailed AI profiles'}</button><button class="conversion-profiles-restart" ${generation.completed?'':'hidden'}>Regenerate all profiles…</button></div>
        <p class="conversion-generation-summary">${generation.completed} of ${generation.total} detailed profiles saved. ${generation.remaining_requests} AI requests remaining (up to six characters per request). Large modules can take many minutes; progress appears above.</p>
        <p class="muted">Updates role, personality, background and motivation for unfinished characters. Completed batches are saved immediately; resume skips them and retains your public knowledge edits. Regenerate all replaces previously generated characterization. Generated everyday history is creative elaboration, not recovered author canon. Creating the module copy itself needs no AI request.</p>
        <details><summary>Review ${p.npcs.length} creature profiles</summary><label>Character <select class="conversion-select">${p.npcs.map((n,i)=>`<option value="${i}">${esc(n.name)} — ${esc(n.native_tag)}</option>`).join('')}</select></label><div class="conversion-npc"></div></details>
        <p>Creates a new copy and verifies preserved resources. Test quests, transitions, rest/death and companion recruitment before sharing. Original authors retain their rights; obtain permission before redistributing their modules or packs.</p>
        <div class="analysis-controls"><button class="conversion-save">Save conversion edits</button><button class="conversion-build primary">Create AI-enabled copy</button></div>
        ${b?`<article class="analysis-card"><h3>Last converted copy: ${esc(b.module)}</h3><p>${esc(b.title)} · ${b.areas} areas · ${b.quests} native quests</p><p>Static preservation checks passed. Gameplay testing is still required. Start a new game in this copy; original saved games do not contain the additions.</p><div class="analysis-controls"><a href="/download?build=${encodeURIComponent(b.build_id)}&kind=zip" download>Download AI copy + dependencies</a><a href="/download?build=${encodeURIComponent(b.build_id)}&kind=project" download>Download AI profile</a><a href="/download?build=${encodeURIComponent(b.build_id)}&kind=preservation" download>Preservation report</a><button class="conversion-install">Install copy locally</button><button class="conversion-delete danger">Delete exported copy</button></div></article>`:''}
        </details></div><p class="conversion-message" role="status"></p>`;
      npc();q('.conversion-select').onchange=e=>{selected=Number(e.target.value);npc();};
      for(const [selector,key] of [['.conversion-title','title'],['.conversion-name','module_name']])q(selector).oninput=e=>{p[key]=e.target.value;remember();};
      q('.conversion-deps').oninput=e=>{current.dependency_folder=e.target.value;remember();};
      q('.conversion-summary').oninput=e=>{p.summary=e.target.value;remember();};
      q('.conversion-companions').onchange=e=>{p.companions.enabled=e.target.checked;remember();};
      setBusy(busy);
      async function run(fn){requestPending=true;setBusy(busy);try{await fn();}catch(e){message(e.message,true);}finally{requestPending=false;if(alive())setBusy(busy);}}
      const save=()=>run(async()=>{await api('/api/analyser/conversion-save',{id,project:p,dependency_folder:current.dependency_folder});remember();message('Conversion edits saved. Create a new AI-enabled copy to apply mission and journal changes in NWN.');});
      q('.conversion-save').onclick=save;
      const profiles=restart=>run(async()=>{
        if(restart&&!confirm('Regenerate every character profile? This replaces their role, background, personality and motivation as each batch finishes and makes new API requests. Public knowledge and other conversion edits are retained.'))return;
        const job=await api('/api/analyser/profiles',{id,project:p,dependency_folder:current.dependency_folder,restart});drafts.delete(id);setBusy(job.status==='profiling');message(job.message);await onStarted(job);
      });
      q('.conversion-profiles').onclick=()=>profiles(false);
      q('.conversion-profiles-restart').onclick=()=>profiles(true);
      q('.conversion-build').onclick=()=>run(async()=>{remember();const job=await api('/api/analyser/convert',{id,project:p,dependency_folder:current.dependency_folder});message(job.message);await onStarted(job);});
      if(b)q('.conversion-delete').onclick=()=>run(async()=>{if(!confirm('Delete this exported AI copy and its packaged files? Installed modules, original modules and saved games remain unchanged.'))return;await api('/api/build/delete',{build_id:b.build_id,confirm:true});const saved=await api('/api/analyser/conversion-plan',{id});current.build=saved.build;render();});
      if(b)q('.conversion-install').onclick=()=>run(async()=>{const result=await api('/api/install',{build_id:b.build_id});message('Installed '+result.installed+'. Keep Role Weaver running, start NWN separately and select this copy for a new game.');});
      if(p.mission_editor){
        function panel(name){
          if(name!=='missions'){missionEditor?.destroy();missionEditor=null;}
          panels.set(id,name);q('.conversion-missions').hidden=name!=='missions';q('.conversion-profile-panel').hidden=name!=='profiles';
          q('.conversion-show-missions').classList.toggle('primary',name==='missions');q('.conversion-show-profiles').classList.toggle('primary',name==='profiles');
          if(name==='missions'&&!missionEditor)missionEditor=window.MissionEditor.mount(q('.conversion-missions'),{
            getProject:()=>current.project,baseline:current.mission_baseline,evidence:current.mission_evidence,conversion:current.mission_conversion,disabled:busy,historyKey:id,
            onChange:()=>{remember();q('.conversion-summary').value=current.project.summary;message('Unsaved conversion edits. Save before creating the next copy.');},
            onSave:save,onCheck:()=>api('/api/analyser/missions-review',{id,project:current.project}),onCopy:tag=>api('/api/analyser/mission-copy',{id,project:current.project,tag}),onNotice:message,onInspect});
        }
        q('.conversion-show-missions').onclick=()=>panel('missions');q('.conversion-show-profiles').onclick=()=>panel('profiles');panel(panels.get(id)||'missions');
      }
    }
    async function refresh(){
      const opened=current?Array.from(host.querySelectorAll('details')).map(el=>el.open):null;
      const data=await api('/api/analyser/conversion-plan',{id});if(!alive())return;
      current={...data,...drafts.get(id)};selected=Math.min(selected,current.project.npcs.length-1);render();
      q('.conversion-select').value=String(selected);
      if(opened)host.querySelectorAll('details').forEach((el,i)=>{if(i<opened.length)el.open=opened[i];});
    }
    refresh().catch(e=>{if(alive())host.textContent='Conversion profile unavailable: '+e.message;});
    return {refresh,setBusy,destroy(){disposed=true;missionEditor?.destroy();}};
  }
  return {mount};
})();
