// Basic and catalog furniture must share working edit/removal controls.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const elements={'#saveState':{}},removers=[];
const ctx={console,document:{querySelector:s=>elements[s]||null,querySelectorAll:s=>s==='[data-remove]'?removers:[]}};
vm.createContext(ctx);
const source=fs.readFileSync('web/editor.js','utf8');
vm.runInContext(source.slice(0,source.indexOf("$('#saveProject').onclick")),ctx);
const run=s=>vm.runInContext(s,ctx);
run(`app={authoring_catalog:{furnishings:['bed','table','crate']}};
project={id:'demo',areas:[{id:'keep',rooms:[{id:'guard',name:'Guard room'}]},{id:'cave',rooms:[{id:'vault',name:'Vault'}]}],
furnishings:[{id:'outside',room:'vault',name:'Hidden cave crate',kind:'crate',placement:'north',description:''},{id:'bed',room:'guard',name:'Guard bed',kind:'bed',placement:'west',description:'Keep east door clear'}],
custom_placements:[{id:'throne',room:'guard',name:'Royal chair',asset_id:'catalog_chair',placement:'north',description:''}],
custom_assets:[{id:'catalog_chair'}],object_positions:[{id:'bed',x:2,y:2,facing:0},{id:'throne',x:7,y:7,facing:0}]};`);
let html=ctx.placedAssetsPanel(ctx.area());
assert(html.includes('Placed furnishings · 2'));
assert(html.includes('Guard bed')&&html.includes('Royal chair'));
assert(!html.includes('<summary>Hidden cave crate'));
assert(html.includes('data-field="furnishings.1.kind"'));
assert(html.includes('data-field="custom_placements.0.description"'));
assert(html.includes('data-remove="furnishings:1"'));
assert(html.includes('data-remove="custom_placements:0"'));
assert(html.includes('data-action="addFurniture"'));
assert(html.includes('fixed position'));
let rendered=0;
ctx.render=()=>rendered++;
ctx.bindSafety=ctx.bindAreaSections=ctx.bindDesign=ctx.bindPresets=()=>{};
removers.push({dataset:{remove:'furnishings:1'}},{dataset:{remove:'custom_placements:0'}});
ctx.bind();removers[0].onclick();
assert.equal(run('project.furnishings.length'),1);
assert.equal(run('project.furnishings[0].id'),'outside');
assert.equal(run('project.object_positions.some(p=>p.id==="bed")'),false);
assert.equal(elements['#saveState'].textContent,'Unsaved draft');
removers[1].onclick();assert.equal(run('project.custom_placements.length'),0);
assert.equal(run('project.object_positions.length'),0);
assert.equal(rendered,2);
run('report=null;async function designAction(){return false;}');
ctx.action('addFurniture').then(()=>{
 assert.equal(run('project.furnishings.at(-1).room'),'guard');
 assert.equal(run('project.furnishings.at(-1).kind'),'crate');
 assert(ctx.placedAssetsPanel(ctx.area()).includes('Supply crate'));
 console.log('Mixed furnishings: listing, editing paths, add/remove and position cleanup passed.');
}).catch(e=>{console.error(e);process.exitCode=1;});
