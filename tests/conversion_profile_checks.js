const fs=require('fs'),vm=require('vm'),assert=require('assert');
const ctx={window:{},console};vm.createContext(ctx);
vm.runInContext(fs.readFileSync('web/conversion.js','utf8'),ctx);
function host(){
  const els={};
  const element=()=>({innerHTML:'',textContent:'',disabled:false,classList:{toggle(){}},querySelectorAll(selector){
    if(selector!=='[data-merchant-field]')return [];
    return this.merchantFields??=Array.from(this.innerHTML.matchAll(/<input[^>]*data-merchant-field="([^"]+)"[^>]*>/g),m=>({dataset:{merchantField:m[1]},checked:m[0].includes('checked'),disabled:false}));
  }});
  let html='';
  return {els,isConnected:true,get innerHTML(){return html;},set innerHTML(value){html=value;for(const match of value.matchAll(/class="([^"]+)"/g))for(const name of match[1].split(' '))els['.'+name]??=element();},querySelector(s){return els[s]??=element();},querySelectorAll(){return Object.values(els);}};
}
const npc={name:'Keeper',alias:'keeper',native_tag:'keeper',native_resref:'keeper',ai_enabled:true,
  role:'Keeper',personality:'Calm',background:'Before generation',motivation:'Help',knowledge:'Public',
  behavior:{communication:'speech'},companion:{},profile_origin:'Authored',profile_sources:['<unsafe>'],native_lines:[],
  merchant:{enabled:true,haggle_enabled:true},native_store:{detected:true,tags:['<store>'],scripts:['trade']}};
const project={title:'Copy',module_name:'copy',summary:'The setting',companions:{enabled:true},npcs:[npc]};
let saved={project:structuredClone(project),dependency_folder:'',build:null},requests=[],finish=0;
async function api(path,body){
  requests.push([path,structuredClone(body)]);
  if(path.endsWith('/conversion-plan'))return structuredClone(saved);
  if(path.endsWith('/profiles')){saved=structuredClone(saved);saved.project.npcs[0].background='Generated background';return {status:'profiling',message:'Generating'};}
  return {saved:true};
}
const tick=()=>new Promise(r=>setImmediate(r));
(async()=>{
  const h=host();ctx.window.ModuleConversion.mount(h,api,'analysis',false,async()=>{finish++;});await tick();
  assert(h.innerHTML.includes('Generate detailed AI profiles'));
  assert(h.els['.conversion-npc'].innerHTML.includes('Personal background'));
  assert(h.els['.conversion-npc'].innerHTML.includes('&lt;unsafe&gt;'));
  assert(h.innerHTML.includes('1 merchant profiles detected'));
  assert(h.els['.conversion-npc'].innerHTML.includes('&lt;store&gt;'));
  const merchantFields=h.els['.conversion-npc'].querySelectorAll('[data-merchant-field]');
  assert.equal(merchantFields.length,2);assert(merchantFields.every(el=>el.checked));
  merchantFields[0].checked=false;merchantFields[0].onchange();
  h.els['.conversion-summary'].oninput({target:{value:'Edited setting'}});
  await h.els['.conversion-save'].onclick();
  assert.equal(requests.find(([url])=>url.endsWith('/conversion-save'))[1].project.summary,'Edited setting');
  assert.equal(requests.find(([url])=>url.endsWith('/conversion-save'))[1].project.npcs[0].merchant.enabled,false);
  await h.els['.conversion-profiles'].onclick();assert.equal(finish,1);
  const refreshed=host();ctx.window.ModuleConversion.mount(refreshed,api,'analysis',false,async()=>{});await tick();
  assert(refreshed.els['.conversion-npc'].innerHTML.includes('Generated background')); // Old draft must not mask result.
  const busy=host();ctx.window.ModuleConversion.mount(busy,api,'analysis',true,async()=>{});await tick();
  assert(busy.els['.conversion-profiles'].disabled);
  assert(busy.els['.conversion-npc'].querySelectorAll('[data-merchant-field]').every(el=>el.disabled));
  console.log('Conversion profiles: edited setting, escaped evidence, merchant opt-out, generation dispatch, result refresh and busy controls passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
