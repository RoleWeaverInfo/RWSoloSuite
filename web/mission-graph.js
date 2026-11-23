/* Source-independent graph viewport. Authoring and future import adapters supply
   nodes and edges; this component never edits or executes mission definitions. */
window.MissionGraph=(()=>{
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const short=(s,n=34)=>String(s||'').length>n?String(s).slice(0,n-1)+'…':String(s||'');
  function layout(graph){
    const nodes=graph.nodes.map(n=>({...n})),byId=new Map(nodes.map(n=>[n.id,n]));
    const incoming=new Map(nodes.map(n=>[n.id,0])),rank=new Map(nodes.map(n=>[n.id,0]));
    for(const e of graph.edges)if(byId.has(e.from)&&byId.has(e.to))incoming.set(e.to,incoming.get(e.to)+1);
    const queue=nodes.filter(n=>!incoming.get(n.id)).map(n=>n.id),done=new Set();
    while(queue.length){const id=queue.shift();done.add(id);for(const e of graph.edges.filter(e=>e.from===id&&byId.has(e.to))){rank.set(e.to,Math.max(rank.get(e.to),rank.get(id)+1));incoming.set(e.to,incoming.get(e.to)-1);if(!incoming.get(e.to))queue.push(e.to);}}
    // Invalid cyclic drafts remain visible and editable without a layout loop.
    let fallback=Math.max(0,...rank.values())+1;
    for(const n of nodes)if(!done.has(n.id))rank.set(n.id,fallback++);
    const rows=new Map();for(const n of nodes){const col=rank.get(n.id),row=rows.get(col)||0;rows.set(col,row+1);Object.assign(n,{x:35+col*350,y:40+row*155,width:260,height:104});}
    return {nodes,edges:graph.edges.filter(e=>byId.has(e.from)&&byId.has(e.to)),width:Math.max(500,...nodes.map(n=>n.x+295)),height:Math.max(300,...nodes.map(n=>n.y+145))};
  }
  function drawing(g,selected){
    const byId=new Map(g.nodes.map(n=>[n.id,n]));
    return `<defs><marker id="missionArrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#7cadd1"/></marker></defs>`+
      g.edges.map((e,i)=>{
        const a=byId.get(e.from),b=byId.get(e.to),x=a.x+a.width,y=a.y+a.height/2,tx=b.x,ty=b.y+b.height/2,bend=Math.max(40,Math.abs(tx-x)/2);
        // Choices may intentionally rejoin the same objective. Keep both arrows
        // and their labels selectable instead of painting them on top of each other.
        const parallel=g.edges.filter(other=>other.from===e.from&&other.to===e.to);
        const lane=(parallel.indexOf(e)-(parallel.length-1)/2)*48;
        const path=`M${x} ${y} C${x+bend} ${y+lane*4/3},${tx-bend} ${ty+lane*4/3},${tx} ${ty}`;
        return `<g class="mission-edge ${e.optional?'optional':''}" data-edge="${i}" role="button" tabindex="0" aria-label="${esc(e.label||'Next objective')}: ${esc(a.label)} to ${esc(b.label)}"><title>${esc(e.label||'Next')} · ${esc(a.label)} → ${esc(b.label)}</title><path class="edge-hit" d="${path}"/><path class="edge-line" marker-end="url(#missionArrow)" d="${path}"/><text x="${(x+tx)/2}" y="${(y+ty)/2+lane-12}" text-anchor="middle">${esc(short(e.label,27))}</text></g>`;
      }).join('')+
      g.nodes.map((n,i)=>`<g class="mission-node ${n.kind==='choice'?'decision':''} ${n.invalid?'invalid':''} ${selected===n.id?'selected':''}" data-node="${i}" transform="translate(${n.x} ${n.y})" role="button" tabindex="0" aria-label="${esc(n.label)}${n.badge?' · '+esc(n.badge):''}"><title>${esc(n.label)}${n.lines?.length?' — '+esc(n.lines.join(' · ')):''}</title><rect width="260" height="104" rx="10"/><text class="node-badge" x="16" y="22">${esc(short(n.badge||n.kind,35))}</text><text class="node-title" x="16" y="48">${esc(short(n.label,29))}</text>${(n.lines||[]).slice(0,2).map((s,j)=>`<text class="node-detail" x="16" y="${70+j*17}">${esc(short(s,36))}</text>`).join('')}</g>`).join('');
  }
  function mount(host,{onSelect,onEdge,onZoom=()=>{},view={}}){
    host.innerHTML='<svg class="mission-canvas" role="group" aria-label="Visual mission map" tabindex="0"></svg>';
    const svg=host.querySelector('svg');let g=layout({nodes:[],edges:[]}),selected='',drag=null;
    view.x??=0;view.y??=0;view.scale??=1;
    function paintView(){svg.setAttribute('viewBox',`${view.x} ${view.y} ${Math.max(1,host.clientWidth)/view.scale} ${Math.max(1,host.clientHeight)/view.scale}`);onZoom(Math.round(view.scale*100));}
    function fit(){view.scale=Math.max(.08,Math.min(1.2,host.clientWidth/g.width,host.clientHeight/g.height));view.x=(g.width-host.clientWidth/view.scale)/2;view.y=(g.height-host.clientHeight/view.scale)/2;paintView();}
    function zoom(factor,px=host.clientWidth/2,py=host.clientHeight/2){const old=view.scale;view.scale=Math.max(.08,Math.min(2.5,old*factor));view.x+=px/old-px/view.scale;view.y+=py/old-py/view.scale;paintView();}
    function focus(id=selected){const n=g.nodes.find(n=>n.id===id)||g.nodes[0];if(!n)return;view.scale=Math.max(.85,view.scale);view.x=n.x+n.width/2-host.clientWidth/view.scale/2;view.y=n.y+n.height/2-host.clientHeight/view.scale/2;paintView();}
    function activate(target){const n=target.closest('[data-node]'),e=target.closest('[data-edge]');if(n)onSelect(g.nodes[Number(n.dataset.node)]);else if(e)onEdge?.(g.edges[Number(e.dataset.edge)]);}
    svg.addEventListener('click',e=>activate(e.target));
    svg.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){if(e.target.closest('[data-node],[data-edge]')){e.preventDefault();activate(e.target);}}else if(e.target===svg){const moves={ArrowLeft:[-60,0],ArrowRight:[60,0],ArrowUp:[0,-60],ArrowDown:[0,60]};if(moves[e.key]){e.preventDefault();view.x+=moves[e.key][0]/view.scale;view.y+=moves[e.key][1]/view.scale;paintView();}}});
    svg.addEventListener('pointerdown',e=>{if(e.button!==0||e.target.closest('[data-node],[data-edge]'))return;drag={x:e.clientX,y:e.clientY,vx:view.x,vy:view.y};svg.setPointerCapture(e.pointerId);svg.classList.add('panning');});
    svg.addEventListener('pointermove',e=>{if(!drag)return;view.x=drag.vx-(e.clientX-drag.x)/view.scale;view.y=drag.vy-(e.clientY-drag.y)/view.scale;paintView();});
    const end=()=>{drag=null;svg.classList.remove('panning');};svg.addEventListener('pointerup',end);svg.addEventListener('pointercancel',end);
    svg.addEventListener('wheel',e=>{if(!e.ctrlKey&&!e.metaKey)return;e.preventDefault();const r=svg.getBoundingClientRect();zoom(e.deltaY<0?1.12:1/1.12,e.clientX-r.left,e.clientY-r.top);},{passive:false});
    const resize=new ResizeObserver(paintView);resize.observe(host);
    return {setGraph(graph,id,autoFit=false){g=layout(graph);selected=id;svg.innerHTML=drawing(g,selected);if(autoFit){fit();if(view.scale<.65)focus();}else paintView();},fit,zoom,focus,destroy(){resize.disconnect();}};
  }
  return {layout,drawing,mount};
})();
