const fs=require('fs'),vm=require('vm'),assert=require('assert');
const ctx={window:{},console};vm.createContext(ctx);
// Expose the pure renderers in the test VM, without changing the browser API.
vm.runInContext(fs.readFileSync('web/analyser.js','utf8').replace('return {mount};','return {mount,card,overview};'),ctx);
const {card,overview}=ctx.window.ModuleAnalyser,attack='<img src=x onerror="alert(1)">';
const npc={name:attack,source:'keep.git/Creature List[0]',kind:'placed',area:'keep',tag:attack,description:attack,conversation:'talk',inferred_role:[],classes:[],inventory:[],position:{},script_refs:[attack]};
const output=card(npc,'characters');assert(!output.includes('<img'));assert(output.includes('&lt;img'));assert(output.includes('data-script="&lt;img'));assert(output.includes('placed'));
const quest={name:'Quest',source:'module.jrl',tag:'seal',entries:[{id:10,text:attack,end:false,source:'module.jrl/EntryList[0]'}],script_evidence:[{script:'reward',finding:'Matching string literal only; inferred.'}]};
assert(!card(quest,'quests').includes('<img'));assert(card(quest,'quests').includes('Matching string literal only'));
const script={id:'reward',status:'partial',instructions:12,source_available:false,debug_available:false,categories:{journal:1},warnings:['Unsupported opcode']};
assert(card(script,'scripts').includes('Source absent'));assert(card(script,'scripts').includes('Unsupported opcode'));
const report={counts:{areas:1},module:{name:attack},story:{overview:attack,note:'Recovered text',evidence:[],evidence_total:0},warnings:[attack],limitations:['Static inspection only'],resource_types:{are:1},lore:[],ai_explanation:{note:'Inference',provider:'test',model:'test',claims:[{topic:attack,text:attack,evidence_ids:['E1']}],evidence:[{id:'E1',kind:'Module',source:'module.ifo',data:attack}],uncertainties:[attack]}};
assert(!overview(report).includes('<img'));assert(overview(report).includes('module.ifo'));assert(overview(report).includes('Inference'));
// Opening the analyser with a dirty draft must preserve it and disable editing actions.
const els={};function el(){return {disabled:false,hidden:false,innerHTML:'',textContent:'',classList:{remove(){}}};}
const editor={document:{querySelector:s=>els[s]??=el(),querySelectorAll:()=>[]},ModuleAnalyser:{mount(){editor.mounted=true;}}};vm.createContext(editor);
const code=fs.readFileSync('web/editor.js','utf8');vm.runInContext(code.slice(0,code.indexOf("$('#saveProject').onclick")),editor);
vm.runInContext("project={id:'keep_this',areas:[],title:'Unsaved adventure'};dirty=true;page='analyser';render();",editor);
assert(editor.mounted);assert.equal(vm.runInContext('project.id',editor),'keep_this');assert.equal(vm.runInContext('dirty',editor),true);assert(els['#saveProject'].disabled);assert(els['#deleteProject'].disabled);assert(els['#reviewProject'].disabled);
vm.runInContext('project=null;render();',editor);assert(els['nav[aria-label="Authoring workflow"]'].hidden);
console.log('Module analyser: escaped untrusted content, qualified evidence, source-absent scripts, and read-only draft preservation passed.');
