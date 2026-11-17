'use strict';
const roomMetres=r=>[r.interior?.width_m??r.width*10,r.interior?.depth_m??r.height*10];
function spatialInput(label,path,value,step=.1){return `<label class="field"><span>${E(label)}</span><input data-spatial="${path}" type="number" step="${step}" value="${E(value)}"></label>`;}
function spatialPanel(a,r){
 const p=`areas.${areaIndex}`,rp=`${p}.rooms.${roomIndex}`,g=a.geometry;
 return `<div class="card"><h3>Room boundaries and scale</h3>${g?`<p>Measured stone interior. Wall faces follow the clear dimensions below; the surrounding tile envelope does not enlarge the room.</p><div class="row">${spatialInput('Wall height · m',p+'.geometry.wall_height',g.wall_height)}${spatialInput('Wall thickness · m',p+'.geometry.wall_thickness',g.wall_thickness)}${spatialInput('Passage width · m',p+'.geometry.corridor_width',g.corridor_width)}</div>${r?`<strong>${E(r.name)}</strong><div class="row">${spatialInput('Clear width · m',rp+'.interior.width_m',roomMetres(r)[0])}${spatialInput('Clear depth · m',rp+'.interior.depth_m',roomMetres(r)[1])}</div>${openingPanel(r,rp)}${platformPanel(r,rp)}${carpetPanel(r,rp)}`:''}<p class="hint">Rebuild to export matching floors, walls, collision and minimaps. The generated geometry HAK travels with the share ZIP. Walls are rectangular stone; native cave shapes and outdoor terrain use the native tiles mode.</p><button data-action="nativeGeometry">Use native tiles instead</button>`:`<p>Native tiles and room groups keep their authored wall shapes. Their clear interiors may differ from the tile dimensions.</p>${['castle','dungeon','cave'].includes(a.type)?'<button data-action="measuredGeometry">Use measured stone walls</button>':'<p class="hint">Outdoor forests, desert and winter areas keep their native terrain.</p>'}`}</div>`;
}
function openingPanel(r,rp){return `<h4>Wall openings</h4>${(r.openings||[]).map((o,i)=>{const c=typeof project==='undefined'?null:(project?.connections||[]).find(c=>c.from_room===r.id&&c.from_side===o.side||c.to_room===r.id&&c.to_side===o.side),rid=c?(c.from_room===r.id?c.to_room:c.from_room):'',dest=c?project.areas.flatMap(a=>a.rooms).find(r=>r.id===rid):null;return `<div class="row"><strong>${E(o.side)} wall</strong>${spatialInput('Centre along wall · m',rp+'.openings.'+i+'.offset',o.offset)}${spatialInput('Clear width · m',rp+'.openings.'+i+'.width',o.width)}<button data-action="removeOpening_${i}">Remove</button></div><p class="hint">${c?`Connected to ${E(dest?.name||rid)}. Edit its door under Room and area connections.`:`<button data-action="connectOpening_${o.side}">Connect this opening to a room</button>`}</p>`;}).join('')}<div class="actions">${['north','east','south','west'].filter(side=>!(r.openings||[]).some(o=>o.side===side)).map(side=>`<button data-action="addOpening_${side}">+ ${side} opening</button>`).join('')}</div><p class="hint">Measure from the west end of north/south walls or the south end of east/west walls. Connected measured corridors have fitted wooden doors by default. Unconnected openings remain doorway recesses.</p>`;}
function doorwayFields(c,i,a){
 if(!a.geometry||c.kind!=='corridor'||![c.from_room,c.to_room].every(id=>a.rooms.some(r=>r.id===id)))return '';
 const d={style:'wood',height:2.4,leaves:'auto',...c.doorway};
 return `<h4>Doorways at both ends</h4><div class="row">${[['style','Door type',[['wood','Working wooden door'],['open','Framed opening'],['none','Open passage']]],['leaves','Door leaves',[['auto','Automatic · double from 1.8 m'],['single','Single'],['double','Double']]]].map(([key,label,opts])=>`<label class="field"><span>${label}</span><select data-doorway="${i}.${key}">${opts.map(([v,text])=>`<option value="${v}" ${d[key]===v?'selected':''}>${text}</option>`).join('')}</select></label>`).join('')}<label class="field"><span>Clear height · m</span><input data-doorway="${i}.height" type="number" min="1.8" max="4" step=".1" value="${d.height}"></label></div><p class="hint">Door width follows each wall opening. Facing openings must have equal widths. These rooms connect by walking through the passage.</p>`;
}
function platformFields(p,path,attribute='data-spatial'){
 const fields=[['x','West edge · m'],['y','South edge · m'],['width','Platform width · m'],['depth','Platform depth · m'],['height','Platform height · m'],['stair_width','Stair width · m'],['stair_run','Total stair run · m'],['steps','Number of steps'],['stair_offset','Stair centre along edge · m']];
 return `<div class="row">${fields.map(([key,label])=>`<label class="field"><span>${label}</span><input ${attribute}="${path}.${key}" type="number" step="${key==='steps'?1:.05}" value="${E(p[key])}"></label>`).join('')}<label class="field"><span>Stairs approach from</span><select ${attribute}="${path}.stair_side">${['south','north','east','west'].map(side=>`<option ${p.stair_side===side?'selected':''}>${side}</option>`).join('')}</select></label></div><p class="hint">${(p.height/p.steps).toFixed(2)} m rise · ${(p.stair_run/p.steps).toFixed(2)} m tread. Stair run extends outside the platform footprint. X/Y start at the room’s southwest corner.</p>`;
}
function platformPanel(r,rp){return `<h4>Raised platforms and stairs</h4>${(r.platforms||[]).map((p,i)=>`<div class="connection-card"><strong>${E(p.name)}</strong>${platformFields(p,rp+'.platforms.'+i)}<button data-action="removePlatform_${i}">Remove platform and stairs</button></div>`).join('')}<button data-action="addPlatform">Add raised platform with stairs</button><p class="hint">Furniture follows the platform height automatically. Keep steps clear and leave a flat landing below them. Rebuild to update the area in Aurora.</p>`;}
const carpetColors={red:'#8e161e',blue:'#1e3871',green:'#235636',purple:'#532363',brown:'#5e3c25',cream:'#c3b289',gold:'#b48b37'};
function carpetFields(c,path,attribute='data-spatial'){
 return `<div class="row">${[['x','West edge · m'],['y','South edge · m'],['width','Width east–west · m'],['depth','Length north–south · m']].map(([key,label])=>`<label class="field"><span>${label}</span><input ${attribute}="${path}.${key}" type="number" step=".1" value="${E(c[key])}"></label>`).join('')}${[['color','Color',Object.keys(carpetColors)],['border','Border',['none','gold','cream']]].map(([key,label,values])=>`<label class="field"><span>${label}</span><select ${attribute}="${path}.${key}">${values.map(v=>`<option value="${v}" ${c[key]===v?'selected':''}>${v}</option>`).join('')}</select></label>`).join('')}</div><p class="hint">One continuous ${E(c.width)} × ${E(c.depth)} m carpet. X/Y start at the room’s southwest corner. It rests on the floor or a flat platform and stops before stairs.</p>`;
}
function carpetPanel(r,rp){return `<h4>Carpets and runners</h4>${(r.carpets||[]).map((c,i)=>`<div class="connection-card"><strong>${E(c.name)}</strong>${carpetFields(c,rp+'.carpets.'+i)}<button data-action="removeCarpet_${i}">Remove carpet</button></div>`).join('')}<button data-action="addCarpet">Add measured carpet</button><p class="hint">Carpets use the dimensions and color above without blocking walking. Rebuild to update the generated area.</p>`;}
function carpetOutlines(a,r){return (r.carpets||[]).map(c=>`<rect x="${r.x+c.x/10}" y="${a.height-r.y-(c.y+c.depth)/10}" width="${c.width/10}" height="${c.depth/10}" fill="${carpetColors[c.color]||carpetColors.red}" stroke="${c.border==='none'?'none':carpetColors[c.border]}" stroke-width=".016" pointer-events="none"><title>${E(c.name)} · ${E(c.width)} × ${E(c.depth)} m · ${E(c.color)}</title></rect>`).join('');}
function supportedChildren(parent,before,after){
 const positions=project.object_positions||[],seen=new Set([parent]);
 function move(id,old,next){for(const child of positions.filter(p=>p.support===id)){
  if(seen.has(child.id))continue;seen.add(child.id);const initial=clone(child),angle=(next.facing-old.facing)*Math.PI/180,dx=child.x-old.x,dy=child.y-old.y;
  child.x=Number((next.x+dx*Math.cos(angle)-dy*Math.sin(angle)).toFixed(3));child.y=Number((next.y+dx*Math.sin(angle)+dy*Math.cos(angle)).toFixed(3));child.facing=(child.facing+next.facing-old.facing+720)%360;move(child.id,initial,child);
 }}move(parent,before,after);
}
function placementPanel(a){
 const rooms=new Set(a.rooms.map(r=>r.id)),objects=[...project.furnishings,...(project.custom_placements||[])],positions=project.object_positions||[];
 return `<div class="card"><h3>Precise object placement</h3><p class="hint">X/Y are metres from the room’s southwest corner. Rotation turns the model’s own axes: 0° keeps its original shape, 90° turns it counterclockwise. The cyan outlines show measured model footprints. The arrow is the model’s +X axis, not necessarily its front.</p>${positions.map((pos,i)=>{
 const f=objects.find(f=>f.id===pos.id);if(!f||!rooms.has(f.room))return '';const p='object_positions.'+i;pos.z??=0;pos.support??='';
 const supports=positions.filter(v=>v.id!==pos.id&&objects.find(o=>o.id===v.id)?.room===f.room&&project.asset_geometry?.[objects.find(o=>o.id===v.id)?.asset_id]);
 return `<div class="connection-card"><strong>${E(f.name)}</strong><div class="row">${spatialInput('X · m',p+'.x',pos.x)}${spatialInput('Y · m',p+'.y',pos.y)}${spatialInput('Rotation · °',p+'.facing',pos.facing,1)}</div><div class="row">${spatialInput(pos.support?'Height above support · m':'Height above floor · m',p+'.z',pos.z)}<label class="field"><span>Rest on</span><select data-support="${i}"><option value="">Floor / manual elevation</option>${supports.map(v=>`<option value="${E(v.id)}" ${pos.support===v.id?'selected':''}>${E(objects.find(o=>o.id===v.id).name)} · ${E(v.id)}</option>`).join('')}</select></label></div><button data-rotate="${i}">Rotate 90°</button></div>`;
 }).join('')||'<p>Generate from a reviewed checklist to create explicit object positions.</p>'}<p class="hint">Supported items use the measured top of their parent model. Moving or rotating that parent here moves its supported items too. Irregular surfaces may need a small height adjustment in Aurora.</p><button data-action="checkPositions">Check placement edits</button></div>`;
}
function bindSpatial(){
 function unlocked(rid){if((project.locked_rooms||[]).includes(rid))throw Error('Unlock this room before changing its layout or contents.');}
 async function update(fn){const before=clone(project);try{fn();previousDraft=before;change();report=await api('/api/author/review',{project});render();if(report.errors.length)notify(report.errors.join('\n'),true);}catch(e){project=before;render();throw e;}}
 document.querySelectorAll('[data-doorway]').forEach(el=>el.onchange=()=>task(el,()=>update(()=>{const [index,key]=el.dataset.doorway.split('.'),c=project.connections[Number(index)];unlocked(c.from_room);unlocked(c.to_room);c.doorway??={style:'wood',height:2.4,leaves:'auto'};c.doorway[key]=key==='height'?Number(el.value):el.value;})));
 document.querySelectorAll('[data-spatial]').forEach(el=>el.onchange=()=>task(el,()=>update(()=>{
  const path=el.dataset.spatial,parts=path.split('.'),n=el.tagName==='SELECT'?el.value:Number(el.value);if(!el.value.trim()||(el.tagName!=='SELECT'&&!Number.isFinite(n)))throw Error('Enter a finite number.');
  if(parts[0]==='object_positions'){const pos=project.object_positions[Number(parts[1])],f=[...project.furnishings,...(project.custom_placements||[])].find(f=>f.id===pos.id);unlocked(f.room);const old=clone(pos);set(path,n);supportedChildren(pos.id,old,pos);}
  else {const a=project.areas[Number(parts[1])];a.rooms.forEach(r=>unlocked(r.id));set(path,n);for(const r of a.rooms){const [w,h]=roomMetres(r);r.width=Math.ceil(w/10);r.height=Math.ceil(h/10);}}
 })));
 document.querySelectorAll('[data-support]').forEach(el=>el.onchange=()=>task(el,()=>update(()=>{const pos=project.object_positions[Number(el.dataset.support)],f=[...project.furnishings,...(project.custom_placements||[])].find(f=>f.id===pos.id);unlocked(f.room);pos.support=el.value;pos.z=0;})));
 document.querySelectorAll('[data-rotate]').forEach(el=>el.onclick=()=>task(el,()=>update(()=>{const pos=project.object_positions[Number(el.dataset.rotate)],f=[...project.furnishings,...(project.custom_placements||[])].find(f=>f.id===pos.id);unlocked(f.room);const before=clone(pos);pos.facing=(pos.facing+90)%360;supportedChildren(pos.id,before,pos);})));
}
async function spatialAction(name){
 if(name.startsWith('connectOpening_')){
  const r=selectedRoom(),a=area(),side=name.split('_')[1],o=r.openings.find(o=>o.side===side),others=a.rooms.filter(x=>x.id!==r.id),opposite={north:'south',south:'north',east:'west',west:'east'};
  if((project.locked_rooms||[]).includes(r.id))throw Error('Unlock this room first.');if(!others.length)throw Error('Add the destination room to this area first, then connect this opening.');
  modal(`<h2>Connect the ${E(side)} opening</h2><label class="field"><span>Destination room</span><select id="openingRoom">${others.map(x=>`<option value="${E(x.id)}">${E(x.name)}</option>`).join('')}</select></label><label class="field"><span>Destination wall</span><select id="openingSide">${['north','east','south','west'].map(s=>`<option ${s===opposite[side]?'selected':''}>${s}</option>`).join('')}</select></label><p>Creates a physical passage with a working door at each end. A new destination opening uses the same width and aligns with this opening where possible.</p><button id="connectOpeningNow" class="primary">Connect rooms</button>`);
  $('#connectOpeningNow').onclick=e=>task(e.target,async()=>{
   const a=area(),r=selectedRoom(),before=clone(project),dest=a.rooms.find(x=>x.id===$('#openingRoom').value),targetSide=$('#openingSide').value;
   if((project.locked_rooms||[]).includes(dest.id))throw Error('Unlock the destination room first.');
   const used=(rid,s)=>project.connections.some(c=>c.from_room===rid&&c.from_side===s||c.to_room===rid&&c.to_side===s);
   if(used(r.id,side)||used(dest.id,targetSide))throw Error('One of these walls is already connected. Choose an unused wall.');
   try{
    dest.openings??=[];if(!dest.openings.some(x=>x.side===targetSide)){const alongX=['north','south'].includes(targetSide),length=roomMetres(dest)[alongX?0:1],aligned=['north','south'].includes(side)===alongX,offset=aligned?(alongX?r.x-dest.x:r.y-dest.y)*10+o.offset:length/2;dest.openings.push({side:targetSide,width:o.width,offset:Math.min(length-o.width/2-.1,Math.max(o.width/2+.1,offset))});}
    let n=1;while(project.connections.some(c=>c.id==='passage_'+n))n++;
    project.connections.push({id:'passage_'+n,name:r.name+' to '+dest.name,from_room:r.id,from_side:side,to_room:dest.id,to_side:targetSide,kind:'corridor',two_way:true,requires_quest:''});
    previousDraft=before;change();report=await api('/api/author/review',{project});$('#modal').close();render();notify(report.errors.length?'Connection added to draft. '+report.errors.join('\n'):'Rooms connected. Update generated area to build the passage and doors.',!!report.errors.length);
   }catch(error){project=before;throw error;}
  });return true;
 }
 if(name==='addCarpet'||name.startsWith('removeCarpet_')){
  const r=selectedRoom();if(!r||!area().geometry)throw Error('Choose a room with measured walls.');if((project.locked_rooms||[]).includes(r.id))throw Error('Unlock this room first.');const before=clone(project);previousDraft=before;r.carpets??=[];
  if(name==='addCarpet'){const [w,h]=roomMetres(r);let n=1;while(r.carpets.some(c=>c.id==='carpet_'+n))n++;const width=Math.min(2,w-.4),depth=Math.min(4,h-.4);r.carpets.push({id:'carpet_'+n,name:'Carpet '+n,x:(w-width)/2,y:.2,width,depth,color:'red',border:'none',requirements:[]});}
  else r.carpets.splice(Number(name.split('_')[1]),1);
  try{change();report=await api('/api/author/review',{project});render();if(report.errors.length)notify(report.errors.join('\n'),true);}catch(e){project=before;render();throw e;}return true;
 }
 if(name==='addPlatform'||name.startsWith('removePlatform_')){
  const r=selectedRoom();if(!r||!area().geometry)throw Error('Choose a room with measured walls.');if((project.locked_rooms||[]).includes(r.id))throw Error('Unlock this room first.');previousDraft=clone(project);r.platforms??=[];
  if(name==='addPlatform'){const [w,h]=roomMetres(r);if(w<3||h<5)throw Error('This room needs more space for a platform and a stair landing.');let n=1;while(r.platforms.some(p=>p.id==='platform_'+n))n++;const width=Math.min(4,w-1),depth=Math.min(3,h-3);r.platforms.push({id:'platform_'+n,name:'Raised platform '+n,x:(w-width)/2,y:h-depth,width,depth,height:.45,stair_side:'south',stair_width:Math.min(2,width),stair_run:.9,steps:3,stair_offset:width/2,requirements:[]});}
  else r.platforms.splice(Number(name.split('_')[1]),1);
  change();report=await api('/api/author/review',{project});render();if(report.errors.length)notify(report.errors.join('\n'),true);return true;
 }
 if(name.startsWith('addOpening_')||name.startsWith('removeOpening_')){
  const r=selectedRoom();if(!r||!area().geometry)throw Error('Choose a room with measured walls.');if((project.locked_rooms||[]).includes(r.id))throw Error('Unlock this room first.');previousDraft=clone(project);r.openings??=[];
  if(name.startsWith('remove'))r.openings.splice(Number(name.split('_')[1]),1);
  else {const side=name.split('_')[1],length=roomMetres(r)[['north','south'].includes(side)?0:1];if(r.openings.some(o=>o.side===side))return true;r.openings.push({side,offset:length/2,width:Math.min(2,length-.2)});}
  change();report=await api('/api/author/review',{project});render();return true;
 }
 if(!['measuredGeometry','nativeGeometry'].includes(name))return false;
 const a=area();if(a.rooms.some(r=>(project.locked_rooms||[]).includes(r.id)))throw Error('Unlock the area’s rooms before changing wall geometry.');
 if(name==='measuredGeometry'&&a.rooms.some(r=>r.native_group))throw Error('Remove native room groups before enabling measured walls.');
 previousDraft=clone(project);
 if(name==='nativeGeometry'){delete a.geometry;a.rooms.forEach(r=>{delete r.interior;delete r.openings;delete r.platforms;delete r.carpets;});for(const c of project.connections)if(a.rooms.some(r=>r.id===c.from_room||r.id===c.to_room))delete c.doorway;}
 else {a.geometry={mode:'measured',wall_height:5,wall_thickness:.3,corridor_width:2};for(const r of a.rooms){const m=a.design_plan?.measurements?.find(m=>m.room===r.id);r.interior={width_m:m?.width_m??r.width*10,depth_m:m?.height_m??r.height*10};r.width=Math.ceil(r.interior.width_m/10);r.height=Math.ceil(r.interior.depth_m/10);}}
 change();report=await api('/api/author/review',{project});render();notify('Geometry mode changed. Update generated area to rebuild.');return true;
}
function measuredOutlines(a){return a.geometry?a.rooms.map(r=>{const [w,h]=roomMetres(r);return platformOutlines(a,r)+carpetOutlines(a,r)+`<rect x="${r.x}" y="${a.height-r.y-h/10}" width="${w/10}" height="${h/10}" fill="none" stroke="#ffe679" stroke-width="${a.geometry.wall_thickness/10}" pointer-events="none"><title>${E(r.name)} · clear ${w} × ${h} m</title></rect>`;}).join(''):'';}

