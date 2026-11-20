const fs=require('fs'),vm=require('vm'),assert=require('assert');
const unescape=s=>s.replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&amp;/g,'&');
class Container{
 set innerHTML(html){this.html=html;this.elements=[];
  const re=/<select\b([^>]*)>([\s\S]*?)<\/select>|<(button|input|label|p)\b([^>]*)>/g;
  for(const match of html.matchAll(re)){
   const tag=match[3]||'select',attrs=match[1]??match[4],options=match[2],dataset={};for(const a of attrs.matchAll(/data-([\w-]+)(?:="([^"]*)")?/g))dataset[a[1].replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=unescape(a[2]||'');
   const el={tagName:tag.toUpperCase(),dataset,value:unescape(attrs.match(/\bvalue="([^"]*)"/)?.[1]||''),disabled:false,hidden:/\bhidden\b/.test(attrs),textContent:'',classList:{toggle(){}}};
   if(tag==='select'){
    const choices=[...options.matchAll(/<option([^>]*)>([^<]*)<\/option>/g)],chosen=choices.find(o=>/\bselected\b/.test(o[1]))||choices[0];
    el.value=unescape(chosen[1].match(/value="([^"]*)"/)?.[1]??chosen[2]);
   }
   this.elements.push(el);
  }
 }
 get innerHTML(){return this.html;}
 querySelectorAll(selector){if(selector==='button,input,select')return this.elements.filter(e=>['BUTTON','INPUT','SELECT'].includes(e.tagName));
  const [,raw,value]=selector.match(/^\[data-([\w-]+)(?:="([^"]*)")?\]$/),key=raw.replace(/-([a-z])/g,(_,c)=>c.toUpperCase());
  return this.elements.filter(e=>key in e.dataset&&(value===undefined||e.dataset[key]===value));}
 querySelector(selector){return this.querySelectorAll(selector)[0];}
}
let accept=false;const ctx={window:{confirm:()=>accept}};vm.createContext(ctx);vm.runInContext(fs.readFileSync('web/provider-setup.js','utf8'),ctx);
const container=new Container(),q=s=>container.querySelector(`[data-setup-${s}]`),requests=[];
let state={settings:{provider:'openai',model:'my-current-model',authoring_model:'my-authoring-model',authoring_reasoning:'high',gemini_model:'gemini-2.5-flash',authoring_gemini_model:'gemini-2.5-flash',user_dir:'keep-path'},credentials:{openai:{saved:false,available:true},gemini:{saved:false,available:false}}};
let failSave=false;
async function api(path,body){requests.push({path,body});if(path==='/api/state')return structuredClone(state);
 if(path==='/api/credentials'){if(failSave)throw Error('Windows could not save this key');state.credentials[body.provider]={saved:!body.remove,available:!body.remove};return {credentials:structuredClone(state.credentials)};}
 if(path==='/api/settings'){Object.assign(state.settings,body);return {saved:true};}
 if(path==='/api/credentials/check')return {models:body.models,message:'Metadata only; quota not verified.'};
 throw Error(path);
}
(async()=>{
 let updates=0;ctx.window.AISetup.mount(container,{state:structuredClone(state),api,onState:()=>updates++});
 assert(container.innerHTML.includes('https://platform.openai.com/api-keys'));assert(container.innerHTML.includes('Paid API'));assert.equal(q('custom="0"').value,'my-current-model');assert.equal(requests.length,0);
 await q('provider="gemini"').onclick();assert.equal(state.settings.provider,'openai');assert(container.innerHTML.includes('https://aistudio.google.com/apikey'));assert(container.innerHTML.includes('free tier available'));assert(container.innerHTML.includes('paid project'));
 q('recommend').onclick();assert.equal(q('model="0"').value,'gemini-3.5-flash-lite');assert.equal(requests.length,0);
 await q('activate').onclick();assert(q('message').textContent.includes('Save a key'));assert.equal(requests.length,0);
 q('key').value='fake-test-key';q('provider="openai"').onclick();assert(q('message').textContent.includes('Save or clear'));assert.equal(q('key').value,'fake-test-key');
 q('recommend').onclick();assert.equal(q('key').value,'fake-test-key');await q('check').onclick();assert(q('message').textContent.includes('Save the pasted key'));assert.equal(requests.length,0);
 await q('save-key').onclick();assert.equal(q('key').value,'');assert(state.credentials.gemini.saved);assert.equal(state.settings.provider,'openai');
 await q('check').onclick();assert(q('message').textContent.includes('quota not verified'));assert.equal(state.settings.provider,'openai');
 await q('activate').onclick();assert.equal(state.settings.provider,'gemini');assert.equal(state.settings.gemini_model,'gemini-3.5-flash-lite');assert.equal(state.settings.authoring_gemini_model,'gemini-3.6-flash');assert.equal(state.settings.model,'my-current-model');assert.equal(state.settings.user_dir,'keep-path');
 const patch=requests.find(r=>r.path==='/api/settings').body;assert.deepEqual(Object.keys(patch).sort(),['authoring_gemini_model','gemini_model','provider']);
 const before=requests.length;await q('remove').onclick();assert.equal(requests.length,before);accept=true;await q('remove').onclick();assert(!state.credentials.gemini.saved);
 failSave=true;q('key').value='fake-not-saved';await q('save-key').onclick();assert.equal(q('key').value,'');assert(q('message').textContent.includes('could not save'));assert(!q('save-key').disabled);
 assert(updates>=3);assert(!container.innerHTML.includes('fake-test-key'));
 console.log('Guided setup: provider choice, existing models, local save, free-tier guidance, activation, metadata check and confirmed removal passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
