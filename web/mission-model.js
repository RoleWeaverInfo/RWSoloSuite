/* Adapter between executable format-2 quests and the shared mission graph.
   Graph layout and editor state are never written into the playable project. */
window.MissionModel=(()=>{
  const copy=v=>JSON.parse(JSON.stringify(v));
  const kinds={talk:'Talk to a character',visit:'Visit a room',retrieve:'Retrieve an item',defeat:'Defeat an encounter',interact:'Resolve an interaction',choice:'Player decision'};
  const rooms=p=>p.areas.flatMap(a=>a.rooms.map(r=>({...r,name:a.name+' / '+r.name})));
  function targets(p,kind){return kind==='visit'?rooms(p):kind==='talk'||kind==='choice'?p.npcs:kind==='retrieve'?p.items:p.encounters.filter(e=>kind==='defeat'?['combat','ambush'].includes(e.kind):!['combat','ambush'].includes(e.kind));}
  const exits=s=>s.kind==='choice'?s.choices.map(c=>c.next):[s.next];
  function snapshot(p){return copy({quests:p.quests,summary:p.summary,story:p.story,opening:p.opening,ending:p.ending});}
  function references(p,id){return [
    ...p.quests.filter(q=>q.id!==id&&q.requires.includes(id)).map(q=>'Mission: '+q.name),
    ...p.npcs.filter(n=>n.reveal_after===id||n.dialogue.some(d=>d.after_quest===id)).map(n=>'Character knowledge/dialogue: '+n.name),
    ...p.encounters.filter(e=>e.after_quest===id).map(e=>'Encounter: '+e.name),
    ...p.connections.filter(c=>c.requires_quest===id).map(c=>'Passage: '+c.name)];}
  function newId(p,prefix){const used=JSON.stringify(p);let i=1;while(used.includes('"'+prefix+i+'"'))i++;return prefix+i;}
  function newQuest(p){if(p.quests.length>=16)throw Error('An adventure supports up to 16 missions.');const q={id:newId(p,'quest_'),name:'New mission',description:'',start_npc:'',completion:'The mission is complete.',optional:false,requires:[],gold:0,xp:100,steps:[]};p.quests.push(q);return q;}
  function addStep(p,q,after,kind='talk'){
    if(q.steps.length>=20)throw Error('A mission supports up to 20 objectives.');
    const old=after&&after.kind!=='choice'?after.next:'';
    const s={id:newId(p,'objective_'),name:kind==='choice'?'New decision':'New objective',description:'',kind,target:targets(p,kind)[0]?.id||'',next:kind==='choice'?'':old,consume:false,choices:kind==='choice'?[{label:'First choice',text:'',next:old},{label:'Second choice',text:'',next:old}]:[]};
    if(after&&after.kind!=='choice')after.next=s.id;q.steps.push(s);return s;
  }
  function connect(q,from,to,choice=null){
    const source=q.steps.find(s=>s.id===from);if(!source||to&&!q.steps.some(s=>s.id===to))throw Error('Choose an objective in this mission.');
    const visited=new Set(),todo=[to];while(todo.length){const id=todo.pop();if(!id||visited.has(id))continue;if(id===from)throw Error('That connection creates a loop. Mission paths must reach completion.');visited.add(id);const s=q.steps.find(s=>s.id===id);if(s)todo.push(...exits(s));}
    if(source.kind==='choice'){if(!Number.isInteger(choice)||!source.choices[choice])throw Error('Choose the decision branch to connect.');source.choices[choice].next=to;}else source.next=to;
  }
  function removeStep(q,id){
    const s=q.steps.find(s=>s.id===id);if(!s)return;const next=s.kind==='choice'?'':s.next;
    for(const other of q.steps){if(other.next===id)other.next=next;for(const c of other.choices)if(c.next===id)c.next=next;}
    const wasFirst=q.steps[0]===s;q.steps=q.steps.filter(o=>o!==s);
    if(wasFirst&&next){const i=q.steps.findIndex(o=>o.id===next);if(i>0)q.steps.unshift(...q.steps.splice(i,1));}
  }
  function issues(p){
    const out=[],add=(q,s,message)=>out.push({quest:q?.id||'',step:s?.id||'',message}),ids=new Set(p.quests.map(q=>q.id));
    function cyclic(map){const active=new Set(),done=new Set();function walk(id){if(active.has(id))return true;if(done.has(id))return false;active.add(id);for(const n of map.get(id)||[])if(map.has(n)&&walk(n))return true;active.delete(id);done.add(id);return false;}return [...map.keys()].some(walk);}
    if(cyclic(new Map(p.quests.map(q=>[q.id,q.requires]))))add(null,null,'Mission prerequisites contain a loop.');
    for(const q of p.quests){
      if(!q.name.trim())add(q,null,'Give this mission a name.');
      for(const dep of q.requires)if(!ids.has(dep))add(q,null,'Missing prerequisite mission: '+dep);
      if(q.start_npc&&!p.npcs.some(n=>n.id===q.start_npc))add(q,null,'The starting character is missing.');
      if(!q.steps.length){add(q,null,'Add at least one objective.');continue;}
      if(q.steps.length>20)add(q,null,'Use at most 20 objectives.');
      if(!Number.isInteger(q.gold)||!Number.isInteger(q.xp)||q.gold<0||q.xp<0||q.gold>10000||q.xp>10000)add(q,null,'Rewards must be whole numbers between 0 and 10,000.');
      const map=new Map(q.steps.map(s=>[s.id,exits(s)])),seen=new Set(),todo=[q.steps[0].id];
      if(map.size!==q.steps.length)add(q,null,'Objective identities are duplicated.');
      while(todo.length){const id=todo.pop();if(!id||seen.has(id))continue;seen.add(id);todo.push(...(map.get(id)||[]));}
      if(cyclic(map))add(q,null,'Objective connections contain a loop.');
      for(const s of q.steps){
        if(!s.name.trim())add(q,s,'Give this objective a name.');
        if(!seen.has(s.id))add(q,s,'This objective cannot be reached from the first objective.');
        if(!targets(p,s.kind).some(t=>t.id===s.target))add(q,s,'Choose an existing target of the correct type.');
        if(s.kind==='choice'&&(s.choices.length<2||s.choices.length>6))add(q,s,'A decision needs 2–6 choices.');
        if(s.kind==='choice'&&s.choices.some(c=>!c.label.trim()))add(q,s,'Give every player choice a label.');
        if(s.kind!=='choice'&&s.choices.length)add(q,s,'Only decisions can have choices.');
        for(const next of exits(s))if(next&&!map.has(next))add(q,s,'Missing next objective: '+next);
      }
    }
    if(!p.quests.length)add(null,null,'Add a mission or generate missions with AI.');
    return out;
  }
  function graph(p,questId=''){
    const errors=issues(p),q=p.quests.find(q=>q.id===questId);
    if(!q){const nodes=p.quests.map(q=>({id:q.id,quest:q.id,kind:'mission',label:q.name,badge:q.optional?'OPTIONAL MISSION':'MAIN MISSION',lines:[q.steps.length+' objectives',q.start_npc?'Starts with '+(p.npcs.find(n=>n.id===q.start_npc)?.name||q.start_npc):'Starts automatically'],invalid:errors.some(e=>e.quest===q.id)})),edges=[];
      nodes.push({id:'@ending',kind:'ending',label:'Adventure ending',badge:'ALL MAIN MISSIONS COMPLETE',lines:[p.ending||'Write the ending in Story details']});
      for(const q of p.quests){for(const dep of q.requires)if(p.quests.some(o=>o.id===dep))edges.push({from:dep,to:q.id,label:'Required first',quest:q.id});if(!q.optional)edges.push({from:q.id,to:'@ending',label:'Required for ending'});}
      return {nodes,edges};
    }
    const nodes=[{id:'@start',kind:'start',quest:q.id,label:'Mission begins',badge:'ENTRY POINT',lines:[q.start_npc?p.npcs.find(n=>n.id===q.start_npc)?.name||q.start_npc:'Starts automatically',q.requires.length?q.requires.length+' prerequisite mission(s)':'No prerequisites']},
      ...q.steps.map((s,i)=>({id:s.id,step:s.id,quest:q.id,kind:s.kind,label:s.name,badge:(i===0?'FIRST · ':'')+kinds[s.kind],lines:[targets(p,s.kind).find(t=>t.id===s.target)?.name||'Choose a target',s.description],invalid:errors.some(e=>e.quest===q.id&&e.step===s.id)})),
      {id:'@complete',kind:'complete',quest:q.id,label:'Mission complete',badge:q.optional?'SIDE MISSION COMPLETE':'MAIN MISSION COMPLETE',lines:[`${q.gold} gold · ${q.xp} XP`,q.completion]}];
    const edges=q.steps.length?[{from:'@start',to:q.steps[0].id,label:'Start here',quest:q.id}]:[];
    for(const s of q.steps){const links=s.kind==='choice'?s.choices:[{next:s.next,label:'Then'}];links.forEach((c,i)=>{const to=c.next||'@complete';if(c.next&&!nodes.some(n=>n.id===to))nodes.push({id:to,label:'Missing: '+to,kind:'missing',invalid:true});edges.push({from:s.id,to,label:c.label||'Choice '+(i+1),quest:q.id,step:s.id,choice:s.kind==='choice'?i:null});});}
    return {nodes,edges};
  }
  return {copy,kinds,targets,exits,snapshot,references,newQuest,addStep,connect,removeStep,issues,graph};
})();
