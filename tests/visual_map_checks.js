// Exercise the real handlers with SVG screen transforms, including letterboxing.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const elements={},buttons={},tasks=[],commits=[],messages=[],inspections=[];
let dirtyCalls=0,renders=0,reviewCalls=0;
function element(dataset={}){
 const classes=new Set();return {dataset,attrs:{},classList:{add:k=>classes.add(k),remove:k=>classes.delete(k),toggle(k,on){if(on)classes.add(k);else classes.delete(k);}},
 setAttribute(k,v){this.attrs[k]=String(v);},getAttribute(k){return this.attrs[k];},hasAttribute(k){return Object.hasOwn(this.attrs,k);},closest(){return null;}};
}
for(const action of ['in','out','fit','room','pan'])buttons[action]=element({mapView:action});
elements['#mapZoom']=element();elements['#mapMode']=element();
const svg=elements['.worldmap']=element(),rect=element({roomMap:'0'}),object=element({objectPosition:'chair'});
rect.closest=selector=>selector.includes('data-room-map')?rect:null;
object.closest=selector=>selector==='[data-object-position]'?object:null;object.parentElement=element();
svg.clientHeight=400;svg.listeners={};svg.focus=()=>{};svg.addEventListener=(name,fn)=>svg.listeners[name]=fn;
svg.querySelector=()=>rect;svg.capture=null;svg.setPointerCapture=id=>svg.capture=id;svg.hasPointerCapture=id=>svg.capture===id;svg.releasePointerCapture=()=>svg.capture=null;
svg.createSVGPoint=()=>({x:0,y:0,matrixTransform(m){return {x:this.x*m.a+m.e,y:this.y*m.d+m.f};}});
function screenMatrix(){const [x,y,w,h]=svg.attrs.viewBox.split(' ').map(Number),scale=Math.min(800/w,400/h);return {x,y,scale,left:40+(800-w*scale)/2,top:30+(400-h*scale)/2};}
svg.getScreenCTM=()=>({inverse(){const m=screenMatrix();return {a:1/m.scale,d:1/m.scale,e:m.x-m.left/m.scale,f:m.y-m.top/m.scale};}});
function eventAt(x,y,target=svg,extra={}){
 const m=screenMatrix();return {clientX:m.left+(x-m.x)*m.scale,clientY:m.top+(y-m.y)*m.scale,pointerId:1,button:0,isPrimary:true,target,preventDefault(){this.prevented=true;},...extra};
}
const ctx={console,document:{querySelector(s){const match=s.match(/^\[data-map-view="(\w+)"\]$/);return match?buttons[match[1]]:elements[s]||null;},querySelectorAll:s=>s==='[data-map-view]'?Object.values(buttons):[]}};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('web/design.js','utf8'),ctx);
const editor=fs.readFileSync('web/editor.js','utf8');vm.runInContext(editor.slice(0,editor.indexOf("$('#saveProject').onclick")),ctx);
vm.runInContext(`project={id:'map_test',areas:[{id:'area_a',width:100,height:60,rooms:[{id:'room_a',name:'Room',x:20,y:20,width:4,height:3}]}],furnishings:[{id:'chair',room:'room_a'}],object_positions:[{id:'chair',x:2,y:3}],locked_rooms:[]};`,ctx);
ctx.bindSpatial=()=>{};ctx.render=()=>renders++;ctx.change=()=>dirtyCalls++;ctx.notify=message=>messages.push(message);
ctx.supportedChildren=()=>{};ctx.api=async()=>{reviewCalls++;return {errors:[]};};
ctx.showFixtureInfo=id=>inspections.push(id);
ctx.task=(_button,fn)=>{const result=fn();tasks.push(result);return result;};ctx.commitMap=async(...args)=>commits.push(args);
const run=s=>vm.runInContext(s,ctx),a=ctx.area(),view=ctx.mapView(a),original=run('JSON.stringify(project)');
const approx=(a,b)=>assert(Math.abs(a-b)<1e-8,`${a} != ${b}`);
async function checks(){
 // Cursor anchoring and bounds; zooming never edits the module.
 const anchor={x:30,y:25};ctx.zoomMapView(a,2,anchor);approx((anchor.x-view.x)/(a.width/view.zoom),.3);approx((anchor.y-view.y)/(a.height/view.zoom),25/60);
 ctx.zoomMapView(a,1e6);assert.equal(view.zoom,16);ctx.zoomMapView(a,1e-6);assert.equal(view.zoom,.5);
 ctx.fitMapView(a);assert.deepEqual([view.x,view.y,view.zoom],[0,0,1]);
 ctx.fitMapView(a,ctx.selectedRoom());assert.equal(view.zoom,15);assert(view.x<=20&&view.x+100/view.zoom>=24);assert(view.y<=37&&view.y+60/view.zoom>=40);
 // Separate area/project views; dimension edits reset the view, not the rooms.
 const other={...a,id:'area_b'};assert.equal(ctx.mapView(other).zoom,1);assert.equal(ctx.mapView(a).zoom,15);
 run("project.id='different_project'");assert.equal(ctx.mapView(a).zoom,1);run("project.id='map_test'");assert.equal(ctx.mapView(a).zoom,15);
 a.width=120;assert.equal(ctx.mapView(a).zoom,1);a.width=100;ctx.fitMapView(a);assert.equal(run('JSON.stringify(project)'),original);
 ctx.bindDesign();buttons.in.onclick();assert.equal(ctx.mapView(a).zoom,1.25);buttons.out.onclick();approx(ctx.mapView(a).zoom,1);
 buttons.pan.onclick();assert.equal(run('mapMode'),'pan');assert.equal(buttons.pan.attrs['aria-pressed'],'true');
 buttons.pan.onclick();assert.equal(run('mapMode'),'move');assert.equal(renders,0,'View controls must retain unfinished form fields');
 // A click (including small hand jitter) opens details without moving or dirtying.
 let click=eventAt(22,38,object);svg.onpointerdown(click);svg.onpointermove({...click,clientX:click.clientX+2});svg.onpointerup(click);
 assert.equal(inspections.at(-1),'chair');assert.equal(dirtyCalls,0);assert.equal(reviewCalls,0);assert.equal(run('JSON.stringify(project)'),original);
 svg.onkeydown({target:object,key:'Enter',preventDefault(){}});assert.equal(inspections.length,2);
 buttons.pan.onclick();click=eventAt(22,38,object);svg.onpointerdown(click);svg.onpointerup(click);assert.equal(inspections.length,3);buttons.pan.onclick();
 // Wheel keeps the same SVG coordinate under the mouse, even with letterboxing.
 const wheel=eventAt(30,25,svg,{deltaY:-100,deltaMode:0}),beforePoint=ctx.mapPoint(svg,wheel);svg.listeners.wheel(wheel);
 approx(ctx.mapPoint(svg,wheel).x,beforePoint.x);approx(ctx.mapPoint(svg,wheel).y,beforePoint.y);assert(wheel.prevented);
 svg.onkeydown({key:'ArrowRight',preventDefault(){}});assert(ctx.mapView(a).x>0);
 svg.onkeydown({key:'0',preventDefault(){}});assert.equal(ctx.mapView(a).zoom,1);
 // Pan starts over rooms/objects without editing them, and does not drift.
 run("mapMode='pan'");ctx.bindDesign();buttons.in.onclick();buttons.in.onclick();
 let v=ctx.mapView(a),before={...v},start=eventAt(50,30,rect),scale=screenMatrix().scale;
 svg.onpointerdown(start);svg.onpointermove({...start,clientX:start.clientX+20});svg.onpointermove({...start,clientX:start.clientX+40});
 approx(v.x,before.x-40/scale);approx(v.y,before.y);assert.equal(commits.length,0);
 const held=v.zoom;svg.listeners.wheel({...start,deltaY:-100,deltaMode:0});buttons.in.onclick();assert.equal(v.zoom,held);
 svg.onpointerup(start);assert.equal(svg.capture,null);assert.equal(run('JSON.stringify(project)'),original);assert.equal(dirtyCalls,0);
 // Middle-button pans in editing mode; pointer loss clears the active drag.
 run("mapMode='move'");ctx.bindDesign();start=eventAt(50,30,object,{button:1});svg.onpointerdown(start);svg.onpointermove({...start,clientY:start.clientY+20});svg.onlostpointercapture(start);
 buttons.in.onclick();assert(ctx.mapView(a).zoom>held);assert.equal(dirtyCalls,0);assert.equal(run('JSON.stringify(project)'),original);
 // Moving and resizing rooms uses world units at both normal and high zoom.
 for(const zoom of [1,4]){
  ctx.fitMapView(a);ctx.zoomMapView(a,zoom);ctx.bindDesign();const p=eventAt(22,38,rect),q=eventAt(24,37,rect);
  svg.onpointerdown(p);svg.onpointermove(q);svg.onpointerup(q);await Promise.all(tasks.splice(0));
  assert.equal(commits.at(-1)[1],'move');assert.deepEqual(commits.at(-1)[2],{x:22,y:21});
  const handle=element({resizeRoom:'0'});handle.attrs['data-resize-room']='';handle.closest=s=>s.includes('data-resize-room')?handle:null;
  ctx.bindDesign();const begin=eventAt(24,37,handle),end=eventAt(25,35,handle);svg.onpointerdown(begin);svg.onpointermove(end);svg.onpointerup(end);await Promise.all(tasks.splice(0));
  assert.equal(commits.at(-1)[1],'resize');assert.deepEqual(commits.at(-1)[2],{width:5,height:5});
 }
 // Object dragging preserves metre units and cancels cleanly.
 ctx.bindDesign();start=eventAt(22,38,object);let end=eventAt(22.2,37.9,object);svg.onpointerdown(start);svg.onpointermove(end);
 assert.equal(run('project.object_positions[0].x'),4);assert.equal(run('project.object_positions[0].y'),4);
 svg.onpointercancel(end);assert.equal(run('JSON.stringify(project)'),original);assert.equal(dirtyCalls,0);
 ctx.bindDesign();start=eventAt(22,38,object);end=eventAt(22.2,37.9,object);svg.onpointerdown(start);svg.onpointermove(end);svg.onpointerup(end);await Promise.all(tasks.splice(0));
 assert.equal(dirtyCalls,1);assert.equal(reviewCalls,1);
 // Room locks still protect edits, and secondary clicks never edit.
 run("project.locked_rooms=['room_a']");ctx.bindDesign();const count=commits.length;
 svg.onpointerdown(eventAt(22,38,rect));assert(messages.at(-1).includes('Unlock'));assert.equal(svg.capture,null);
 svg.onpointerdown(eventAt(22,38,object));assert.equal(svg.capture,null);
 run('project.locked_rooms=[]');svg.onpointerdown(eventAt(22,38,rect,{button:2}));assert.equal(svg.capture,null);assert.equal(commits.length,count);
 console.log('Camera bounds, cursor anchor, view persistence, pan safety, zoomed edits, cancellation, and locks passed.');
}
checks().catch(e=>{console.error(e);process.exitCode=1;});