function platformOutlines(a,r){
 const rect=(x,y,w,h,title,fill)=>`<rect x="${r.x+x/10}" y="${a.height-r.y-(y+h)/10}" width="${w/10}" height="${h/10}" fill="${fill}" stroke="#ffd458" stroke-width=".012" pointer-events="none"><title>${E(title)}</title></rect>`;
 return (r.platforms||[]).map(p=>{let out=rect(p.x,p.y,p.width,p.depth,`${p.name} · ${p.height} m high`,'#b69c6338');const tread=p.stair_run/p.steps;
 for(let i=0;i<p.steps;i++){const z=p.height*(i+1)/p.steps;let x,y,w,h;if(['north','south'].includes(p.stair_side)){x=p.x+p.stair_offset-p.stair_width/2;y=p.stair_side==='south'?p.y-p.stair_run+i*tread:p.y+p.depth+p.stair_run-(i+1)*tread;w=p.stair_width;h=tread;}else{x=p.stair_side==='west'?p.x-p.stair_run+i*tread:p.x+p.width+p.stair_run-(i+1)*tread;y=p.y+p.stair_offset-p.stair_width/2;w=tread;h=p.stair_width;}out+=rect(x,y,w,h,`Step ${i+1} · ${z.toFixed(2)} m`,'#f9cb7040');}return out;}).join('');
}
