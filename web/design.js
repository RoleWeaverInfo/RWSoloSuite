'use strict';
let mapMode='move',mapOverlay=0,overlayIndex=0,pendingDoor=null,designBusy=false;
let inspectedFixture=null;
function fixtureRecord(data,id){
 const fixture=[...(data.furnishings||[]),...(data.custom_placements||[])].find(f=>f.id===id),position=(data.object_positions||[]).find(p=>p.id===id);
 const room=fixture&&data.areas.flatMap(a=>a.rooms).find(r=>r.id===fixture.room);
 return fixture&&position&&room?{fixture,position,room}:null;
}
function refreshMapFixtures(){
 const layer=$('.worldmap .map-fixtures');if(layer)layer.innerHTML=objectMarkers(area());
}
function fixtureInfoHtml(id){
 const record=fixtureRecord(project,id);if(!record)return '<p>This fixture is no longer in the area.</p>';
 const {fixture:f,position:p,room:r}=record,locked=(project.locked_rooms||[]).includes(r.id),asset=(project.custom_assets||[]).find(a=>a.id===f.asset_id);
 const support=p.support?fixtureRecord(project,p.support)?.fixture.name||p.support:'Floor / platform';
 return `<div class="fixture-info"><h2 id="fixtureTitle">${E(f.name)}</h2>${f.description?`<p>${E(f.description)}</p>`:''}<dl><dt>Room</dt><dd>${E(r.name)}</dd><dt>Fixture</dt><dd>${E(asset?.name||f.kind||'Custom fixture')}</dd><dt>Position in room</dt><dd>${p.x.toFixed(2)} m east · ${p.y.toFixed(2)} m north</dd><dt>Support</dt><dd>${E(support)}</dd><dt>Height above ${p.support?'support':'floor / platform'}</dt><dd>${(p.z||0).toFixed(2)} m</dd><dt>Rotation</dt><dd><output id="fixtureFacing">${p.facing}°</output></dd></dl><p class="hint">Position starts at the room’s southwest corner. The red marker shows the model’s rotation axis; a model’s visible front can differ.</p>${locked?'<p class="notice">This room is locked. Unlock it to move or rotate fixtures.</p>':''}<fieldset id="fixtureRotationControls" class="fixture-rotation" ${locked?'disabled':''}><legend>Rotate fixture</legend><label>Step <select id="fixtureRotationStep"><option value="15">15°</option><option value="45" selected>45°</option><option value="90">90°</option></select></label><div class="actions"><button type="button" data-fixture-turn="1">↺ Rotate left</button><button type="button" data-fixture-turn="-1">Rotate right ↻</button></div></fieldset><p id="fixtureStatus" role="status"></p><p class="hint">Use Update generated area when ready to rebuild the area with your changes.</p></div>`;
}
async function rotateMapFixture(id,degrees){
 if(designBusy||generating)throw Error('Wait for the current design operation to finish.');
 const source=project,before=clone(source),draft=clone(source),record=fixtureRecord(draft,id);
 if(!record)throw Error('This fixture is no longer in the area.');
 if((draft.locked_rooms||[]).includes(record.room.id))throw Error('Unlock this room before rotating its fixtures.');
 if(!Number.isFinite(degrees))throw Error('Choose a valid rotation step.');
 const old=clone(record.position);record.position.facing=Number(((old.facing+degrees)%360+360).toFixed(3))%360;
 supportedChildren(id,old,record.position,draft.object_positions);
 const review=await api('/api/author/review',{project:draft});
 // Reviewing is asynchronous; never overwrite edits made after this rotation began.
 if(project!==source||JSON.stringify(project)!==JSON.stringify(before))throw Error('The draft changed during the placement check. Please retry the rotation.');
 previousDraft=before;project=draft;change();report=review;refreshMapFixtures();
 document.querySelectorAll('[data-spatial^="object_positions."]').forEach(el=>{el.value=value(el.dataset.spatial);});
 const undo=document.querySelector('[data-action="undoDesign"]');if(undo)undo.disabled=false;
 return review;
}
function showFixtureInfo(id){
 if(!fixtureRecord(project,id))return;
 inspectedFixture={project:project.id,id};refreshMapFixtures();modal(fixtureInfoHtml(id));
 const dialog=$('#modal'),content=$('#modalContent');
 dialog.addEventListener('close',()=>{inspectedFixture=null;refreshMapFixtures();$('.worldmap')?.focus({preventScroll:true});},{once:true});
 function bindRotation(){document.querySelectorAll('[data-fixture-turn]').forEach(button=>button.onclick=async()=>{
  const step=$('#fixtureRotationStep').value,controls=$('#fixtureRotationControls'),status=$('#fixtureStatus');controls.disabled=true;status.textContent='Checking placement…';
  try{
   const result=await rotateMapFixture(id,Number(button.dataset.fixtureTurn)*Number(step));
   if(dialog.open&&content.contains(controls)){
    content.innerHTML=fixtureInfoHtml(id);$('#fixtureRotationStep').value=step;bindRotation();
    $('#fixtureStatus').textContent=result.errors.length?'Rotation applied. Check placement: '+result.errors.join(' '):'Rotation applied to the draft.';
    document.querySelector(`[data-fixture-turn="${button.dataset.fixtureTurn}"]`).focus();
   }
  }catch(error){if(content.contains(controls))status.textContent=error.message;}
  finally{if(content.contains(controls))controls.disabled=(project.locked_rooms||[]).includes(fixtureRecord(project,id)?.room.id);}
 });}
 bindRotation();
}
// Camera positions belong to this tab, never to the module's saved geometry.
const mapViews=new Map(),mapZoomMin=.5,mapZoomMax=16;
function mapView(a){
 const key=JSON.stringify([project.id,a.id]);let view=mapViews.get(key);
 if(!view||view.width!==a.width||view.height!==a.height){view={x:0,y:0,zoom:1,width:a.width,height:a.height};mapViews.set(key,view);}
 return view;
}
function constrainMapView(view){
 view.zoom=Math.max(mapZoomMin,Math.min(mapZoomMax,view.zoom));
 for(const [axis,size] of [['x','width'],['y','height']]){
  const span=view[size]/view.zoom,margin=span*.25,low=-margin,high=view[size]-span+margin;
  view[axis]=low>high?(view[size]-span)/2:Math.max(low,Math.min(high,view[axis]));
 }
 return view;
}
function mapViewBox(a){const v=mapView(a);return `${v.x} ${v.y} ${a.width/v.zoom} ${a.height/v.zoom}`;}
function zoomMapView(a,factor,anchor){
 const v=mapView(a),oldZoom=v.zoom,next=Math.max(mapZoomMin,Math.min(mapZoomMax,oldZoom*factor));
 anchor=anchor||{x:v.x+a.width/oldZoom/2,y:v.y+a.height/oldZoom/2};
 v.x=anchor.x-(anchor.x-v.x)*oldZoom/next;v.y=anchor.y-(anchor.y-v.y)*oldZoom/next;v.zoom=next;
 constrainMapView(v);
}
function fitMapView(a,room){
 const v=mapView(a);
 if(!room){v.x=0;v.y=0;v.zoom=1;return;}
 v.zoom=Math.min(mapZoomMax,Math.max(mapZoomMin,Math.min(a.width/(room.width+1),a.height/(room.height+1))));
 v.x=room.x+room.width/2-a.width/v.zoom/2;
 v.y=a.height-room.y-room.height/2-a.height/v.zoom/2;constrainMapView(v);
}
function mapViewport(a){return `<div class="map-wrap"><div class="map-toolbar" role="group" aria-label="Map view controls"><button type="button" data-map-view="out" aria-label="Zoom out" title="Zoom out">−</button><output id="mapZoom" aria-live="polite" aria-label="Map zoom">${Math.round(mapView(a).zoom*100)}%</output><button type="button" data-map-view="in" aria-label="Zoom in" title="Zoom in">＋</button><button type="button" data-map-view="fit">Fit area</button><button type="button" data-map-view="room" ${selectedRoom()?'':'disabled'}>Focus room</button><button type="button" data-map-view="pan" aria-pressed="${mapMode==='pan'}">Pan view</button></div>${worldMap(a)}<p id="mapViewHint" class="hint">Click a blue fixture for details and rotation; drag it to move. Scroll over the map to zoom. Drag with Pan view or the middle mouse button to look around. With the map focused, use arrow keys to pan, + / − to zoom, and 0 to fit the area. North is up; each square is a 10 m tile. Gold dots mark exits.</p></div>`;}
function mapPoint(svg,event,matrix=svg.getScreenCTM().inverse()){
 const point=svg.createSVGPoint();point.x=event.clientX;point.y=event.clientY;return point.matrixTransform(matrix);
}
function bindMapViewport(svg){
 const a=area(),drag={active:false};
 const update=()=>{
  svg.setAttribute('viewBox',mapViewBox(a));svg.classList.toggle('pan-mode',mapMode==='pan');
  $('#mapZoom').textContent=Math.round(mapView(a).zoom*100)+'%';
  document.querySelector('[data-map-view="out"]').disabled=mapView(a).zoom<=mapZoomMin;
  document.querySelector('[data-map-view="in"]').disabled=mapView(a).zoom>=mapZoomMax;
  document.querySelector('[data-map-view="pan"]').setAttribute('aria-pressed',String(mapMode==='pan'));
 };
 const blocked=()=>designBusy||generating||drag.active;
 drag.setMode=mode=>{
  if(blocked())return;
  mapMode=mode;pendingDoor=null;$('#mapMode').value=mode;
  svg.querySelector('.map-tools').innerHTML=mapExtras(a);update();
 };
 drag.begin=(event,move,end,cancel=()=>{})=>{
  const id=event.pointerId;drag.active=true;svg.setPointerCapture(id);
  const finish=(e,aborted)=>{
   if(e.pointerId!==id)return;
   svg.onpointermove=svg.onpointerup=svg.onpointercancel=svg.onlostpointercapture=null;
   drag.active=false;svg.classList.remove('panning');
   if(svg.hasPointerCapture(id))svg.releasePointerCapture(id);
   (aborted?cancel:end)();
  };
  svg.onpointermove=e=>{if(e.pointerId===id)move(e);};
  svg.onpointerup=e=>finish(e,false);svg.onpointercancel=e=>finish(e,true);svg.onlostpointercapture=e=>finish(e,true);
 };
 drag.pan=event=>{
  if(event.button!==1&&!(event.button===0&&mapMode==='pan'))return false;
  event.preventDefault();svg.focus({preventScroll:true});
  // Freeze the inverse matrix: changing the viewBox during a drag changes its CTM.
  const matrix=svg.getScreenCTM().inverse(),start=mapPoint(svg,event,matrix),before={...mapView(a)};
  let moved=false;
  svg.classList.add('panning');
  drag.begin(event,e=>{
   if(!moved&&Math.hypot(e.clientX-event.clientX,e.clientY-event.clientY)<4)return;
   moved=true;const p=mapPoint(svg,e,matrix),v=mapView(a);v.x=before.x+start.x-p.x;v.y=before.y+start.y-p.y;constrainMapView(v);update();
  },()=>{const fixture=event.target.closest('[data-object-position]');if(!moved&&event.button===0&&fixture)showFixtureInfo(fixture.dataset.objectPosition);});
  return true;
 };
 document.querySelectorAll('[data-map-view]').forEach(button=>button.onclick=()=>{
  if(blocked())return;
  const action=button.dataset.mapView;
  if(action==='in'||action==='out')zoomMapView(a,action==='in'?1.25:1/1.25);
  else if(action==='fit'||action==='room')fitMapView(a,action==='room'?selectedRoom():null);
  else if(action==='pan'){drag.setMode(mapMode==='pan'?'move':'pan');return;}
  update();
 });
 svg.addEventListener('wheel',e=>{
  e.preventDefault();if(blocked())return;
  const delta=e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?svg.clientHeight:1);
  zoomMapView(a,Math.exp(-Math.max(-200,Math.min(200,delta))*.002),mapPoint(svg,e));update();
 },{passive:false});
 svg.onkeydown=e=>{
  if(e.ctrlKey||e.metaKey||e.altKey||blocked())return;
  const fixture=e.target?.closest('[data-object-position]');
  if(fixture&&(e.key==='Enter'||e.key===' ')){e.preventDefault();showFixtureInfo(fixture.dataset.objectPosition);return;}
  const v=mapView(a),steps={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]};
  if(steps[e.key]){v.x+=steps[e.key][0]*a.width/v.zoom*.1;v.y+=steps[e.key][1]*a.height/v.zoom*.1;constrainMapView(v);}
  else if(['+','=','-','_'].includes(e.key))zoomMapView(a,e.key==='+'||e.key==='='?1.25:1/1.25);
  else if(e.key==='0')fitMapView(a);else return;
  e.preventDefault();update();
 };
 svg.onauxclick=e=>{if(e.button===1)e.preventDefault();};update();return drag;
}
function workshopPanel(){if(project.design_mode!=='area')return '';const targets=app.projects.filter(p=>p.schema_version===2&&p.design_mode!=='area'&&p.id!==project.id);return `<div class="card accent"><h2>Standalone area workspace</h2><p>Build and furnish rooms here without a storyline. They stay separate until you choose an adventure below.</p>${field('Workspace name','title')}<div class="actions"><select id="attachAdventure" aria-label="Destination adventure">${targets.length?targets.map(p=>`<option value="${E(p.id)}">${E(p.title)}</option>`).join(''):'<option value="">No adventures yet</option>'}</select><button data-action="attachArea" ${targets.length?'':'disabled'}>Add area to adventure</button><button data-action="createAdventure">Create an adventure</button></div><p class="hint">Adding copies the selected area and its contents. Your workspace stays editable; adventure connections and story links can be added later.</p><div id="attachStatus" role="status"></div></div>`;}
function mapBackground(a){const ref=a.references?.[overlayIndex];return ref&&mapOverlay?`<image href="${E(ref.data_url)}" x="0" y="0" width="${a.width}" height="${a.height}" preserveAspectRatio="xMidYMid meet" opacity="${mapOverlay}" pointer-events="none"/>`:'';}
function mapExtras(a){return a.rooms.map((r,i)=>{const locked=(project.locked_rooms||[]).includes(r.id);let out=locked?`<text x="${r.x+.2}" y="${a.height-r.y-r.height+.5}" fill="#ffe679" font-size=".4" pointer-events="none">LOCKED</text>`:'';
 if(mapMode==='resize')out+=`<rect data-resize-room="${i}" x="${r.x+r.width-.25}" y="${a.height-r.y-r.height-.25}" width=".5" height=".5" fill="#ffe679" class="resize-handle"><title>Drag to resize ${E(r.name)}</title></rect>`;
 if(mapMode==='door')for(const [s,x,y] of [['north',r.x+roomMetres(r)[0]/20,r.y+roomMetres(r)[1]/10],['south',r.x+roomMetres(r)[0]/20,r.y],['west',r.x,r.y+roomMetres(r)[1]/20],['east',r.x+roomMetres(r)[0]/10,r.y+roomMetres(r)[1]/20]])out+=`<circle data-door-room="${i}" data-door-side="${s}" cx="${x}" cy="${a.height-y}" r=".25" fill="${pendingDoor?.room===r.id&&pendingDoor.side===s?'#fff':'#ffd75b'}"><title>${E(r.name)} · ${s} wall</title></circle>`;
 return out;}).join('');}
