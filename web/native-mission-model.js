/* Native journal adapter. Review arrows never become quest-engine transitions. */
window.NativeMissionModel=(()=>{
  const copy=v=>JSON.parse(JSON.stringify(v)),key=(q,s)=>q.id+':'+s.id;
  const snapshot=p=>copy({summary:p.summary,mission_editor:p.mission_editor,mission_control:p.mission_control||{version:1,missions:[]}});
  const nodes=w=>w.quests.flatMap(q=>[q.id,...q.stages.map(s=>key(q,s))]);
  function link(w,from,to){
    const ids=nodes(w);
    if(!ids.includes(from)||!ids.includes(to)||from===to)throw Error('Choose two different mission cards or stage cards.');
    if(from.includes(':')!==to.includes(':')||(from.includes(':')&&from.split(':')[0]!==to.split(':')[0]))throw Error('Link stages within one mission. Use the overview to link missions.');
    if(w.links.some(l=>l.from===from&&l.to===to))throw Error('These cards already have a review link.');
    if(w.links.length>=2000)throw Error('This review has reached its 2,000-link limit.');
    w.links.push({from,to,label:'Reviewed story path'});return w.links.length-1;
  }
  function changes(w,baseline){
    const out=[];
    for(const q of w.quests){const old=baseline.quests.find(o=>o.id===q.id);if(!old)continue;
      if(q.name!==old.name)out.push({quest:q.id,stage:'',field:'name',label:q.name+' · journal name'});
      for(const s of q.stages){if(s.text!==old.stages.find(o=>o.id===s.id)?.text)out.push({quest:q.id,stage:s.id,field:'text',label:q.name+' · Entry '+s.native_id});}
    }return out;
  }
  function graph(p,questId='',evidence={},showEvidence=false,nativeOnly=false){
    const w=p.mission_editor,q=w.quests.find(q=>q.id===questId);
    const managed=q&&window.ManagedMissionModel?.get(p,q.tag);
    if(managed&&!nativeOnly)return window.ManagedMissionModel.graph(managed,q.id);
    const nodeList=q?q.stages.map(s=>({id:key(q,s),quest:q.id,stage:s.id,kind:'native-stage',label:s.label||'Entry '+s.native_id,badge:'ENTRY '+s.native_id+(s.end?' · NATIVE FINAL':''),lines:[s.text.split(/\n\s*\n/).at(-1),s.notes||'Native triggers and rewards retained']})):
      [...w.quests.map(q=>({id:q.id,quest:q.id,kind:'mission',label:q.name||q.tag,badge:'NATIVE JOURNAL QUEST',lines:[q.stages.length+' stages · '+q.stages.filter(s=>s.end).length+' final entries',q.tag]})),{id:'@story',kind:'story',label:'Storyline & review notes',badge:'CREATOR WORKSPACE',lines:['Private plot notes and public premise','Not a native quest completion gate']}];
    if(!q)for(const node of nodeList){const native=w.quests.find(q=>q.id===node.id),controlled=native&&window.ManagedMissionModel?.get(p,native.tag);if(controlled){node.label=controlled.quest.name;node.badge=controlled.mode==='studio'?'STUDIO CONTROL · EXPERIMENTAL':'NATIVE QUEST · EDITABLE DRAFT';node.lines=[controlled.quest.steps.length+' editable objectives',native.tag];}}
    const visible=new Set(nodeList.map(n=>n.id));
    const edges=w.links.map((l,i)=>({...l,index:i,review:true,optional:true})).filter(l=>visible.has(l.from)&&visible.has(l.to));
    if(q&&showEvidence){
      let counter=0;for(const s of q.stages)for(const e of evidence[q.id]?.stages?.[s.id]||[]){
        const id='@e'+counter++;nodeList.push({id,quest:q.id,stage:s.id,kind:'evidence',label:e.source,badge:e.confidence.toUpperCase(),lines:[e.kind,e.text],evidence:e});
        edges.push({from:id,to:key(q,s),label:'Journal write',evidence:e});
      }
    }
    return {nodes:nodeList,edges};
  }
  return {copy,key,snapshot,link,changes,graph};
})();
