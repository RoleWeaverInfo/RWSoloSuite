const fs=require('fs'),vm=require('vm'),assert=require('assert');
const els=new Map(),timeouts=new Map(),intervals=new Map();let nextTimer=0,mounts=0,refreshes=0,destroys=0;
function element(selector){
  if(els.has(selector))return els.get(selector);
  let html='';
  const el={isConnected:true,hidden:false,disabled:false,textContent:'',value:'',renders:0,
    classList:{toggle(){}},querySelector:element,querySelectorAll(){return [];},
    get selectedOptions(){return [{value:'job',textContent:''}];},
    get innerHTML(){return html;},set innerHTML(value){html=value;this.renders++;}};
  els.set(selector,el);return el;
}
const report={analysis_id:'job',module:{name:'Test adventure',filename:'test.mod'},counts:{characters:13},
  story:{overview:'Story',note:'Evidence',evidence:[],evidence_total:0},warnings:[],limitations:[],resource_types:{},lore:[]};
let job={id:'job',name:'Test adventure',status:'profiling',message:'Generating',profile_progress:{
  completed:0,total:13,started_at:Date.now()/1000-10,batch_started_at:Date.now()/1000-5,
  batch:1,batches:3,current_names:['<guard>','Merchant']}};
const calls=[];
async function api(path,body){
  calls.push(path);
  if(path.endsWith('/list'))return {analyses:[structuredClone(job)]};
  if(path.endsWith('/status'))return structuredClone(job);
  if(path.endsWith('/report'))return structuredClone(report);
  if(path.endsWith('/profiles-pause')){job.pause_requested=true;return structuredClone(job);}
  throw Error('Unexpected endpoint '+path);
}
const ctx={window:{ModuleConversion:{mount(){mounts++;return {setBusy(){},async refresh(){refreshes++;},destroy(){destroys++;}};}}},console,Date,
  setTimeout(fn){const id=++nextTimer;timeouts.set(id,fn);return id;},clearTimeout(id){timeouts.delete(id);},
  setInterval(fn){const id=++nextTimer;intervals.set(id,fn);return id;},clearInterval(id){intervals.delete(id);}};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('web/analyser.js','utf8'),ctx);
const flush=async()=>{for(let i=0;i<8;i++)await new Promise(r=>setImmediate(r));};
async function poll(){assert.equal(timeouts.size,1);const [id,fn]=[...timeouts][0];timeouts.delete(id);fn();await flush();}
(async()=>{
  const controller=ctx.window.ModuleAnalyser.mount(element('host'),api,()=>({settings:{provider:'openai',authoring_model:'test'}}));await flush();
  assert.equal(mounts,1);assert.equal(calls.filter(p=>p.endsWith('/report')).length,1);
  const initialRenders=element('#analysisReport').renders;
  element('#analysisSearch').value='Keep my search';
  assert(element('#analysisProgressBatch').textContent.includes('<guard>')); // Assigned as text, never HTML.
  job.profile_progress={...job.profile_progress,completed:6,batch:2,saved_at:Date.now()/1000,current_names:['Next keeper']};
  await poll();await poll();await poll();
  assert.equal(mounts,1);assert.equal(element('#analysisReport').renders,initialRenders);
  assert.equal(calls.filter(p=>p.endsWith('/report')).length,1);
  assert.equal(element('#analysisSearch').value,'Keep my search');
  assert(element('#analysisProgressCount').textContent.includes('6 of 13 profiles saved'));
  assert.equal(element('#analysisProgressBar').value,6);
  await element('#analysisPauseProfiles').onclick();await flush();
  assert(element('#analysisPauseProfiles').disabled);
  job.status='profile_paused';job.profile_progress.finished_at=Date.now()/1000;
  await poll();assert.equal(refreshes,1);assert.equal(mounts,1);assert.equal(timeouts.size,0);
  assert(element('#analysisPhase').textContent.startsWith('Profiles paused'));
  assert.equal(calls.filter(p=>p.endsWith('/report')).length,1);
  assert(element('#analysisPauseProfiles').hidden);
  controller.destroy();assert.equal(intervals.size,0);assert.equal(destroys,1);
  // Returning to the tab with a cached report still mounts the editor once.
  const again=ctx.window.ModuleAnalyser.mount(element('host'),api,()=>({settings:{provider:'openai',authoring_model:'test'}}));await flush();
  assert.equal(mounts,2);again.destroy();assert.equal(intervals.size,0);
  console.log('Conversion progress: stable editor across polls, saved counts, current batch, pause, one completion refresh and timer cleanup passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
