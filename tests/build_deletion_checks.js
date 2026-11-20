const fs=require('fs'),vm=require('vm'),assert=require('assert');
let accepted=false,failed=false,notice='',rows=[],buttons=[],requests=[];
const list={innerHTML:'',querySelectorAll:s=>s==='[data-delete-build]'?buttons:[]};
const result={innerHTML:'Latest result',querySelector:()=>true};
const ctx={console,window:{confirm:message=>{assert(message.includes('permanently'));return accepted;}},document:{querySelector:s=>s==='#buildList'?list:s==='#buildResult'?result:null,querySelectorAll:()=>[]}};
vm.createContext(ctx);const source=fs.readFileSync('web/editor.js','utf8');vm.runInContext(source.slice(0,source.indexOf("$('#saveProject').onclick")),ctx);
const run=s=>vm.runInContext(s,ctx);run("project={id:'demo',story:'Unsaved story'};dirty=true;");
ctx.notify=s=>notice=s;
ctx.api=async(path,body)=>{requests.push({path,body});if(path==='/api/builds')return {builds:rows};if(failed)throw Error('File is open');assert.deepEqual(body,{build_id:'b'.repeat(20),confirm:true});rows=rows.filter(b=>b.build_id!==body.build_id);return {deleted:body.build_id};};
// Real task wrapper catches errors and restores buttons. This test's button has no DOM text.
function fixture(){
 rows=[{build_id:'a'.repeat(20),project_id:'demo',title:'Old <build>',module:'demo.mod',areas:3},{build_id:'b'.repeat(20),project_id:'demo',title:'New build',module:'demo.mod',areas:3},{build_id:'c'.repeat(20),project_id:'another',title:'Hidden build',module:'hidden.mod',areas:3}];
 buttons=rows.slice(0,2).map(b=>({dataset:{deleteBuild:b.build_id},disabled:false}));
}
(async()=>{
 fixture();await ctx.builds();assert.equal((list.innerHTML.match(/Delete build/g)||[]).length,2);assert(!list.innerHTML.includes('Hidden build'));assert(list.innerHTML.includes('Old &lt;build&gt;'));
 requests=[];const draft=run('JSON.stringify(project)');await buttons[1].onclick();assert.equal(requests.length,0);assert.equal(rows.length,3);
 accepted=true;failed=true;await buttons[1].onclick();assert.equal(rows.length,3);assert.equal(notice,'File is open');assert(!buttons[1].disabled);
 failed=false;await buttons[1].onclick();assert(!list.innerHTML.includes('New build'));assert(list.innerHTML.includes('Latest export'));assert.equal(result.innerHTML,'');
 assert.equal(run('JSON.stringify(project)'),draft);assert(run('dirty'));assert(!buttons[1].disabled);
 rows=[];await ctx.builds();assert(list.innerHTML.includes('No builds yet'));
 // A late response for a different selected project must not repaint this page.
 list.innerHTML='Keep this';ctx.api=async()=>{run("project.id='switched'");return {builds:[]};};await ctx.builds();assert.equal(list.innerHTML,'Keep this');
 console.log('Build deletion confirmation, cancellation, failure, refresh, empty state and draft preservation passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
