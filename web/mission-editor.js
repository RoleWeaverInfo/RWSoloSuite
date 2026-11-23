/* Shared mission entry point, with format-specific authoring/import adapters. */
window.MissionEditor=(()=>{
  const sessions=new Map(),adapters=new Map(),M=window.MissionModel;
  const esc=window.MissionGraph? v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])):String;
  function mount(host,options){
    if(adapters.has(options.getProject().schema_version))return adapters.get(options.getProject().schema_version)(host,options);
    const {getProject,onChange,onCheck,onGenerate,onNotice=()=>{}}=options;
    const p=()=>getProject(),key=p().id,current=JSON.stringify(M.snapshot(p()));
    let state=sessions.get(key);
    if(!state||state.last!==current)state={last:current,undo:[],redo:[],view:'',quest:p().quests[0]?.id||'',selected:'',views:{},group:''};
    sessions.set(key,state);let pick=null,graphView,checking=false,review=null;
    const q=()=>p().quests.find(q=>q.id===state.quest),step=()=>q()?.steps.find(s=>s.id===state.selected),el=s=>host.querySelector(s);
    const button=(label,action,attrs='')=>`<button type="button" data-mission-action="${action}" ${attrs}>${label}</button>`;
    const input=(label,key,value,type='text',options=[])=>`<label class="field"><span>${esc(label)}</span>${type==='textarea'?`<textarea data-mission-field="${key}" rows="3">${esc(value)}</textarea>`:type==='select'?`<select data-mission-field="${key}">${options.map(([id,name])=>`<option value="${esc(id)}" ${id===value?'selected':''}>${esc(name)}</option>`).join('')}</select>`:type==='checkbox'?`<input type="checkbox" data-mission-field="${key}" ${value?'checked':''}>`:`<input data-mission-field="${key}" type="${type}" value="${esc(value)}" ${type==='number'?'min="0" max="10000" step="1"':'maxlength="100"'}>`}</label>`;
    function mutate(fn,group='',full=true){
      const before=M.snapshot(p());try{fn();}catch(error){Object.assign(p(),before);onNotice(error.message,true);return false;}
      const after=JSON.stringify(M.snapshot(p()));if(after===JSON.stringify(before))return true;
      if(!group||state.group!==group){state.undo.push(before);if(state.undo.length>60)state.undo.shift();}state.group=group;state.redo=[];state.last=after;review=null;onChange();
      if(full)render();else{updateGraph();validation();toolbarState();}return true;
    }
    function travel(back){const from=back?state.undo:state.redo,to=back?state.redo:state.undo;if(!from.length)return;to.push(M.snapshot(p()));Object.assign(p(),from.pop());state.last=JSON.stringify(M.snapshot(p()));state.group='';pick=null;review=null;onChange();render();}
    function ensure(){if(!q()){state.quest=p().quests[0]?.id||'';state.view='';state.selected='';}if(state.view&&state.view!==state.quest)state.view=state.quest;if(state.selected&&!step()&&!['@start','@complete','@ending'].includes(state.selected))state.selected='';}
    function toolbarState(){el('[data-mission-action="undo"]').disabled=!state.undo.length;el('[data-mission-action="redo"]').disabled=!state.redo.length;el('[data-mission-action="objectives"]').disabled=!q();el('[data-mission-action="check"]').disabled=checking;}
    function validation(){const problems=M.issues(p());el('.mission-validation').innerHTML=`<div class="mission-status ${problems.length?'has-issues':''}"><strong>${problems.length?problems.length+' mission issue'+(problems.length===1?'':'s'):'Mission connections look complete'}</strong><span>Full adventure checks also verify rooms, gates and item dependencies.</span></div>${problems.length?`<ul>${problems.map((e,i)=>`<li><button class="quiet" data-issue="${i}">${esc((p().quests.find(q=>q.id===e.quest)?.name||'Adventure')+': '+e.message)}</button></li>`).join('')}</ul>`:''}${review?`<div class="mission-review"><strong>Full adventure check</strong>${[...review.errors,...review.warnings].length?`<ul>${[...review.errors,...review.warnings].map(s=>`<li>${esc(s)}</li>`).join('')}</ul>`:'<p>No errors or warnings.</p>'}</div>`:''}`;
      el('.mission-validation').querySelectorAll('[data-issue]').forEach(b=>b.onclick=()=>{const e=problems[Number(b.dataset.issue)];if(e.quest){state.quest=e.quest;state.view=e.quest;state.selected=e.step||'@start';pick=null;render();}});
    }
    function updateGraph(autoFit=false){
      graphView.setGraph(M.graph(p(),state.view),state.view?state.selected:state.selected==='@ending'?'@ending':state.quest,autoFit);
      for(const option of el('.mission-select').options){const quest=p().quests.find(q=>q.id===option.value);if(quest)option.textContent=quest.name+(quest.optional?' · optional':'');}
      for(const option of el('.mission-objective-select')?.options||[]){const s=q()?.steps.find(s=>s.id===option.value);if(s)option.textContent=s.name;}
      el('.mission-pick').textContent=pick?'Choose a destination card or Mission complete. Escape cancels.':'Drag the background to pan. Ctrl + wheel to zoom. Fit shows all paths; Focus enlarges the selection. Select a card or arrow to edit.';
    }
    function chooseNode(node){state.group='';if(pick){if(node.step||node.kind==='complete'){const pending=pick;if(mutate(()=>M.connect(q(),pending.step,node.step||'',pending.choice))){pick=null;state.selected=pending.step;render();}}return;}
      if(node.kind==='mission'){state.quest=node.quest;state.selected='';}else if(node.kind==='ending'){state.selected='@ending';}else if(node.quest){state.quest=node.quest;state.selected=node.step||node.id;}render(false);
    }
    function details(){
      const quest=q(),s=step(),next=[['','Complete this mission'],...(quest?.steps||[]).filter(o=>o!==s).map(o=>[o.id,o.name])];
      if(state.selected==='@ending')return `<h3>Adventure story & ending</h3><p class="hint">The ending appears after every main mission completes. Optional missions do not block it.</p>${['summary','story','opening','ending'].map(k=>input({summary:'Adventure summary',story:'Storyline',opening:'Opening text',ending:'Adventure ending'}[k],'project.'+k,p()[k],'textarea')).join('')}`;
      if(!quest)return '<h3>Your mission workspace</h3><p>Add a mission or generate missions with AI. Generated objectives and choices appear on this map when you apply the proposal.</p>'+button('Generate missions with AI','generate');
      if(state.view&&s)return `<div class="eyebrow">OBJECTIVE · ${esc(s.id)}</div><h3>Edit objective</h3>${input('Objective name','step.name',s.name)}${input('Journal instruction / decision text','step.description',s.description,'textarea')}${input('Objective type','step.kind',s.kind,'select',Object.entries(M.kinds))}${input('Target','step.target',s.target,'select',[['','Choose a target'],...M.targets(p(),s.kind).map(t=>[t.id,t.name])])}<p class="hint">${s.kind==='choice'?'Choices appear in the selected character’s native dialogue.':'This objective completes when the player performs the selected action.'}</p>${s.kind==='choice'?s.choices.map((c,i)=>`<div class="mission-choice"><strong>Choice ${i+1}</strong>${input('Player choice','choice.'+i+'.label',c.label)}${input('Response / outcome text','choice.'+i+'.text',c.text,'textarea')}${input('Then','choice.'+i+'.next',c.next,'select',next)}<div class="mission-buttons">${button('Pick destination on map','pick:'+i)}${button('Remove choice','removeChoice:'+i,'class="quiet danger"')}</div></div>`).join('')+button('＋ Choice','addChoice',s.choices.length>=6?'disabled':''):`${input('Next objective','step.next',s.next,'select',next)}${button('Pick destination on map','pick')}${s.kind==='retrieve'?input('Consume item when completed','step.consume',s.consume,'checkbox'):''}`}<div class="mission-buttons after-card">${button('Make first objective','first',quest.steps[0]===s?'disabled':'')}${button('Remove objective','removeStep','class="danger"')}</div><p class="hint">Removing a normal objective reconnects incoming arrows to its next objective. Removing a decision sends its incoming arrows to completion. Undo restores the entire edit.</p>`;
      return `<div class="eyebrow">MISSION · ${esc(quest.id)}</div><h3>${state.selected==='@complete'?'Completion & rewards':'Edit mission'}</h3>${input('Mission name','quest.name',quest.name)}${input('Story purpose','quest.description',quest.description,'textarea')}${input('Starts when talking to','quest.start_npc',quest.start_npc,'select',[['','Start automatically'],...p().npcs.map(n=>[n.id,n.name])])}${input('Optional side mission','quest.optional',quest.optional,'checkbox')}<fieldset><legend>Prerequisite missions · all must finish</legend>${p().quests.filter(o=>o!==quest).map(o=>`<label class="check"><input data-prerequisite="${esc(o.id)}" type="checkbox" ${quest.requires.includes(o.id)?'checked':''}>${esc(o.name)}</label>`).join('')||'<p class="hint">No other missions yet.</p>'}</fieldset>${input('Completion text','quest.completion',quest.completion,'textarea')}<div class="row">${input('Gold reward','quest.gold',quest.gold,'number')}${input('XP reward','quest.xp',quest.xp,'number')}</div><p class="hint">Completion grants these rewards once. The first objective is the entry point.</p><div class="mission-buttons">${button('Edit objective map','objectives','class="primary"')}${button('Remove mission','removeQuest','class="danger"')}</div>`;
    }
    function bindFields(){
      host.querySelectorAll('[data-mission-field]').forEach(control=>{control.oninput=()=>{
        const path=control.dataset.missionField,[type,key,field]=path.split('.'),target=type==='project'?p():type==='quest'?q():type==='step'?step():step().choices[Number(key)],prop=type==='choice'?field:key;
        const value=control.type==='checkbox'?control.checked:control.type==='number'?Number(control.value):control.value;
        if(path==='step.kind'){
          const s=step();if(s.kind==='choice'&&value!=='choice'&&!window.confirm('Replace this decision with a normal objective? Its choices will be removed. You can undo this change.')){control.value=s.kind;return;}
          mutate(()=>{const next=s.kind==='choice'?s.choices[0]?.next||'':s.next;s.kind=value;s.target=M.targets(p(),value)[0]?.id||'';s.next=value==='choice'?'':next;s.consume=false;s.choices=value==='choice'?[{label:'First choice',text:'',next},{label:'Second choice',text:'',next}]:[];});return;
        }
        const before=target[prop];const ok=mutate(()=>{if(prop==='next')M.connect(q(),step().id,value,type==='choice'?Number(key):null);else target[prop]=value;},path,control.tagName==='SELECT'||control.type==='checkbox');if(!ok)control.value=before;
      };control.onblur=()=>{state.group='';};});
      host.querySelectorAll('[data-prerequisite]').forEach(control=>control.onchange=()=>mutate(()=>{q().requires=q().requires.filter(id=>id!==control.dataset.prerequisite);if(control.checked)q().requires.push(control.dataset.prerequisite);}));
    }
    async function act(action){
      state.group='';const quest=q(),s=step();
      if(action==='undo'||action==='redo'){travel(action==='undo');return;}
      if(action==='fit'){graphView.fit();return;}if(action==='focus'){graphView.focus();return;}if(action==='zoomIn'||action==='zoomOut'){graphView.zoom(action==='zoomIn'?1.25:.8);return;}
      if(action==='overview'||action==='objectives'){state.view=action==='overview'?'':state.quest;state.selected=state.view?'@start':'';pick=null;render();return;}
      if(action==='story'){state.selected='@ending';render(false);return;}
      if(action==='generate'){onGenerate();return;}
      if(action==='check'){checking=true;toolbarState();const checked=state.last;try{const result=await onCheck();if(host.isConnected&&checked===state.last){review=result;validation();}}catch(e){onNotice(e.message,true);}finally{checking=false;if(host.isConnected)toolbarState();}return;}
      if(action==='addQuest'){mutate(()=>{const q=M.newQuest(p());state.quest=q.id;state.view=q.id;state.selected='@start';});return;}
      if(action==='addStep'||action==='addDecision'){if(!quest){onNotice('Add a mission first.',true);return;}if(mutate(()=>{const after=s||quest.steps.at(-1);const added=M.addStep(p(),quest,after,action==='addDecision'?'choice':'talk');state.view=quest.id;state.selected=added.id;}))graphView.focus();return;}
      if(action==='first'&&s){mutate(()=>{quest.steps.splice(quest.steps.indexOf(s),1);quest.steps.unshift(s);});return;}
      if(action.startsWith('pick')&&s){pick={step:s.id,choice:action.includes(':')?Number(action.split(':')[1]):null};updateGraph();return;}
      if(action==='removeStep'&&s){const next=s.kind==='choice'?'mission completion':quest.steps.find(o=>o.id===s.next)?.name||'mission completion';if(window.confirm(`Remove “${s.name}”? Incoming connections will go to ${next}. This can change which objectives the player must complete. Undo is available.`))mutate(()=>{M.removeStep(quest,s.id);state.selected='@start';pick=null;});return;}
      if(action==='removeQuest'&&quest){const refs=M.references(p(),quest.id);if(refs.length){onNotice('Remove this mission’s references first: '+refs.join('; '),true);return;}if(window.confirm(`Remove mission “${quest.name}” and all its objectives? Undo is available.`))mutate(()=>{p().quests=p().quests.filter(o=>o!==quest);state.quest='';pick=null;});return;}
      if(action==='addChoice'&&s){if(s.choices.length<6)mutate(()=>s.choices.push({label:'New choice',text:'',next:''}));return;}
      if(action.startsWith('removeChoice:')&&s){if(window.confirm('Remove this player choice and its connection? Undo is available.'))mutate(()=>{s.choices.splice(Number(action.split(':')[1]),1);pick=null;});}
    }
    function render(autoFit){
      ensure();graphView?.destroy();const viewKey=state.view||'overview';const fresh=!state.views[viewKey];state.views[viewKey]??={};
      host.innerHTML=`<div class="mission-toolbar"><div class="mission-buttons">${button('Adventure overview','overview',!state.view?'class="active"':'')}${button('Mission objectives','objectives',state.view?'class="active"':'')}${button('Story details','story')}</div><label>Mission <select class="mission-select" aria-label="Selected mission">${p().quests.map(q=>`<option value="${esc(q.id)}" ${q.id===state.quest?'selected':''}>${esc(q.name)}${q.optional?' · optional':''}</option>`).join('')||'<option value="">No missions</option>'}</select></label><div class="mission-buttons">${button('Undo','undo')}${button('Redo','redo')}${button('Check adventure','check')}</div></div>
        <div class="mission-layout"><div class="mission-left"><div class="mission-map-tools"><div class="mission-buttons">${button('＋ Mission','addQuest')}${button('＋ Objective','addStep')}${button('＋ Decision','addDecision')}</div><div class="mission-buttons">${button('−','zoomOut','aria-label="Zoom mission map out"')}<output class="mission-zoom" aria-label="Mission zoom"></output>${button('+','zoomIn','aria-label="Zoom mission map in"')}${button('Fit','fit')}${button('Focus','focus')}</div></div><div class="mission-viewport"></div><p class="mission-pick" role="status"></p><p class="hint">${state.view?'Arrows are executable objective paths. A decision follows the player’s chosen branch.':'Arrows show prerequisites. All prerequisite missions must complete before a mission starts. All main missions are required for the adventure ending.'}</p><div class="mission-validation" aria-live="polite"></div></div><aside class="mission-inspector">${state.view?`<label class="field"><span>Jump to objective</span><select class="mission-objective-select">${[['@start','Mission start & settings'],...q().steps.map(s=>[s.id,s.name]),['@complete','Completion & rewards']].map(([id,name])=>`<option value="${esc(id)}" ${id===state.selected?'selected':''}>${esc(name)}</option>`).join('')}</select></label>`:''}${details()}</aside></div>`;
      graphView=window.MissionGraph.mount(el('.mission-viewport'),{view:state.views[viewKey],onSelect:chooseNode,onEdge:e=>{if(e.quest){state.quest=e.quest;state.selected=e.step||'@start';render(false);}},onZoom:z=>{if(host.isConnected)el('.mission-zoom').textContent=z+'%';}});
      updateGraph(autoFit===true||fresh);validation();toolbarState();bindFields();
      el('.mission-select').onchange=e=>{state.quest=e.target.value;if(state.view)state.view=state.quest;state.selected=state.view?'@start':'';state.group='';pick=null;render();};
      if(el('.mission-objective-select'))el('.mission-objective-select').onchange=e=>{state.selected=e.target.value;state.group='';pick=null;render();graphView.focus();};
      host.querySelectorAll('[data-mission-action]').forEach(b=>b.onclick=()=>act(b.dataset.missionAction).catch(e=>onNotice(e.message,true)));
      host.onkeydown=e=>{if(e.key==='Escape'&&pick){pick=null;updateGraph();}};
    }
    render();return {destroy(){graphView?.destroy();host.onkeydown=null;}};
  }
  return {mount,registerAdapter:(version,adapter)=>adapters.set(version,adapter)};
})();
