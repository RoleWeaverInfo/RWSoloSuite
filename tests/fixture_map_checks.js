const fs=require('fs'),vm=require('vm'),assert=require('assert');
const els={},controls={};let dirtyCount=0,reviewCount=0;
const ctx={console,document:{querySelector:s=>els[s]||null,querySelectorAll:s=>controls[s]||[]}};
vm.createContext(ctx);
for(const name of ['spatial','design'])vm.runInContext(fs.readFileSync('web/'+name+'.js','utf8'),ctx);
const editor=fs.readFileSync('web/editor.js','utf8');vm.runInContext(editor.slice(0,editor.indexOf("$('#saveProject').onclick")),ctx);
const run=s=>vm.runInContext(s,ctx);
run(`project={id:'fixture_test',areas:[{id:'hall',width:10,height:10,rooms:[{id:'room',name:'Reading room',x:1,y:1,width:4,height:4}]}],furnishings:[{id:'desk',name:'Writing <desk>',kind:'desk',room:'room',description:'Desk & papers'},{id:'paper',name:'Papers',kind:'book',room:'room'}],custom_placements:[{id:'lamp',name:'Lamp',asset_id:'hak_lamp',room:'room'}],custom_assets:[{id:'hak_lamp',name:'HAK lamp'}],object_positions:[{id:'desk',x:5,y:5,z:0,facing:0,support:''},{id:'paper',x:6,y:5,z:.1,facing:30,support:'desk'},{id:'lamp',x:10,y:10,z:0,facing:90,support:''}],locked_rooms:[]};`);
ctx.change=()=>dirtyCount++;ctx.api=async(_path,body)=>{reviewCount++;assert(body.project!==run('project'));return {errors:[]};};
const layer=els['.worldmap .map-fixtures']={innerHTML:''};
els['[data-action="undoDesign"]']={disabled:true};
controls['[data-spatial^="object_positions."]']=[{dataset:{spatial:'object_positions.1.x'},value:6},{dataset:{spatial:'object_positions.1.facing'},value:30}];
async function checks(){
 const initial=run('JSON.stringify(project)'),view=ctx.mapView(ctx.area());ctx.zoomMapView(ctx.area(),3);const camera=ctx.mapViewBox(ctx.area());
 let markup=ctx.objectMarkers(ctx.area());assert(markup.includes('r=".065"'));assert(markup.includes('class="fixture-direction"'));assert(markup.includes('fill="#ff4b55"'));assert(markup.includes('rotate(-90)'));assert(!markup.includes(' l '));assert.equal((markup.match(/aria-haspopup="dialog"/g)||[]).length,3);
 assert(markup.includes('Writing &lt;desk&gt;'));assert(ctx.fixtureInfoHtml('desk').includes('Desk &amp; papers'));assert(ctx.fixtureInfoHtml('lamp').includes('HAK lamp'));assert(ctx.fixtureInfoHtml('paper').includes('Writing &lt;desk&gt;'));
 await ctx.rotateMapFixture('desk',90);assert.equal(run('project.object_positions[0].facing'),90);assert.equal(run('project.object_positions[1].x'),5);assert.equal(run('project.object_positions[1].y'),6);assert.equal(run('project.object_positions[1].facing'),120);
 assert.equal(run('JSON.stringify(previousDraft)'),initial);assert.equal(dirtyCount,1);assert.equal(reviewCount,1);assert(layer.innerHTML.includes('rotate(-90)'));assert.equal(controls['[data-spatial^="object_positions."]'][0].value,5);assert.equal(els['[data-action="undoDesign"]'].disabled,false);assert.equal(ctx.mapViewBox(ctx.area()),camera);
 await ctx.rotateMapFixture('desk',-90);assert.equal(run('project.object_positions[0].facing'),0);assert.equal(run('project.object_positions[1].x'),6);assert.equal(run('project.object_positions[1].y'),5);
 await ctx.rotateMapFixture('lamp',-135);assert.equal(run('project.object_positions[2].facing'),315);
 // Locked fixtures remain inspectable, but cannot rotate or request validation.
 run("project.locked_rooms=['room']");assert(ctx.fixtureInfoHtml('desk').includes('class="fixture-rotation" disabled'));const count=reviewCount;
 await assert.rejects(()=>ctx.rotateMapFixture('desk',45),/Unlock/);assert.equal(reviewCount,count);run('project.locked_rooms=[]');
 // Failed or stale async reviews never change the draft, undo, or dirty state.
 const before=run('JSON.stringify(project)'),undo=run('JSON.stringify(previousDraft)'),dirtyBefore=dirtyCount;
 ctx.api=async()=>{throw Error('Review unavailable');};await assert.rejects(()=>ctx.rotateMapFixture('desk',45),/Review unavailable/);
 assert.equal(run('JSON.stringify(project)'),before);assert.equal(run('JSON.stringify(previousDraft)'),undo);assert.equal(dirtyCount,dirtyBefore);
 ctx.api=async()=>{run("project.areas[0].rooms[0].name='Edited during review'");return {errors:[]};};await assert.rejects(()=>ctx.rotateMapFixture('desk',45),/draft changed/);assert.equal(run('project.object_positions[0].facing'),0);assert.equal(dirtyCount,dirtyBefore);
 await assert.rejects(()=>ctx.rotateMapFixture('missing',45),/no longer/);
 console.log('Fixture details, compact markers, rotation, supported items, locks, view retention, and failed/stale reviews passed.');
}
checks().catch(error=>{console.error(error);process.exitCode=1;});
