/* Independent runtime profiles for copies of community modules. */
window.ModuleConversion=(()=>{
  const drafts=new Map();
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function mount(host,api,id,busy,onStarted){
    let current=null,selected=0;
    const alive=()=>host.isConnected,q=s=>host.querySelector(s);
    host.innerHTML='<details class="analysis-conversion"><summary>Create an AI-enabled copy</summary><p>Loading conversion profile…</p></details>';
    const message=(s,error=false)=>{if(alive()){q('.conversion-message').textContent=s;q('.conversion-message').classList.toggle('analysis-warning',error);}};
    const remember=()=>drafts.set(id,{project:current.project,dependency_folder:current.dependency_folder});
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
        ${n.native_store?.detected?`<fieldset><legend>Native merchant</legend><label><input type="checkbox" data-merchant-field="enabled" ${n.merchant.enabled?'checked':''}> Enable AI merchant abilities</label><label><input type="checkbox" data-merchant-field="haggle_enabled" ${n.merchant.haggle_enabled?'checked':''}> Allow requests to negotiate through the original trading conversation</label><p class="muted">Enabled by default for detected stores. Browse the original shop once to let AI discuss its real current stock. Browsing and negotiation return to the original trading menu; native prices, Appraise rules, gold and item transfers stay in control.</p><p class="analysis-source">Store links: ${esc(n.native_store.tags.join(', ')||'resolved from native variables during play')} · Scripts: ${esc(n.native_store.scripts.join(', '))}</p></fieldset>`:''}
        <p class="muted">${esc(n.profile_origin||'Creator profile')} Native dialogue memory: ${n.native_lines?.length||0} lines, available to AI only after that character and player reach them.</p>
        <details><summary>Profile evidence</summary>${(n.profile_sources||[]).map(s=>`<p class="analysis-source">${esc(s)}</p>`).join('')}</details>
        <label>Communication <select data-npc-field="communication"><option value="speech" ${n.behavior.communication==='speech'?'selected':''}>Speech</option><option value="nonverbal" ${n.behavior.communication==='nonverbal'?'selected':''}>Gestures and sounds</option></select></label>`;
      q('.conversion-npc').querySelectorAll('[data-npc-field]').forEach(el=>{el.disabled=busy;el.oninput=()=>{const k=el.dataset.npcField;if(k==='communication'){n.behavior.communication=el.value;n.companion.communication=el.value;}else n[k]=el.type==='checkbox'?el.checked:el.value;remember();};});
      q('.conversion-npc').querySelectorAll('[data-merchant-field]').forEach(el=>{el.disabled=busy;el.onchange=()=>{n.merchant[el.dataset.merchantField]=el.checked;remember();};});
    }
    function render(){
      const p=current.project,b=current.build;
      host.innerHTML=`<details class="analysis-conversion" open><summary>Create an AI-enabled copy</summary>
        <p>Add free-form AI conversations, merchant support and companion tools to a separate module. Original maps, encounters, quest scripts and stores remain in control. Recruitment and dismissal use the original menus. This requires NWN: Enhanced Edition.</p>
        <p class="muted">Profiles include authored descriptions and setting information. Generate richer personalities and everyday backgrounds with your authoring model, then review them. Generation uses your API key and is tracked as authoring usage. Original conversations are remembered as they happen; unseen story branches stay unavailable during gameplay.</p>
        <div class="analysis-controls"><label>Copy title <input class="conversion-title" value="${esc(p.title)}" maxlength="160"></label><label>New module filename <input class="conversion-name" value="${esc(p.module_name)}" maxlength="16"> .mod</label></div>
        <label>Required HAK/TLK folder <input class="conversion-deps" value="${esc(current.dependency_folder)}" placeholder="Folder containing the original module dependencies"></label>
        <label><input class="conversion-companions" type="checkbox" ${p.companions.enabled?'checked':''}> Companion conversations, controls, storage and errands for already recruited allies, familiars and summons</label>
        <p>${p.npcs.filter(n=>n.native_store?.detected).length} merchant profiles detected. AI merchant abilities default on; review or disable them per character below.</p>
        <label>Public setting and adventure premise <textarea class="conversion-summary" maxlength="3000" rows="4">${esc(p.summary)}</textarea></label>
        <div class="analysis-controls"><button class="conversion-profiles">Generate detailed AI profiles</button></div>
        <p class="muted">Replaces role, personality, background and motivation for all imported characters. Public knowledge edits are retained. Generated everyday history is creative elaboration, not recovered author canon. Creating the module copy itself needs no AI request.</p>
        <details><summary>Review ${p.npcs.length} creature profiles</summary><label>Character <select class="conversion-select">${p.npcs.map((n,i)=>`<option value="${i}">${esc(n.name)} — ${esc(n.native_tag)}</option>`).join('')}</select></label><div class="conversion-npc"></div></details>
        <p>Creates a new copy and verifies preserved resources. Test quests, transitions, rest/death and companion recruitment before sharing. Original authors retain their rights; obtain permission before redistributing their modules or packs.</p>
        <div class="analysis-controls"><button class="conversion-save">Save AI profile</button><button class="conversion-build primary">Create AI-enabled copy</button></div>
        <p class="conversion-message" role="status"></p>
        ${b?`<article class="analysis-card"><h3>Last converted copy: ${esc(b.module)}</h3><p>${esc(b.title)} · ${b.areas} areas · ${b.quests} native quests</p><p>Static preservation checks passed. Gameplay testing is still required. Start a new game in this copy; original saved games do not contain the additions.</p><div class="analysis-controls"><a href="/download?build=${encodeURIComponent(b.build_id)}&kind=zip" download>Download AI copy + dependencies</a><a href="/download?build=${encodeURIComponent(b.build_id)}&kind=project" download>Download AI profile</a><a href="/download?build=${encodeURIComponent(b.build_id)}&kind=preservation" download>Preservation report</a><button class="conversion-install">Install copy locally</button><button class="conversion-delete danger">Delete exported copy</button></div></article>`:''}
        </details>`;
      npc();q('.conversion-select').onchange=e=>{selected=Number(e.target.value);npc();};
      for(const [selector,key] of [['.conversion-title','title'],['.conversion-name','module_name']])q(selector).oninput=e=>{p[key]=e.target.value;remember();};
      q('.conversion-deps').oninput=e=>{current.dependency_folder=e.target.value;remember();};
      q('.conversion-summary').oninput=e=>{p.summary=e.target.value;remember();};
      q('.conversion-companions').onchange=e=>{p.companions.enabled=e.target.checked;remember();};
      host.querySelectorAll('button,input,textarea,select').forEach(el=>el.disabled=busy);
      async function run(fn){host.querySelectorAll('button').forEach(el=>el.disabled=true);try{await fn();}catch(e){message(e.message,true);}finally{if(alive())host.querySelectorAll('button').forEach(el=>el.disabled=busy);}}
      q('.conversion-save').onclick=()=>run(async()=>{await api('/api/analyser/conversion-save',{id,project:p,dependency_folder:current.dependency_folder});message('AI profile saved. Create a new copy to apply changes in NWN.');});
      q('.conversion-profiles').onclick=()=>run(async()=>{const job=await api('/api/analyser/profiles',{id,project:p,dependency_folder:current.dependency_folder});drafts.delete(id);message(job.message);await onStarted(job);});
      q('.conversion-build').onclick=()=>run(async()=>{remember();const job=await api('/api/analyser/convert',{id,project:p,dependency_folder:current.dependency_folder});message(job.message);await onStarted(job);});
      if(b)q('.conversion-delete').onclick=()=>run(async()=>{if(!confirm('Delete this exported AI copy and its packaged files? Installed modules, original modules and saved games remain unchanged.'))return;await api('/api/build/delete',{build_id:b.build_id,confirm:true});const saved=await api('/api/analyser/conversion-plan',{id});current.build=saved.build;render();});
      if(b)q('.conversion-install').onclick=()=>run(async()=>{const result=await api('/api/install',{build_id:b.build_id});message('Installed '+result.installed+'. Keep Role Weaver running, start NWN separately and select this copy for a new game.');});
    }
    api('/api/analyser/conversion-plan',{id}).then(data=>{if(!alive())return;current={...data,...drafts.get(id)};render();}).catch(e=>{if(alive())host.textContent='Conversion profile unavailable: '+e.message;});
  }
  return {mount};
})();