function designPanel(a){const r=selectedRoom();return `<div class="card"><h3>Visual area editor</h3><div class="actions"><label>Map tool <select id="mapMode">${[['move','Move rooms'],['resize','Resize rooms'],['door','Connect wall doors'],['pan','Pan view']].map(([v,n])=>`<option value="${v}" ${mapMode===v?'selected':''}>${n}</option>`).join('')}</select></label><button data-action="undoDesign" ${previousDraft?'':'disabled'}>Undo last design change</button></div><p class="hint">Drag a room to move it, or its yellow corner to resize. In door mode, click one wall dot and then a wall dot on another room. Changes snap to tiles; blocked corridor layouts are rejected. Click Update generated area to save your edits and rebuild the native area preview, then open the updated copy in Aurora.</p>${a.references?.length?`<label>Floor-plan overlay <select id="overlayImage">${a.references.map((ref,i)=>`<option value="${i}" ${i===overlayIndex?'selected':''}>${E(ref.name)}</option>`).join('')}</select></label><label>Overlay opacity <input id="overlayOpacity" type="range" min="0" max="0.8" step="0.05" value="${mapOverlay}"></label><p class="hint">The image is fitted to the map as a visual guide; it is not a calibrated tracing.</p>`:''}${mapViewport(a)}${r?`<hr><h3>Selected room: ${E(r.name)}</h3><p>${r.native_group?'Native group: '+E(r.native_group.definition.name):'Free room geometry'}</p><button data-action="chooseNativeGroup">Choose native room / terrain group</button><label class="check"><input id="roomLock" type="checkbox" ${(project.locked_rooms||[]).includes(r.id)?'checked':''}>Lock room layout, connections and contents against AI changes</label><label class="field"><span>Change only this room’s contents</span><textarea id="roomDirection" placeholder="Reduce furniture, keep a clear walkway, and add a suspicious guard."></textarea></label><button data-action="regenerateRoom">Preview room regeneration</button><p class="hint">Room regeneration preserves geometry, other rooms and quest definitions. Review any quest-target warnings before applying.</p><h3>Encounter template</h3><div class="row"><label>Type<select id="encounterKind">${[['combat','Guarded chamber'],['ambush','Ambush'],['puzzle','Clue and levers'],['treasure','Supply cache'],['story','Discovery / message']].map(([v,n])=>`<option value="${v}">${n}</option>`).join('')}</select></label><label>Enemy count<select id="encounterDifficulty"><option value="easy">Light · 1</option><option value="standard" selected>Standard · 2</option><option value="hard">Heavy · 3</option></select></label></div><label class="field"><span>Encounter design brief</span><textarea id="encounterBrief" placeholder="Describe what should happen here. The template supplies editable starting mechanics."></textarea></label><button data-action="encounterTemplate">Preview encounter template</button><p class="hint">Templates need no API. Combat defaults to goblins with bounded party scaling; edit creatures, puzzle answers and rewards in Encounters & items. Use room regeneration to turn your brief into AI-designed content.</p>`:''}<p class="hint">Area testing builds a separate offline module, disables quest gates and ambient behavior, and installs it for testing. Open NWN separately, select this module and choose a suitable test character; this does not generate a test party.</p></div>${spatialPanel(a,r)}`;}
async function designOperation(fn){if(designBusy||generating)throw Error('Wait for the current operation to finish.');designBusy=true;const controls=['#projectSelect','#newProject','#importProject','#saveProject','#deleteProject'].map(s=>$(s));controls.forEach(el=>el.disabled=true);$('#workspace').style.pointerEvents='none';$('#busy').hidden=false;try{return await fn();}finally{designBusy=false;controls.forEach(el=>el.disabled=false);$('#workspace').style.pointerEvents='';$('#busy').hidden=true;}}
async function commitMap(room_id,operation,values){return designOperation(async()=>{const before=clone(project);const result=await api('/api/design/map',{project,room_id,operation,values});previousDraft=before;project=result.project;change();report=result.review;render();notify('Map updated and corridor routes checked.');});}
function bindDesign(){
 bindSpatial();
 if($('#overlayImage'))$('#overlayImage').onchange=e=>{overlayIndex=Number(e.target.value);render();};
 if($('#overlayOpacity'))$('#overlayOpacity').onchange=e=>{mapOverlay=Number(e.target.value);render();};
 if($('#roomLock'))$('#roomLock').onchange=e=>{previousDraft=clone(project);project.locked_rooms=(project.locked_rooms||[]).filter(id=>id!==selectedRoom().id);if(e.target.checked)project.locked_rooms.push(selectedRoom().id);change();render();};
 const svg=$('.worldmap');if(!svg)return;
 const navigation=bindMapViewport(svg),point=e=>mapPoint(svg,e);
 if($('#mapMode'))$('#mapMode').onchange=e=>navigation.setMode(e.target.value);
 svg.onpointerdown=e=>{
  if(designBusy||generating||navigation.active||e.isPrimary===false)return;
  if(navigation.pan(e))return;
  if(e.button!==0)return;
  svg.focus({preventScroll:true});
  const object=e.target.closest('[data-object-position]');
  if(object){
   const pos=project.object_positions.find(p=>p.id===object.dataset.objectPosition),f=[...project.furnishings,...(project.custom_placements||[])].find(f=>f.id===pos.id);
   if((project.locked_rooms||[]).includes(f.room)){showFixtureInfo(pos.id);return;}
   const start=point(e),original=clone(pos),before=clone(project);
   let moved=false;
   navigation.begin(e,event=>{
    if(!moved&&Math.hypot(event.clientX-e.clientX,event.clientY-e.clientY)<4)return;
    moved=true;
    const end=point(event);pos.x=Math.round((original.x+(end.x-start.x)*10)*10)/10;pos.y=Math.round((original.y-(end.y-start.y)*10)*10)/10;
    object.parentElement.setAttribute('transform',`translate(${(pos.x-original.x)/10} ${-(pos.y-original.y)/10})`);
   },()=>{
    if(!moved){showFixtureInfo(pos.id);return;}
    supportedChildren(pos.id,original,pos);previousDraft=before;change();
    task(null,async()=>{report=await api('/api/author/review',{project});render();if(report.errors.length)notify(report.errors.join('\n'),true);});
   },()=>{project=before;render();});return;
  }
  const door=e.target.closest('[data-door-room]');
  if(door){
   const r=area().rooms[Number(door.dataset.doorRoom)],side=door.dataset.doorSide;
   if(!pendingDoor){pendingDoor={room:r.id,side};notify('Now select the destination wall.');render();}
   else{const start=pendingDoor;pendingDoor=null;task(null,()=>commitMap(start.room,'connect',{to_room:r.id,from_side:start.side,to_side:side}));}return;
  }
  const target=e.target.closest('[data-room-map],[data-resize-room]');if(!target)return;
  const index=Number(target.dataset.roomMap??target.dataset.resizeRoom);roomIndex=index;
  const original=clone(area().rooms[index]),start=point(e),resizing=target.hasAttribute('data-resize-room');
  if(mapMode==='door'){render();return;}
  if((project.locked_rooms||[]).includes(original.id)){notify('Unlock this room before moving or resizing it.',true);render();return;}
  let dx=0,dy=0;const rect=svg.querySelector(`[data-room-map="${index}"]`);
  navigation.begin(e,event=>{
   const p=point(event);dx=Math.round(p.x-start.x);dy=Math.round(p.y-start.y);
   if(resizing){rect.setAttribute('width',Math.max(1,original.width+dx));rect.setAttribute('height',Math.max(1,original.height-dy));rect.setAttribute('y',area().height-original.y-Math.max(1,original.height-dy));}
   else{rect.setAttribute('x',original.x+dx);rect.setAttribute('y',area().height-original.y-original.height+dy);}
  },()=>{
   if(!dx&&!dy){render();return;}
   task(null,async()=>{try{await commitMap(original.id,resizing?'resize':'move',resizing?{width:Math.max(1,original.width+dx),height:Math.max(1,original.height-dy)}:{x:original.x+dx,y:original.y-dy});}catch(e){render();throw e;}});
  },()=>render());
 };
}
async function designAction(name){
 if(await spatialAction(name))return true;
 if(['openAurora','updateArea','testArea'].includes(name)&&proposal?.proposal){showProposal();notify('Apply this generated proposal before building, or discard it to keep your current draft.',true);return true;}
 if(name==='generateSelectedFloorplan'||name.startsWith('generateFloorplan_')||((name==='generateArea'||(name==='generate'&&$('#aiScope')?.value==='area'))&&area()?.references?.length)){const reference_index=name.startsWith('generateFloorplan_')?Number(name.split('_').at(-1)):Number($('#generationFloorplan')?.value||0);const areaId=area().id;await designOperation(async()=>{const result=await api('/api/design/analyze-reference',{project,area_id:areaId,reference_index});showReferenceChecklist(result.plan,areaId);});return true;}
 if(name==='reviewSavedChecklist'){showReferenceChecklist(clone(area().design_plan),area().id);return true;}
 if(name==='chooseNativeGroup'){if(area().geometry)throw Error('Switch to native tiles before choosing a native group.');await showNativeGroups();return true;}
 if(name==='checkPositions'){report=await api('/api/author/review',{project});render();notify(report.errors.length?report.errors.join('\n'):'Object positions checked. Update generated area to rebuild.',!!report.errors.length);return true;}
 if(name==='createAdventure'){$('#newProject').click();$('#newMode').value='adventure';$('#newTitle').value='My adventure';return true;}
 if(name==='attachArea'){const target_id=$('#attachAdventure').value;if(!target_id)throw Error('Choose or create an adventure first.');await designOperation(async()=>{await save();const result=await api('/api/design/attach-area',{project,area_id:area().id,target_id});$('#attachStatus').textContent=result.message;app.projects=(await api('/api/state')).projects;projectList();notify(result.message);});return true;}
 if(name==='updateArea'){await designOperation(async()=>{const result=await api('/api/design/update-area',{project,area_id:area().id});dirty=false;renderHeader();const id=result.build.build_id;$('#designStatus').innerHTML=`<div class="card"><strong>${E(result.area)} updated</strong><p>Your draft is saved and a new native area preview includes the current room layout and contents.</p><p><a href="/download?build=${encodeURIComponent(id)}&kind=mod">Download updated area module</a> · <a href="/download?build=${encodeURIComponent(id)}&kind=zip">Download complete package with HAKs</a></p><button id="openUpdatedArea" class="primary">Open updated area in Aurora</button><p class="hint">This isolated preview uses a walkthrough quest. Full-adventure export remains in Build & share. Existing Aurora copies are not changed.</p><code>${E(result.build.path)}</code></div>`;$('#openUpdatedArea').onclick=e=>task(e.target,async()=>{const opened=await api('/api/design/open-area-build',{build_id:id});notify('Aurora launch requested. Open '+opened.area+' in the Areas tree.');});notify('Area rebuilt from your current edits and draft saved.');});return true;}
 if(name==='undoDesign'){if(previousDraft){const old=project;project=previousDraft;previousDraft=old;change();render();}return true;}
 if(name==='regenerateRoom'){const instruction=$('#roomDirection').value.trim();if(!instruction)throw Error('Describe the changes you want in this room.');await designOperation(async()=>{proposal=await api('/api/design/room',{project,room_id:selectedRoom().id,instruction});showProposal();});return true;}
 if(name==='encounterTemplate'){proposal=await api('/api/design/encounter',{project,room_id:selectedRoom().id,kind:$('#encounterKind').value,difficulty:$('#encounterDifficulty').value,brief:$('#encounterBrief').value});showProposal();return true;}
 if(name==='testArea'){await designOperation(async()=>{const result=await api('/api/design/test-area',{project,area_id:area().id});$('#designStatus').innerHTML=`<p>Installed <strong>${E(result.module)}</strong>. Open NWN separately, start a new game in this module and choose a test character. Installed at <code>${E(result.installed)}</code>.</p>`;});return true;}
 if(name==='interpretFloorplan'){const index=Number($('#generationFloorplan').value);await designOperation(async()=>{const result=await api('/api/design/interpret',{project,area_id:area().id,reference_index:index});showInterpretation(result,area().id);});return true;}
 return false;
}
function showInterpretation(result,areaId){
 const input=(label,path,value,type='text')=>`<label class="field"><span>${E(label)}</span><input data-plan="${path}" type="${type}" value="${E(value)}"></label>`;
 function draw(){modal(`<h2>Review the floor-plan interpretation</h2><p>Correct room names, purposes, tile dimensions and door connections before generating furnishings. This step changes layout only.</p><h3>Assumptions and uncertainties</h3><ul>${result.assumptions.map(x=>`<li>${E(x)}</li>`).join('')||'<li>No assumptions were reported. Check the image against the plan.</li>'}</ul><div class="row">${input('Width (tiles)','area.width',result.area.width,'number')}${input('Height (tiles)','area.height',result.area.height,'number')}${input('Area type: castle / dungeon / cave / forest / desert / winter','area.type',result.area.type)}</div><h3>Rooms · ${result.area.rooms.length}</h3>${result.area.rooms.map((r,i)=>`<div class="connection-card"><div class="row">${input('Name',`area.rooms.${i}.name`,r.name)}${input('Purpose',`area.rooms.${i}.purpose`,r.purpose)}</div><div class="row">${['x','y','width','height'].map(k=>input(k,`area.rooms.${i}.${k}`,r[k],'number')).join('')}</div>${input('ID · preserve IDs used by the adventure',`area.rooms.${i}.id`,r.id)}<button data-remove-plan-room="${i}">Remove room</button></div>`).join('')}<button id="addPlanRoom">Add room</button><h3>Connections</h3><p class="hint">Room IDs above; wall sides north, east, south or west.</p>${result.connections.map((c,i)=>`<div class="row">${['from_room','from_side','to_room','to_side'].map(k=>input(k,`connections.${i}.${k}`,c[k])).join('')}<button data-remove-plan-door="${i}">Remove</button></div>`).join('')}<button id="addPlanDoor">Add connection</button><p id="planError" role="status"></p><button id="reviewPlan" class="primary">Check layout and preview changes</button>`);
 document.querySelectorAll('[data-plan]').forEach(el=>el.oninput=()=>{const parts=el.dataset.plan.split('.');let obj=result;for(const k of parts.slice(0,-1))obj=obj[k];obj[parts.at(-1)]=el.type==='number'?Number(el.value):el.value;});
 document.querySelectorAll('[data-remove-plan-room]').forEach(b=>b.onclick=()=>{const [r]=result.area.rooms.splice(Number(b.dataset.removePlanRoom),1);result.connections=result.connections.filter(c=>c.from_room!==r.id&&c.to_room!==r.id);draw();});
 document.querySelectorAll('[data-remove-plan-door]').forEach(b=>b.onclick=()=>{result.connections.splice(Number(b.dataset.removePlanDoor),1);draw();});
 $('#addPlanRoom').onclick=()=>{let n=1;while(JSON.stringify(result).includes('"plan_room_'+n+'"'))n++;result.area.rooms.push({id:'plan_room_'+n,name:'New room',purpose:'Exploration',description:'',x:1,y:1,width:2,height:2});draw();};
 $('#addPlanDoor').onclick=()=>{let n=1;while(JSON.stringify(result).includes('"plan_door_'+n+'"'))n++;result.connections.push({id:'plan_door_'+n,name:'Passage',from_room:result.area.rooms[0]?.id||'',to_room:result.area.rooms[1]?.id||'',from_side:'east',to_side:'west',kind:'corridor',two_way:true,requires_quest:''});draw();};
 $('#reviewPlan').onclick=e=>task(e.target,async()=>{try{proposal=await api('/api/design/apply-plan',{project,area_id:areaId,interpretation:result});$('#modal').close();showProposal();}catch(err){$('#planError').textContent=err.message;}});
 }
 draw();
}

