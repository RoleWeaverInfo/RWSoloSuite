'use strict';
// Curated recommendations, checked against provider documentation on 2026-11-20.
// A model's published free tier is not evidence of an account's billing tier.
window.AISetup=(()=>{
 const E=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const catalog={
  gemini:{name:'Google Gemini',keyURL:'https://aistudio.google.com/apikey',pricing:'https://aistudio.google.com/docs/pricing',account:'https://aistudio.google.com/usage',accountLabel:'Check billing tier & limits',
   fields:['gemini_model','authoring_gemini_model'],recommended:['gemini-3.5-flash-lite','gemini-3.6-flash'],
   models:[['gemini-3.5-flash-lite','Gemini 3.5 Flash-Lite · free tier available'],['gemini-3.6-flash','Gemini 3.6 Flash · free tier available']],
   intro:'Free tier available for selected models, subject to Google’s account, region and usage limits.',
   steps:'Sign in to Google AI Studio, create or choose your project, then create an API key. Copy the key and return here.',
   recommendation:'Start with Flash-Lite for NPC conversations and Flash for floor plans and adventure design. Both accept images and support structured responses.'},
  openai:{name:'OpenAI',keyURL:'https://platform.openai.com/api-keys',pricing:'https://developers.openai.com/api/docs/pricing',account:'https://platform.openai.com/settings/organization/billing/overview',accountLabel:'Open API billing',
   fields:['model','authoring_model'],recommended:['gpt-6-luna','gpt-6.2-sol'],
   models:[['gpt-6-luna','GPT-6 Luna · paid · economical conversations'],['gpt-6.2-sol','GPT-6.2 Sol · paid · balanced authoring'],['gpt-6.2-astra','GPT-6.2 Astra · paid · demanding floor plans']],
   intro:'Paid API usage. OpenAI has no ongoing free API tier for these models. Promotional credits, if offered, are temporary.',
   steps:'Sign in to OpenAI Platform, choose your project and create a secret API key. Copy it when shown, then return here. Check API billing and available credits before generating.',
   recommendation:'Start with Luna for NPC conversations and Sol for authoring. Astra is an option for harder floor plans, with a higher cost. API billing is separate from ChatGPT subscriptions.'}
 };
 const link=(url,label,button=false)=>`<a ${button?'class="setup-link" ':''}href="${url}" target="_blank" rel="noopener noreferrer">${label} ↗</a>`;
 function mount(container,{state,api,onState=()=>{}}){
  let selected=state.settings.provider,busy=false;
  const drafts={};
  for(const [id,c] of Object.entries(catalog)){
   const configured=state.credentials?.[id]?.available||state.credentials?.[id]?.saved;
   drafts[id]={models:c.fields.map((f,i)=>configured?(state.settings[f]||c.recommended[i]):c.recommended[i]),effort:state.settings.authoring_reasoning||'medium'};
  }
  const q=s=>container.querySelector(s);
  const feedback=(text,error=false)=>{const el=q('[data-setup-message]');el.textContent=text;el.classList.toggle('error',error);};
  async function sync(){state=await api('/api/state');onState(state);status();}
  function status(){
   const credential=state.credentials?.[selected]||{},c=catalog[selected];
   q('[data-setup-status]').textContent=credential.error|| (credential.saved?'Key saved locally for this user account.':credential.available?'An environment key is available. You can keep using it, or save a replacement below.':'No key is configured for '+c.name+'.');
   q('[data-setup-remove]').disabled=!credential.saved;
   q('[data-setup-current]').textContent='Currently active: '+(catalog[state.settings.provider]?.name||state.settings.provider)+'. Selecting a tab does not switch the active provider.';
  }
  function modelField(index,label){
   const c=catalog[selected],current=drafts[selected].models[index],known=c.models.some(([id])=>id===current);
   return `<label class="field"><span>${label}</span><select data-setup-model="${index}">${c.models.map(([id,name])=>`<option value="${id}" ${current===id?'selected':''}>${name}</option>`).join('')}<option value="custom" ${!known?'selected':''}>Custom / existing model ID</option></select></label><label class="field" data-setup-custom-wrap="${index}" ${known?'hidden':''}><span>${label} · custom model ID</span><input data-setup-custom="${index}" value="${E(current)}" autocomplete="off" spellcheck="false" maxlength="100"></label>`;
  }
  function modelValues(){
   return [0,1].map(i=>{const select=q(`[data-setup-model="${i}"]`),value=(select.value==='custom'?q(`[data-setup-custom="${i}"]`).value:select.value).trim();
    if(!/^[A-Za-z0-9._-]{1,100}$/.test(value))throw Error('Enter a valid model ID for '+(i?'authoring':'conversations')+'.');return value;});
  }
  async function run(fn){
   if(busy)return;busy=true;
   const controls=[...container.querySelectorAll('button,input,select')],disabled=controls.map(el=>el.disabled);
   controls.forEach(el=>el.disabled=true);feedback('Working…');
   try{await fn();}catch(error){feedback(error.message,true);}
   finally{controls.forEach((el,i)=>el.disabled=disabled[i]);busy=false;status();}
  }
  function draw(){
   const c=catalog[selected];
   container.innerHTML=`<div class="card ai-setup"><h2>Set up your AI</h2><p>Use your own Gemini or OpenAI key for gameplay and module creation. One provider is active at a time, with separate models for each task.</p><div class="setup-providers" role="group" aria-label="Choose a provider to set up">${Object.entries(catalog).map(([id,item])=>`<button data-setup-provider="${id}" aria-pressed="${selected===id}" class="${selected===id?'primary':'quiet'}">${item.name}<small>${id==='gemini'?'Free tier available':'Paid API'}</small></button>`).join('')}</div><p class="hint" data-setup-current></p>
    <section class="setup-step"><h3><span class="setup-number">1</span> Get your own ${c.name} key</h3><p>${c.intro}</p><p>${c.steps}</p><div class="actions">${link(c.keyURL,'Get '+(selected==='openai'?'an OpenAI':'a Gemini')+' API key',true)}${link(c.account,c.accountLabel)}${link(c.pricing,'Model pricing')}</div>
    ${selected==='gemini'?`<p class="hint">A free-tier model can still incur charges on a paid project. Check your project’s tier and quota in AI Studio; Studio cannot determine them from your key. Free-tier content may be used to improve Google products. ${link('https://aistudio.google.com/docs/terms','Eligibility, data use & regional terms')}</p>`:''}</section>
    <section class="setup-step"><h3><span class="setup-number">2</span> Save your key on this computer</h3><p class="setup-key-status" data-setup-status></p><label class="field"><span>${c.name} API key</span><input data-setup-key type="password" autocomplete="new-password" spellcheck="false" autocapitalize="none" maxlength="4096" placeholder="Paste your key here to save or replace it"></label><div class="actions"><button data-setup-save-key>Save key locally</button><button data-setup-remove class="quiet danger">Remove saved key</button></div><p class="hint">Protected by Windows DPAPI, macOS Keychain or the Linux desktop keyring, stored outside projects, and excluded from shared modules and ZIPs. Saving a key does not verify provider access. Removing it leaves any environment key available.</p></section>
    <section class="setup-step"><h3><span class="setup-number">3</span> Choose models and enable ${c.name}</h3><p>${c.recommendation}</p><div class="setup-models"><div>${modelField(0,'Gameplay conversations & AI DM')}</div><div>${modelField(1,'Module creation & floor plans')}</div></div>
    ${selected==='openai'?`<label class="field"><span>Authoring reasoning effort</span><select data-setup-effort>${['default','low','medium','high','xhigh','max'].map(v=>`<option ${v===drafts[selected].effort?'selected':''}>${v}</option>`).join('')}</select></label><p class="hint">Medium is a useful starting point for authoring. Stronger reasoning can take longer and use more tokens. Custom models must support the chosen effort.</p>`:''}
    <p class="hint">Suggestions checked 20 November 2026. Availability and pricing can change. Custom models need text output, image input for floor plans, and structured JSON output. Model checks confirm access to metadata, not generation permissions or a free allowance.</p><div class="actions"><button data-setup-recommend class="quiet">Use recommended models</button><button data-setup-check class="quiet">Check model access</button><button data-setup-activate class="primary">Save and use ${c.name}</button></div><p class="hint">Checking access makes a provider metadata request; it does not generate text or images. Save and use changes the active provider for both gameplay and authoring.</p></section><p class="setup-feedback" data-setup-message role="status" aria-live="polite"></p></div>`;
   status();
   container.querySelectorAll('[data-setup-provider]').forEach(el=>el.onclick=()=>{if(busy)return;if(q('[data-setup-key]').value){feedback('Save or clear the pasted key before switching providers.',true);return;}selected=el.dataset.setupProvider;draw();});
   container.querySelectorAll('[data-setup-model]').forEach(el=>el.onchange=()=>{const i=Number(el.dataset.setupModel);q(`[data-setup-custom-wrap="${i}"]`).hidden=el.value!=='custom';drafts[selected].models[i]=el.value==='custom'?q(`[data-setup-custom="${i}"]`).value:el.value;feedback('Model choice changed. Save and use to apply it.');});
   container.querySelectorAll('[data-setup-custom]').forEach(el=>el.oninput=()=>drafts[selected].models[Number(el.dataset.setupCustom)]=el.value);
   if(q('[data-setup-effort]'))q('[data-setup-effort]').onchange=e=>drafts[selected].effort=e.target.value;
   q('[data-setup-recommend]').onclick=()=>{if(q('[data-setup-key]').value){feedback('Save or clear the pasted key before resetting model choices.',true);return;}drafts[selected]={models:[...c.recommended],effort:'medium'};draw();feedback('Recommended models selected. Save and use to apply them.');};
   q('[data-setup-save-key]').onclick=()=>run(async()=>{
    const input=q('[data-setup-key]'),key=input.value.trim();
    try{if(key.length<8||key.length>4096||/\s/.test(key))throw Error('Paste a complete API key without whitespace.');await api('/api/credentials',{provider:selected,key});await sync();feedback('Key saved locally. You can now check model access and save your model choices.');}
    finally{input.value='';}
   });
   q('[data-setup-remove]').onclick=()=>{if(!window.confirm('Remove the saved '+c.name+' API key from this computer?\n\nAny environment key remains available. This does not revoke the key at the provider.'))return;return run(async()=>{await api('/api/credentials',{provider:selected,remove:true});q('[data-setup-key]').value='';await sync();feedback('Saved key removed from this computer.');});};
   q('[data-setup-check]').onclick=()=>run(async()=>{
    if(q('[data-setup-key]').value)throw Error('Save the pasted key first. This check uses the saved or environment key.');
    const result=await api('/api/credentials/check',{provider:selected,models:modelValues()});feedback(result.models.join(', ')+': '+result.message);
   });
   q('[data-setup-activate]').onclick=()=>run(async()=>{
    if(q('[data-setup-key]').value)throw Error('Save the pasted key before enabling this provider.');
    if(!state.credentials?.[selected]?.available)throw Error('Save a key for '+c.name+' first.');
    const values=modelValues(),patch={provider:selected};c.fields.forEach((f,i)=>patch[f]=values[i]);
    if(selected==='openai')patch.authoring_reasoning=q('[data-setup-effort]').value;
    await api('/api/settings',patch);drafts[selected].models=values;await sync();feedback(c.name+' is now active. Gameplay uses '+values[0]+'; authoring uses '+values[1]+'.');
   });
  }
  draw();
 }
 return {mount};
})();
