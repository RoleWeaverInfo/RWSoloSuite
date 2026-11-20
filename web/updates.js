'use strict';
// Shared by the authoring dashboard and the player service page.
window.StudioUpdates = (() => {
 let dialog, timer, status, busy=false;
 async function call(action, body={}) {
  const current=await fetch('/api/state').then(r=>r.json());
  const response=await fetch('/api/updates/'+action,{method:'POST',headers:{'Content-Type':'application/json','X-Studio-Token':current.csrf},body:JSON.stringify(body)});
  const result=await response.json();if(!response.ok)throw Error(result.error||'Update request failed');return result;
 }
 function draw(s) {
  status=s;
  const message={idle:'Check for a newer release.',checking:'Checking GitHub releases…',current:'You have the latest release for your update channel.',available:'A newer release is available.',downloading:'Downloading and verifying the update. You can continue working.',ready:'Download verified. Save your work and exit NWN before installing.',installing:'Installing the update. Role Weaver will restart. This page will reconnect.',error:s.error};
  dialog.querySelector('[data-update-status]').textContent=message[s.state]||s.state;
  dialog.querySelector('[data-update-version]').textContent='Installed: '+s.current+(s.release?' · Available: '+s.release.version+' · '+s.release.name:'');
  dialog.querySelector('[data-update-source]').hidden=s.installable;
  dialog.querySelector('[data-update-check]').disabled=busy||['checking','downloading','installing'].includes(s.state);
  dialog.querySelector('[data-update-download]').hidden=!s.installable||!s.release||!['available','error'].includes(s.state);
  dialog.querySelector('[data-update-install]').hidden=s.state!=='ready';
  if(['checking','downloading'].includes(s.state)&&dialog.open){clearTimeout(timer);timer=setTimeout(poll,1500);}
 }
 async function poll(){try{draw(await call('status'));}catch(error){dialog.querySelector('[data-update-status]').textContent=error.message;}}
 async function act(action){
  if(busy)return;
  try {
   if(action==='install'){
    if(window.RoleWeaverBeforeUpdate)await window.RoleWeaverBeforeUpdate();
    if(!confirm('Install Role Weaver '+status.release.version+' and restart the service? Save your work and exit NWN first. Projects, builds and saved API keys will be preserved.'))return;
   }
   busy=true;dialog.querySelectorAll('[data-update-action]').forEach(b=>b.disabled=true);
   const result=await call(action,action==='install'?{confirm:true}:{});busy=false;draw(result);
   if(action==='install'){
    clearTimeout(timer);
    const version=status.release.version;
    let attempts=0;
    const reconnect=async()=>{
     try{const r=await fetch('/api/state',{cache:'no-store'});const state=await r.json();if(state.version===version){location.reload();return;}}catch{}
     if(++attempts<120)timer=setTimeout(reconnect,2000);
     else dialog.querySelector('[data-update-status]').textContent='The service has not reconnected. Start Role Weaver from its normal shortcut. If installation failed, see the update log in your workspace updates folder.';
    };
    timer=setTimeout(reconnect,4000);
   }
  }catch(error){dialog.querySelector('[data-update-status]').textContent=error.message;}
  finally{busy=false;dialog.querySelectorAll('[data-update-action]').forEach(b=>b.disabled=false);if(status&&['checking','downloading','installing'].includes(status.state))dialog.querySelector('[data-update-check]').disabled=true;}
 }
 async function open(){
  if(!dialog){
   dialog=document.createElement('dialog');dialog.setAttribute('aria-label','Software updates');
   dialog.innerHTML='<h2>Update Role Weaver</h2><p data-update-version></p><p role="status" data-update-status></p><p>The service and dashboard update together. Projects, builds and saved keys stay in your workspace. Stable releases receive stable updates; release candidates can receive newer candidates.</p><p data-update-source hidden>This is a source checkout. Automatic installation is available in the Windows, Linux and macOS packages. Source files and local changes are never overwritten. Install a native release or update your checkout separately.</p><p><a href="https://github.com/RoleWeaverInfo/RWSoloSuite/releases" target="_blank" rel="noopener noreferrer">Open official releases</a></p><div class="actions"><button data-update-action data-update-check>Check for updates</button><button data-update-action data-update-download hidden>Download update</button><button data-update-action data-update-install class="primary" hidden>Install update and restart</button><button data-update-close>Close</button></div>';
   document.body.append(dialog);
   dialog.querySelector('[data-update-check]').onclick=()=>act('check');dialog.querySelector('[data-update-download]').onclick=()=>act('download');dialog.querySelector('[data-update-install]').onclick=()=>act('install');dialog.querySelector('[data-update-close]').onclick=()=>dialog.close();
   dialog.addEventListener('close',()=>{if(status?.state!=='installing')clearTimeout(timer);});
  }
  dialog.showModal();await poll();
  if(status?.state==='idle')await act('check');
 }
 document.addEventListener('DOMContentLoaded',()=>document.querySelectorAll('[data-software-update]').forEach(b=>b.onclick=open));
 return {open};
})();
