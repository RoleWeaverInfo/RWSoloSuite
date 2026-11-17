'use strict';
const statusLine=document.querySelector('#startupStatus'),enter=document.querySelector('#enterStudio');
const player=new URLSearchParams(location.search).get('view')==='player';
let advance,stay=false;
if(player){enter.href='/player';enter.textContent='Open AI service status';}
document.querySelector('#stayOnSplash').onclick=event=>{stay=true;clearTimeout(advance);event.currentTarget.hidden=true;};
(async()=>{
 try{
  const response=await fetch('/api/state');if(!response.ok)throw Error('Service is not ready.');
  const state=await response.json();
  statusLine.textContent='Service '+state.version+' is ready. '+(state.key_available?'Your AI provider is configured.':'Add your OpenAI or Gemini key in Settings to enable AI features.');
  await document.querySelector('#splashArt').decode().catch(()=>{});
  if(!stay)advance=setTimeout(()=>location.replace(enter.getAttribute('href')),4000);
 }catch(error){statusLine.textContent='Unable to reach Role Weaver. Keep its service window open and refresh this page.';}
})();