function positionPanel(a){return placementPanel(a);}
function objectMarkers(a){
 const rooms=Object.fromEntries(a.rooms.map(r=>[r.id,r])),objects=Object.fromEntries([...project.furnishings,...(project.custom_placements||[])].map(f=>[f.id,f]));
 return measuredOutlines(a)+(project.object_positions||[]).map(pos=>{
  const f=objects[pos.id],r=f&&rooms[f.room];if(!r)return '';
  const x=r.x+pos.x/10,y=a.height-r.y-pos.y/10,angle=pos.facing*Math.PI/180,b=project.asset_geometry?.[f.asset_id];let outline='';
  if(b){const points=[[b[0][0],b[0][1]],[b[1][0],b[0][1]],[b[1][0],b[1][1]],[b[0][0],b[1][1]]].map(([u,v])=>`${x+(u*Math.cos(angle)-v*Math.sin(angle))/10},${y-(u*Math.sin(angle)+v*Math.cos(angle))/10}`).join(' ');outline=`<polygon points="${points}" fill="#53e2e2" fill-opacity=".15" stroke="#53e2e2" stroke-width=".035" pointer-events="none"/>`;}
  const selected=inspectedFixture?.project===project.id&&inspectedFixture.id===pos.id;
  return `<g data-object-group="${E(pos.id)}">${outline}<g data-object-position="${E(pos.id)}" class="fixture-marker${selected?' selected-fixture':''}" transform="translate(${x} ${y})" role="button" tabindex="0" aria-label="${E(f.name)} · fixture details" aria-haspopup="dialog"><title>${E(f.name)} · click for details; drag to move</title><circle class="fixture-hit" r=".11" fill="transparent"/><circle class="fixture-dot" r=".065" fill="#53c9ef" stroke="#092e45" stroke-width=".012" pointer-events="none"/><path class="fixture-direction" d="M .072 0 L .025 -.035 L .025 .035 Z" transform="rotate(${-pos.facing})" fill="#ff4b55" stroke="#4c0910" stroke-width=".006" pointer-events="none"/></g></g>`;
 }).join('');
}
function showReferenceChecklist(plan,areaId){
 const stock=app.authoring_catalog.furnishings;const options=Array.isArray(stock)?stock:Object.keys(stock);let accepted=false;
 function draw(){const names=Object.fromEntries(plan.area.rooms.map(r=>[r.id,r.name]));modal(`<h2>Review objects and scale</h2><p>The AI extracted this checklist. Correct uncertain details before generating. The module will use the selected assets and quantities.</p><h3>Scale</h3>${plan.measurements.map((m,i)=>`<div class="card"><strong>${E(names[m.room]||m.room)}</strong> · ${E(m.basis)}<p>${E(m.evidence)}</p><div class="row"><label>Reference width · m<input data-measure="${i}:width_m" type="number" min="1" max="160" value="${m.width_m}"></label><label>Reference depth · m<input data-measure="${i}:height_m" type="number" min="1" max="160" value="${m.height_m}"></label></div><p data-native-scale="${i}">Nominal tile footprint: ${Math.max(1,Math.ceil(m.width_m/10))*10} × ${Math.max(1,Math.ceil(m.height_m/10))*10} m</p></div>`).join('')}<p class="hint">${plan.area.geometry?'Measured stone walls preserve the reviewed clear dimensions, including rooms smaller than 10 m. The tile envelope only packages the geometry.':'Native tile footprints use 10 m increments. Surrounding wall tiles and authored native groups determine the available clear space. Outdoor terrain keeps its native tiles.'}</p><h3>Raised platforms and stairs</h3>${plan.area.rooms.map((r,ri)=>(r.platforms||[]).map((p,pi)=>`<div class="card"><strong>${E(p.name)} · ${E(r.name)}</strong>${platformFields(p,ri+'.'+pi,'data-plan-platform')}</div>`).join('')).join('')||'<p>None detected in this plan.</p>'}<h3>Carpets and runners</h3>${plan.area.rooms.map((r,ri)=>(r.carpets||[]).map((c,ci)=>`<div class="card"><strong>${E(c.name)} · ${E(r.name)}</strong>${carpetFields(c,ri+'.'+ci,'data-plan-carpet')}</div>`).join('')).join('')||'<p>None detected in this plan.</p>'}<h3>Required objects</h3>${plan.objects.map((obj,i)=>{const match=plan.matches.find(m=>m.id===obj.id);return `<div class="connection-card"><strong>${E(obj.name)}</strong> · ${E(names[obj.room])}<p>${E(obj.description)}</p><label>Count<input data-object-count="${i}" ${match.status==='geometry'?'disabled':''} type="number" min="1" max="20" value="${obj.count}"></label><label>Chosen asset<select data-object-match="${i}" ${match.status==='geometry'?'disabled':''}>${match.status==='geometry'?'<option selected>Built area geometry</option>':''}<option value="" ${match.status==='unavailable'?'selected':''}>Unavailable / omit from build</option>${options.map(k=>`<option value="stock:${E(k)}" ${match.stock_kind===k?'selected':''}>Stock: ${E(k)}</option>`).join('')}${plan.assets.map(a=>`<option value="custom:${E(a.id)}" ${match.asset_id===a.id?'selected':''}>HAK: ${E(a.name)}</option>`).join('')}</select></label><p><strong>${E(match.status)}</strong> — ${E(match.reason)}</p></div>`;}).join('')}<h3>Assumptions</h3><ul>${plan.assumptions.map(s=>`<li>${E(s)}</li>`).join('')}</ul><label class="check"><input id="acceptReferenceChanges" type="checkbox" ${accepted?'checked':''}>I accept the listed substitutions and missing objects.</label><p class="hint">Generation keeps the reviewed scale and counts, then assigns exact furnishing positions. It may make multiple authoring-model requests.</p><button id="generateReviewedReference" class="primary">Generate reviewed area</button><div id="referenceError" role="status"></div>`);
 document.querySelectorAll('[data-plan-carpet]').forEach(el=>el.onchange=()=>{const [ri,ci,key]=el.dataset.planCarpet.split('.');plan.area.rooms[Number(ri)].carpets[Number(ci)][key]=['color','border'].includes(key)?el.value:Number(el.value);draw();});
 document.querySelectorAll('[data-plan-platform]').forEach(el=>el.onchange=()=>{const [ri,pi,key]=el.dataset.planPlatform.split('.');plan.area.rooms[Number(ri)].platforms[Number(pi)][key]=key==='stair_side'?el.value:Number(el.value);draw();});
 document.querySelectorAll('[data-measure]').forEach(el=>el.oninput=()=>{const [i,k]=el.dataset.measure.split(':');plan.measurements[Number(i)][k]=Number(el.value);const m=plan.measurements[Number(i)];$(`[data-native-scale="${i}"]`).textContent=`Nominal tile footprint: ${Math.max(1,Math.ceil(m.width_m/10))*10} × ${Math.max(1,Math.ceil(m.height_m/10))*10} m`;});
 document.querySelectorAll('[data-object-count]').forEach(el=>el.oninput=()=>plan.objects[Number(el.dataset.objectCount)].count=Number(el.value));
 document.querySelectorAll('[data-object-match]').forEach(el=>el.onchange=()=>{const obj=plan.objects[Number(el.dataset.objectMatch)],match=plan.matches.find(m=>m.id===obj.id),[kind,id]=el.value.split(':');match.asset_id=kind==='custom'?id:'';match.stock_kind=kind==='stock'?id:'';match.status=el.value?'substitute':'unavailable';match.reason=el.value?'Manually selected replacement; verify its appearance in Aurora.':'Explicitly omitted from the build.';draw();});
 $('#acceptReferenceChanges').onchange=e=>accepted=e.target.checked;
 $('#generateReviewedReference').onclick=e=>task(e.target,()=>designOperation(async()=>{try{proposal=await api('/api/design/generate-reviewed',{project,area_id:areaId,plan,accept_substitutions:accepted});$('#modal').close();showProposal();}catch(err){$('#referenceError').textContent=err.message;}}));
 }
 draw();
}
