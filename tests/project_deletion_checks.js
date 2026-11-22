const fs=require('fs'),vm=require('vm'),assert=require('assert'),els={},requests=[];
function el(){return {disabled:false,value:'',hidden:false,innerHTML:'',focus(){},close(){this.open=false;},click(){this.onclick?.();},classList:{toggle(){}},setAttribute(){}};}
const ctx={console,AISetup:{mount(){}},document:{querySelector:s=>els[s]??=el(),querySelectorAll:()=>[]}};vm.createContext(ctx);
vm.runInContext(fs.readFileSync('web/design.js','utf8'),ctx);
const source=fs.readFileSync('web/editor.js','utf8');vm.runInContext(source.slice(0,source.indexOf("$('#saveProject').onclick")),ctx);
const run=s=>vm.runInContext(s,ctx);let loaded=[],notice='',modalHtml='',binds=0;
ctx.notify=text=>notice=text;ctx.modal=html=>{modalHtml=html;els['#modal']??=el();els['#modal'].open=true;};ctx.bind=()=>binds++;
const saved={id:'saved_id',title:'Old <area>',schema_version:2};
ctx.fixture=saved;
function reset(){
 run("project={id:'edited_unsaved_id',title:'Unsaved title',areas:[],npcs:[],encounters:[],quests:[]};app={projects:[fixture],settings:{},credentials:{}};dirty=true;proposal={proposal:{}};previousDraft={id:'old'};page='world';generating=false;designBusy=false;");
 els['#projectSelect']??=el();els['#projectSelect'].value='saved_id';['#saveProject','#deleteProject','#reviewProject','#newProject','#importProject'].forEach(s=>{els[s]??=el();els[s].disabled=false;});
 requests.length=0;loaded=[];notice='';
}
async function checks(){
 reset();ctx.api=async(path,body)=>{requests.push({path,body});return {deleted:'saved_id',projects:[]};};
 // Confirmation targets the saved selection, not an edited ID, and cancel is inert.
 ctx.requestProjectDeletion();assert(modalHtml.includes('saved_id.json'));assert(modalHtml.includes('Old &lt;area&gt;'));assert(modalHtml.includes('unsaved edits'));assert.equal(requests.length,0);
 els['#cancelProjectDeletion'].onclick();assert.equal(requests.length,0);assert.equal(run('dirty'),true);
 // Last deletion clears every draft/proposal/undo reference and leaves create/import usable.
 await ctx.deleteSavedProject('saved_id');assert.deepEqual(requests,[{path:'/api/project/delete',body:{id:'saved_id',confirm:true}}]);
 assert.equal(run('project'),null);assert.equal(run('previousDraft'),null);assert.equal(run('proposal'),null);assert.equal(run('dirty'),false);
 assert(els['#workspace'].innerHTML.includes('No projects yet'));assert(els['#saveProject'].disabled);assert(els['#deleteProject'].disabled);assert(els['#projectSelect'].disabled);assert(!els['#newProject'].disabled);assert(!els['#importProject'].disabled);assert(!els['nav[aria-label="Authoring workflow"]'].hidden);
 run("page='settings'");ctx.render();assert(els['#workspace'].innerHTML.includes('providerSetup'));assert.equal(binds,1);
 // An unsuccessful deletion retains the selected project and its unsaved changes.
 reset();const before=run('JSON.stringify(project)');ctx.api=async()=>{throw Error('Permission denied');};
 await assert.rejects(()=>ctx.deleteSavedProject('saved_id'),/Permission denied/);assert.equal(run('JSON.stringify(project)'),before);assert.equal(run('dirty'),true);assert(!els['#saveProject'].disabled);
 // The next saved project loads without saving the deleted draft.
 reset();ctx.api=async(path,body)=>{requests.push({path,body});return {deleted:'saved_id',projects:[{id:'next_id',title:'Next project',schema_version:2}]};};
 ctx.load=async id=>{loaded.push(id);run("project={id:'next_id',title:'Next project',areas:[],npcs:[],encounters:[],quests:[]};dirty=false;");ctx.renderHeader();};
 await ctx.deleteSavedProject('saved_id');assert.deepEqual(loaded,['next_id']);assert.equal(requests.length,1);assert.equal(els['#projectSelect'].value,'next_id');assert(!els['#deleteProject'].disabled);assert(!els['nav[aria-label="Authoring workflow"]'].hidden);
 reset();run('generating=true');await assert.rejects(()=>ctx.deleteSavedProject('saved_id'),/Wait/);assert.equal(requests.length,0);
 console.log('Project deletion confirmation, cancellation, state cleanup, failures, next project and empty settings passed.');
}
checks().catch(e=>{console.error(e);process.exitCode=1;});
