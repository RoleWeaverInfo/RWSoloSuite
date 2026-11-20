// Cancellation must stop destructive actions before design helpers or API calls run.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const prompts=[];
let accept=false,delegated=0;
const ctx={console,window:{confirm:s=>{prompts.push(s);return accept;}},document:{querySelector:()=>null,querySelectorAll:()=>[]}};
vm.createContext(ctx);
const src=fs.readFileSync('web/editor.js','utf8');
vm.runInContext(src.slice(0,src.indexOf("$('#saveProject').onclick")),ctx);
const run=s=>vm.runInContext(s,ctx);
run(`project={areas:[{id:'keep',name:'Keep',references:[{name:'Blueprint'}],rooms:[{id:'hall',name:'Hall',openings:[{side:'north'}],platforms:[{name:'Dais'}],carpets:[{name:'Runner'}]}]}],npcs:[{name:'Queen'}],quests:[{name:'Quest'}],custom_placements:[{name:'Throne'}]};`);
ctx.designAction=async()=>{delegated++;return true;};
(async()=>{
 const before=run('JSON.stringify(project)');
 const actions=['deleteArea','deleteRoom','deleteNPC','deleteQuest','remove_reference_0','remove_custom_0','removeOpening_0','removePlatform_0','removeCarpet_0','nativeGeometry','removeCourtyard','key_remove_openai','key_remove_gemini'];
 for(const action of actions){
  const n=prompts.length;await ctx.action(action);
  assert.equal(prompts.length,n+1,action+' should confirm');
  assert.equal(delegated,0,action+' should stop before design dispatch');
  assert.equal(run('JSON.stringify(project)'),before,action+' must leave the draft unchanged');
 }
 accept=true;await ctx.action('removeCarpet_0');assert.equal(delegated,1);
 // Settings work even before a project has been selected.
 run('project=null');accept=false;await ctx.action('key_remove_openai');assert.equal(delegated,1);
 assert(prompts.at(-1).includes('saved openai API key'));
 // Floor-plan review has its own editable proposal and removal handlers.
 const controls={},roomButton={dataset:{removePlanRoom:'0'}},doorButton={dataset:{removePlanDoor:'0'}};
 ctx.document.querySelector=s=>controls[s]??={};
 ctx.document.querySelectorAll=s=>({'[data-remove-plan-room]':[roomButton],'[data-remove-plan-door]':[doorButton]}[s]||[]);
 ctx.modal=()=>{};
 vm.runInContext(fs.readFileSync('web/design.js','utf8'),ctx);
 const plan={area:{width:6,height:6,type:'castle',rooms:[{id:'hall',name:'Hall'},{id:'study',name:'Study'}]},connections:[{name:'Study door',from_room:'hall',to_room:'study'}],assumptions:[]};
 ctx.showInterpretation(plan,'keep');
 const planBefore=JSON.stringify(plan);roomButton.onclick();doorButton.onclick();assert.equal(JSON.stringify(plan),planBefore);
 accept=true;doorButton.onclick();assert.equal(plan.connections.length,0);
 plan.connections.push({from_room:'hall',to_room:'study'});roomButton.onclick();assert.equal(plan.area.rooms.length,1);assert.equal(plan.connections.length,0);
 // Restoring the original area appearance is a destructive reset too.
 vm.runInContext(fs.readFileSync('web/presets.js','utf8'),ctx);
 const resetButton={dataset:{lookAction:'reset'}};let tasks=0;
 ctx.document.querySelectorAll=s=>s==='[data-look-action]'?[resetButton]:[];
 ctx.task=()=>{tasks++;};ctx.bindPresets();accept=false;resetButton.onclick();assert.equal(tasks,0);
 accept=true;resetButton.onclick();assert.equal(tasks,1);
 console.log('Dashboard action confirmations: cancel preserves drafts and prevents dispatch; accept proceeds.');
})().catch(e=>{console.error(e);process.exitCode=1;});
