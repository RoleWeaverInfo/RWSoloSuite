/* Native adapter for the shared mission editor and graph viewport. */
(()=>{
  const M=window.NativeMissionModel,C=window.ManagedMissionModel,sessions=new Map();
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function mount(host,{getProject,onChange,onCheck,onSave,onCopy,onInspect=()=>{},onNotice=()=>{},baseline,evidence={},conversion={missions:[],targets:{}},disabled=false,historyKey=''}){
    const p=()=>getProject(),w=()=>p().mission_editor,sessionKey=historyKey||p().id,initial=JSON.stringify(M.snapshot(p()));
    let state=sessions.get(sessionKey);
    if(!state||state.last!==initial)state={last:initial,quest:'',selected:'@story',edge:-1,undo:[],redo:[],group:'',views:{},evidence:false};
    sessions.set(sessionKey,state);
    let viewport,pick=null,review=null,disposed=false,resolveConfirmation=null,copying=false;
    const el=s=>host.querySelector(s),q=()=>w().quests.find(q=>q.id===state.quest),s=()=>q()?.stages.find(s=>M.key(q(),s)===state.selected);
    const selectedQuest=()=>q()||w().quests.find(q=>q.id===state.selected),copied=()=>C?.get(p(),selectedQuest()?.tag),managed=()=>state.nativeView?undefined:copied(),objective=()=>managed()?.quest.steps.find(s=>C.key(q()?.id,s)===state.selected);
    const button=(label,action,attrs='')=>`<button type="button" data-native-action="${action}" ${attrs}>${label}</button>`;
    const field=(label,path,value,max,rows=0)=>`<label class="field"><span>${esc(label)}</span>${rows?`<textarea rows="${rows}" maxlength="${max}" data-native-field="${path}">${esc(value)}</textarea>`:`<input maxlength="${max}" value="${esc(value)}" data-native-field="${path}">`}</label>`;
    function changed(){state.last=JSON.stringify(M.snapshot(p()));review=null;onChange();}
    function mutate(fn,group='',full=true){
      if(disabled)return false;const before=M.snapshot(p());
      try{fn();for(const m of p().mission_control?.missions||[]){if(m.adapter!=='native_journal_v1')continue;const old=before.mission_control?.missions.find(o=>o.source_tag===m.source_tag);if(old){if(JSON.stringify(old.quest.steps)!==JSON.stringify(m.quest.steps)||old.quest.giver!==m.quest.giver)m.objectives_reviewed=false;if(old.quest.gold!==m.quest.gold||old.quest.xp!==m.quest.xp)m.rewards_reviewed=false;}}}catch(error){Object.assign(p(),before);onNotice(error.message,true);return false;}
      if(JSON.stringify(before)===JSON.stringify(M.snapshot(p())))return true;
      if(!group||state.group!==group){state.undo.push(before);if(state.undo.length>40)state.undo.shift();}
      state.group=group;state.redo=[];changed();if(full)render();else refresh();return true;
    }
    function ensure(){if(state.quest&&!q()){state.quest='';state.selected='@story';}if(state.quest&&!s()&&!objective())state.selected=state.quest;if(!w().links[state.edge])state.edge=-1;}
    function refresh(fit=false){
      viewport.setGraph(M.graph(p(),state.quest,evidence,state.evidence,state.nativeView),state.selected,fit);
      el('[data-native-action="undo"]').disabled=disabled||!state.undo.length;el('[data-native-action="redo"]').disabled=disabled||!state.redo.length;
      el('.native-help').textContent=pick?'Choose a destination card. This records your interpretation, not a change to compiled triggers. Escape cancels.':'Drag to pan; Ctrl + wheel to zoom. Dashed arrows are creator review links. Solid evidence arrows identify journal writes, not progression order.';
      if(managed()&&state.quest)el('.native-help').textContent='Solid arrows are executable objective order. Select a card to edit, move or remove it. '+(managed().mode==='studio'?'Studio control will be used in the next copy.':'Inactive draft: the next copy will still use the original quest.');
      el('[data-native-action="link"]').disabled=disabled||!!(managed()&&state.quest);
      const edits=M.changes(w(),baseline);
      el('.native-changes').innerHTML=`<strong>${edits.length} journal text change${edits.length===1?'':'s'} for the next copy</strong><p>Native journal review labels, notes and arrows are private annotations. They are saved with the conversion profile and withheld from gameplay AI prompts. The public premise remains available to AI characters.</p>${edits.length?`<ul>${edits.map(e=>`<li>${esc(e.label)}</li>`).join('')}</ul>`:''}${review?`<h4>Conversion check</h4>${[...review.errors,...review.warnings].map(t=>`<p>${esc(t)}</p>`).join('')||'<p>No mission review issues.</p>'}`:''}`;
      if(p().mission_control?.missions.length)el('.native-changes').innerHTML+=p().mission_control.missions.map(m=>`<p><strong>${esc(m.quest.name)}: ${m.mode==='studio'?'Studio-controlled · experimental':'Original control · inactive draft'}</strong><br>${m.quest.steps.length} executable objectives · ${m.quest.gold} gold / ${m.quest.xp} completion XP. Native review arrows remain annotations; only Studio objective arrows are executable.</p>`).join('');
      for(const option of el('.native-quest').options){const item=w().quests.find(q=>q.id===option.value);if(item)option.textContent=item.name||item.tag;}
      for(const option of el('.native-stage')?.options||[]){const item=q()?.stages.find(s=>M.key(q(),s)===option.value);if(item)option.textContent='Entry '+item.native_id+' · '+item.label;}
    }
    function sources(rows){return rows.length?rows.map(e=>`<article class="native-source"><strong>${esc(e.kind)} · ${esc(e.confidence)}</strong><p>${esc(e.text)}</p><small>${esc(e.source)}</small>${e.script?button('Inspect '+esc(e.script),'script:'+e.script,'class="quiet"'):''}</article>`).join(''):'<p>No direct writer was recovered for this stage. It may be controlled dynamically or by unresolved native scripts.</p>';}
    function details(){
      const link=w().links[state.edge];
      if(link)return `<h3>Review link</h3><p class="hint">${esc(link.from)} → ${esc(link.to)}. This is your interpretation of the story, not an executable connection.</p>${field('Link description','link.label',link.label,200)}${button('Remove review link','removeLink','class="danger"')}`;
      const quest=q()||w().quests.find(q=>q.id===state.selected),stage=s();
      if(!quest)return `<h3>Storyline & mission overview</h3>${field('Public setting and adventure premise','project.summary',p().summary,3000,4)}${field('Private storyline and review notes','workspace.storyline',w().storyline,20000,9)}<p class="hint">Use private notes for plot twists, a walkthrough and questions for review. Only the public premise is sent as setting information to AI characters.</p><p>${w().quests.length} native journal quests. Entry numbering is not proof of chronology. Use reviewed arrows to record paths you have checked against the journal, dialogue and script evidence.</p>`;
      const original=baseline.quests.find(q=>q.id===quest.id);
      const controls=C?C.controls(copied(),conversion.missions.find(m=>m.tag===quest.tag),state.nativeView):'';
      if(managed())return controls+C.details(managed(),objective(),conversion.targets,conversion.missions.find(m=>m.tag===quest.tag)||{});
      if(!stage)return controls+`<h3>Edit native mission</h3><p class="hint">Immutable tag: ${esc(quest.tag)}<br>${esc(quest.source)}</p>${field('Journal quest name · exported','quest.name',quest.name,500)}${field('Private mission notes','quest.notes',quest.notes,6000,5)}<div class="mission-buttons">${button('Open stage map','stages','class="primary"')}${button('Restore original journal name','resetName')}</div><details><summary>Recovered mission evidence</summary>${sources(evidence[quest.id]?.sources||[])}</details>`;
      const old=original.stages.find(e=>e.id===stage.id);
      return controls+`<h3>Edit journal stage</h3><p class="hint">Entry ${stage.native_id} · ${stage.end?'Native final entry':'Native non-final entry'}<br>Identity, completion flag, triggers and rewards remain native unless Studio control is enabled for this quest.</p>${field('Map label · review only','stage.label',stage.label,120)}${field('Journal text · exported to the copy','stage.text',stage.text,40000,9)}${field('Private stage notes','stage.notes',stage.notes,6000,4)}${button('Restore original journal text','resetText')}<details><summary>Original journal text</summary><p class="analysis-text">${esc(old.text)}</p></details><details open><summary>Evidence for this journal stage</summary>${sources(evidence[quest.id]?.stages?.[stage.id]||[])}</details>`;
    }
    function confirm(message){
      if(resolveConfirmation)resolveConfirmation(false);
      const box=el('.native-confirm');box.innerHTML=`<form method="dialog"><h3>Confirm edit</h3><p>${esc(message)}</p><div class="mission-buttons"><button value="cancel">Cancel</button><button value="confirm" class="danger">Confirm</button></div></form>`;
      return new Promise(resolve=>{resolveConfirmation=resolve;box.returnValue='cancel';box.onclose=()=>{resolveConfirmation=null;resolve(box.returnValue==='confirm');};box.showModal();});
    }
    function choose(node){
      state.group='';
      if(pick){if(node.kind==='evidence'||node.id==='@story')return;const from=pick;if(mutate(()=>{state.edge=M.link(w(),from,node.id);pick=null;}))return;refresh();return;}
      if(node.kind==='evidence'){state.selected=M.key(q(),q().stages.find(s=>s.id===node.stage));state.edge=-1;render();return;}
      state.edge=-1;state.selected=node.id;if(node.kind==='mission'&&!state.quest)state.selected=node.quest;render();
    }
    function selectQuest(id){state.quest=id;state.selected=id||'@story';state.edge=-1;state.group='';state.nativeView=false;pick=null;render();}
    async function act(action){
      if(disabled)return;state.group='';
      if(action==='overview'){selectQuest('');return;}
      if(action==='stages'){const id=state.quest||w().quests.find(q=>q.id===state.selected)?.id||w().quests[0]?.id;if(id)selectQuest(id);return;}
      if(action==='story'){selectQuest('');state.selected='@story';render();return;}
      if(action==='fit'||action==='focus'){viewport[action]();return;}
      if(action==='zoomIn'||action==='zoomOut'){viewport.zoom(action==='zoomIn'?1.25:.8);return;}
      if(action==='undo'||action==='redo'){const from=action==='undo'?state.undo:state.redo,to=action==='undo'?state.redo:state.undo;if(from.length){to.push(M.snapshot(p()));Object.assign(p(),from.pop());state.edge=-1;pick=null;changed();render();}return;}
      if(action==='save'){await onSave();return;}
      if(action==='check'){const before=state.last;const result=await onCheck();if(!disposed&&before===state.last){review=result;refresh();}return;}
      if(action==='copyMission'){if(copying)return;const quest=selectedQuest();copying=true;el('[data-native-action="copyMission"]').disabled=true;try{const result=await onCopy(quest.tag);if(!disposed)mutate(()=>{p().mission_control??={version:1,missions:[]};if(!C.get(p(),quest.tag))p().mission_control.missions.push(result.mission);state.quest=quest.id;state.selected=quest.id;state.nativeView=false;state.views[quest.id]={};});}finally{copying=false;if(!disposed&&el('[data-native-action="copyMission"]'))el('[data-native-action="copyMission"]').disabled=disabled;}return;}
      if(action==='nativeView'||action==='managedView'||action==='managedSettings'){state.nativeView=action==='nativeView';state.edge=-1;state.quest=selectedQuest().id;state.selected=state.quest;state.views[state.quest]={};render();return;}
      if(action==='addObjective'&&managed()){mutate(()=>{const item=C.add(managed(),conversion.targets);state.quest=selectedQuest().id;state.selected=C.key(state.quest,item);});return;}
      if(action==='removeObjective'&&objective()){const item=objective();if(await confirm('Remove this executable objective? The surrounding objectives will be reconnected. This can change what the player must do. Undo is available.'))mutate(()=>{C.remove(managed(),item.id);state.selected=state.quest;});return;}
      if((action==='moveEarlier'||action==='moveLater')&&objective()){mutate(()=>C.move(managed(),objective().id,action==='moveEarlier'?-1:1));return;}
      if(action==='link'){if(state.selected==='@story'||state.selected===state.quest){onNotice('Select a mission card in the overview, or a stage card in its map first.');return;}pick=state.selected;state.edge=-1;refresh();return;}
      if(action==='removeLink'){const index=state.edge;if(await confirm('Remove this review arrow? Native scripts and quest progression are unchanged. Undo is available.'))mutate(()=>{w().links.splice(index,1);state.edge=-1;});return;}
      if(action==='resetText'&&s()){const quest=q(),stage=s();if(await confirm('Restore this stage’s original journal text? Undo is available.'))mutate(()=>stage.text=baseline.quests.find(o=>o.id===quest.id).stages.find(o=>o.id===stage.id).text);return;}
      if(action==='resetName'){const quest=q()||w().quests.find(q=>q.id===state.selected);if(quest&&await confirm('Restore the original journal quest name? Undo is available.'))mutate(()=>quest.name=baseline.quests.find(o=>o.id===quest.id).name);return;}
      if(action.startsWith('script:'))await onInspect(action.slice(7));
    }
    function render(){
      ensure();viewport?.destroy();const key=state.quest||'overview',fresh=!state.views[key];state.views[key]??={};
      host.innerHTML=`<section class="native-missions"><h3>Story & mission editor</h3><p>Import journal missions into editable drafts, review their objectives and rewards, then choose control separately for each mission. Original scripts remain the default; unresolved script conflicts are listed before takeover.</p><div class="mission-toolbar"><div class="mission-buttons">${button('Mission overview','overview')}${button('Stage map','stages',!w().quests.length?'disabled':'')}${button('Storyline','story')}</div><label>Mission <select class="native-quest" aria-label="Native mission"><option value="">All missions</option>${w().quests.map(q=>`<option value="${q.id}" ${q.id===state.quest?'selected':''}>${esc(q.name||q.tag)}</option>`).join('')}</select></label><div class="mission-buttons">${button('Undo','undo')}${button('Redo','redo')}${button('Check edits','check')}${button('Save conversion edits','save','class="primary"')}</div></div>
        <div class="mission-layout"><div class="mission-left"><div class="mission-map-tools">${button('Link selected card','link')}<div class="mission-buttons">${button('−','zoomOut','aria-label="Zoom native mission map out"')}<output class="native-zoom"></output>${button('+','zoomIn','aria-label="Zoom native mission map in"')}${button('Fit','fit')}${button('Focus','focus')}</div></div><div class="mission-viewport"></div><p class="native-help" role="status"></p>${state.quest?`<label class="check"><input type="checkbox" class="native-evidence" ${state.evidence?'checked':''}> Show recovered journal writers on the map</label>`:''}<div class="native-changes mission-status"></div></div><aside class="mission-inspector">${q()?`<label class="field"><span>Jump to stage</span><select class="native-stage"><option value="${q().id}">Mission settings</option>${q().stages.map(s=>`<option value="${M.key(q(),s)}" ${state.selected===M.key(q(),s)?'selected':''}>Entry ${s.native_id} · ${esc(s.label)}</option>`).join('')}</select></label>`:''}${details()}</aside></div><dialog class="native-confirm"></dialog></section>`;
      viewport=window.MissionGraph.mount(el('.mission-viewport'),{view:state.views[key],onSelect:choose,onEdge:e=>{if(e.review){state.edge=e.index;state.selected=e.from;render();}else if(e.evidence?.script)onInspect(e.evidence.script);},onZoom:v=>{if(!disposed&&el('.native-zoom'))el('.native-zoom').textContent=v+'%';}});
      if(managed()&&q())el('.native-stage').innerHTML=`<option value="${q().id}">Mission settings & rewards</option>${managed().quest.steps.map((s,i)=>`<option value="${C.key(q().id,s)}" ${state.selected===C.key(q().id,s)?'selected':''}>Objective ${i+1} · ${esc(s.name)}</option>`).join('')}`;
      if(managed()&&el('.native-evidence'))el('.native-evidence').closest('label').hidden=true;
      refresh(fresh);
      el('.native-quest').onchange=e=>selectQuest(e.target.value);
      if(el('.native-stage'))el('.native-stage').onchange=e=>{state.selected=e.target.value;state.edge=-1;pick=null;render();viewport.focus();};
      if(el('.native-evidence'))el('.native-evidence').onchange=e=>{state.evidence=e.target.checked;refresh();viewport.fit();};
      host.querySelectorAll('[data-native-action]').forEach(b=>b.onclick=()=>act(b.dataset.nativeAction).catch(e=>onNotice(e.message,true)));
      if(el('.managed-mode'))el('.managed-mode').onchange=async e=>{const m=copied(),value=e.target.value;try{if(value==='studio'&&m.adapter==='native_journal_v1'&&(!m.objectives_reviewed||!m.rewards_reviewed)){onNotice('Review the objective bindings and reward evidence in Mission settings, then check both review boxes.',true);render();return;}if(value==='studio'&&!await confirm('Try Studio control for this mission? Identified journal and reward calls are replaced in the new copy. Native conditions and other effects remain and can conflict with edited objectives. Keep the original module, build a separate copy and start a new game to test.')){render();return;}mutate(()=>{m.mode=value;m.risk_acknowledged=value==='studio';});}catch(error){onNotice(error.message,true);}};
      host.querySelectorAll('[data-native-field]').forEach(c=>{c.oninput=()=>{const [type,field]=c.dataset.nativeField.split('.');const quest=selectedQuest();const target=type==='project'?p():type==='workspace'?w():type==='quest'?quest:type==='stage'?s():type==='mission'?managed():type==='managed'?managed()?.quest:type==='reward'?managed()?.rewards:type==='objective'?objective():w().links[state.edge];mutate(()=>{target[field]=c.type==='checkbox'?c.checked:c.type==='number'?Number(c.value):c.value;if(type==='objective'&&field==='kind'){target.target=(conversion.targets[c.value]||[])[0]?.id||'';target.consume=false;}if(type==='managed'&&field==='giver')managed().quest.steps.at(-1).target=c.value;},c.dataset.nativeField,field==='kind'||field==='giver');if(managed()?.adapter==='native_journal_v1')for(const name of ['objectives_reviewed','rewards_reviewed']){const box=el('[data-native-field="mission.'+name+'"]');if(box)box.checked=managed()[name];}};c.onblur=()=>{state.group='';};});
      host.onkeydown=e=>{if(e.key==='Escape'&&pick){pick=null;refresh();}};
      host.querySelectorAll('button,input,textarea,select').forEach(c=>{if(disabled)c.disabled=true;});
    }
    render();return {destroy(){disposed=true;viewport?.destroy();resolveConfirmation?.(false);host.onkeydown=null;},setDisabled(value){disabled=value;render();}};
  }
  window.MissionEditor.registerAdapter(3,mount);
})();
