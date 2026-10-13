
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.179.1/+esm';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.179.1/examples/jsm/controls/OrbitControls.js/+esm';

const app=document.getElementById('world');
const tier=document.getElementById('qualityTier')?.value||'ADAPTIVE';
const lite=tier==='LITE';
const hero=document.getElementById('heroCopy');
const drawer=document.getElementById('drawer');
const drawerContent=document.getElementById('drawerContent');
const drawerClose=document.getElementById('drawerClose');
function closeDrawer(){drawer.classList.remove('open');drawer.setAttribute('aria-hidden','true');hero.classList.remove('fade')}
drawerClose.addEventListener('click',closeDrawer);
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDrawer()});
const toast=document.getElementById('toast');
const video=document.getElementById('bgVideo');
video.addEventListener('error',()=>{video.style.display='none';toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),4200)});
// Cinematic media is disabled in the public shell and never auto-loaded.

const scene=new THREE.Scene();
scene.fog=new THREE.FogExp2(0x05030a,lite?.012:.015);
const mobileView=()=>innerWidth<=760;
const camera=new THREE.PerspectiveCamera(52,innerWidth/innerHeight,.1,1000); camera.position.set(0,52,86);
const renderer=new THREE.WebGLRenderer({alpha:true,antialias:true,powerPreference:'high-performance'}); renderer.setPixelRatio(Math.min(devicePixelRatio,lite?1:tier==='FULL'?2:1.5)); renderer.setSize(innerWidth,innerHeight); renderer.outputColorSpace=THREE.SRGBColorSpace; renderer.toneMapping=THREE.ACESFilmicToneMapping; renderer.toneMappingExposure=1.15; renderer.setClearColor(0x000000,0); app.appendChild(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement); controls.enableDamping=true; controls.dampingFactor=.05; controls.target.set(0,4,0); controls.minDistance=42; controls.maxDistance=180; controls.maxPolarAngle=Math.PI*.46; controls.minPolarAngle=Math.PI*.20;
scene.add(new THREE.HemisphereLight(0x84ddff,0x120817,2.15));
const key=new THREE.DirectionalLight(0xff2a2a,2.3);key.position.set(-35,50,30);scene.add(key);
const fill=new THREE.PointLight(0x19e6e6,4.2,160);fill.position.set(35,30,25);scene.add(fill);

const floor=new THREE.Mesh(new THREE.PlaneGeometry(150,150),new THREE.MeshStandardMaterial({color:0x070a12,metalness:.75,roughness:.35,transparent:true,opacity:.68}));floor.rotation.x=-Math.PI/2;floor.position.y=-.3;scene.add(floor);
const grid=new THREE.GridHelper(112,28,0x19e6e6,0x32152f);grid.position.y=-.26;grid.material.opacity=.18;grid.material.transparent=true;scene.add(grid);

const DATA=[
{id:'identity',name:'IDENTITY TOWER',role:'Who is acting?',x:-30,z:14,color:0x19e6e6,h:22,shape:'tower',href:'./docs/kernel-spec-v0.1.md'},
{id:'mandate',name:'MANDATE FORGE',role:'What is allowed?',x:-16,z:-4,color:0xff2941,h:15,shape:'forge',href:'./contracts/core/execution-envelope.schema.json'},
{id:'policy',name:'POLICY GATE',role:'What constraints apply?',x:0,z:-15,color:0xff2941,h:11,shape:'gate',href:'./docs/COGNITIVE_RUNTIME_NAMESPACE_GUARD.md'},
{id:'capability',name:'CAPABILITY EXCHANGE',role:'What can the agent do?',x:20,z:-8,color:0x19e6e6,h:14,shape:'ring',href:'./contracts/core/capability-abi.md'},
{id:'atranic',name:'ATRANIC HUB',role:'What does the message mean?',x:30,z:10,color:0x19e6e6,h:18,shape:'spire',href:'./docs/ATG-PROFILE-LANGUAGE.md'},
{id:'atralith',name:'ATRALITH CORE',role:'Reference implementation',x:18,z:28,color:0xff2a2a,h:24,shape:'core',href:'./atralith/'},
{id:'mcp',name:'MCP TERMINAL',role:'Governed tool execution',x:-2,z:31,color:0x19e6e6,h:16,shape:'terminal',href:'https://agentropolis-city-of-agents.github.io/AGENTROPOLIS-AGENT-MCP/'},
{id:'verify',name:'VERIFY SPIRE',role:'What actually happened?',x:-22,z:28,color:0xa24bff,h:21,shape:'spire',href:'./docs/ATG-PROFILE-VERIFY.md'},
{id:'receipt',name:'RECEIPT ARCHIVE',role:'What proof remains?',x:-34,z:-12,color:0x3dff9e,h:13,shape:'archive',href:'./examples/'},
{id:'core',name:'ATG CORE',role:'Semantic contract layer',x:0,z:7,color:0xffffff,h:10,shape:'core',href:'https://github.com/AGENTROPOLIS-CITY-OF-AGENTS/AGENTROPOLIS-ATG'}
];
const groups=new Map();
// Architectural city district: actual buildings, podiums, windows, roof equipment and streets.
function mat(c,intensity=.55){return new THREE.MeshStandardMaterial({color:0x101a23,metalness:.78,roughness:.34,emissive:c,emissiveIntensity:intensity*.12})}
const facade=new THREE.MeshStandardMaterial({color:0x111b25,metalness:.68,roughness:.39});
const glass=new THREE.MeshStandardMaterial({color:0x123a48,metalness:.68,roughness:.18,emissive:0x086478,emissiveIntensity:.19});
const trimCyan=new THREE.MeshBasicMaterial({color:0x19e6e6});
const trimRed=new THREE.MeshBasicMaterial({color:0xff2a2a});
function block(g,w,h,depth,x,y,z,material=facade){
 const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,depth),material);
 mesh.position.set(x,y,z);g.add(mesh);return mesh;
}
function addNode(d){
 const g=new THREE.Group();g.position.set(d.x,0,d.z);
 const accent=(d.color===0xff2941||d.color===0xff2a2a)?trimRed:trimCyan;
 const h=d.h,wide=d.shape==='forge'||d.shape==='archive'||d.shape==='terminal';
 const w=wide?10:7.6,depth=wide?9:7.6;
 // Raised podium, articulated skyscraper silhouette, setback upper floors.
 block(g,w+3,1.2,depth+3,0,.6,0,mat(d.color,.28));
 const main=block(g,w,h*.73,depth,0,1.2+h*.365,0,facade);
 main.userData.node=d;
 block(g,w*.72,h*.27,depth*.72,0,1.2+h*.865,0,glass);
 block(g,w*.79,.38,depth*.79,0,1.2+h*.73,0,accent);
 block(g,w*.78,.34,depth*.78,0,1.2+h,0,accent);
 // Distinctive roofline, aerial spire and structural mechanical crown.
 if(d.shape==='spire'||d.shape==='tower'||d.shape==='core'){
   block(g,1.2,4,1.2,0,h+3.1,0,facade);
   block(g,.22,5,.22,0,h+6.7,0,accent);
 } else if(d.shape==='gate'){
   block(g,w+3,2,depth+2,0,h*.6,0,accent);
 } else if(d.shape==='ring'){
   const skybridge=new THREE.Mesh(new THREE.TorusGeometry(5.3,.22,8,48),accent);
   skybridge.rotation.x=Math.PI/2;skybridge.position.y=h*.85;g.add(skybridge);
 }
 // Four facade sides with individually visible window strips and mullions.
 const rows=Math.max(lite?3:5,Math.floor(h/(lite?4.5:2.25)));
 for(let level=0;level<rows;level++){
   const y=2.6+level*(h*.70/rows);
   for(let col=-2;col<=2;col++){
     const x=col*w/6;
     const front=block(g,.55,.72,.09,x,y,depth/2+.07,(level+col)%7===0?accent:glass);
     front.userData.node=d;
     block(g,.55,.72,.09,x,y,-depth/2-.07,glass);
     block(g,.09,.72,.55,w/2+.07,y,col*depth/6,glass);
     block(g,.09,.72,.55,-w/2-.07,y,col*depth/6,glass);
   }
 }
 // Plinth, illuminated entry portal, and a visible building footprint.
 block(g,2.3,3,.18,0,2,depth/2+.18,accent);
 const perimeter=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(w+3,1.2,depth+3)),new THREE.LineBasicMaterial({color:d.color,transparent:true,opacity:.8}));
 perimeter.position.y=.6;g.add(perimeter);
 const beacon=new THREE.Mesh(new THREE.OctahedronGeometry(.3),new THREE.MeshBasicMaterial({color:d.color}));
 beacon.position.y=h+8;g.add(beacon);
 g.userData={data:d,beacon};scene.add(g);groups.set(d.id,g);
}
DATA.forEach(addNode);
if(mobileView()){camera.position.set(0,88,142);controls.target.set(0,6,0)}

const sequence=['identity','mandate','policy','capability','atranic','atralith','mcp','verify','receipt'];
const lineMat=new THREE.LineBasicMaterial({color:0x19e6e6,transparent:true,opacity:.34});
for(let i=0;i<sequence.length-1;i++){const a=DATA.find(x=>x.id===sequence[i]),b=DATA.find(x=>x.id===sequence[i+1]);const pts=[new THREE.Vector3(a.x,.45,a.z),new THREE.Vector3(b.x,.45,b.z)];scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),lineMat))}
const pulse=new THREE.Mesh(new THREE.SphereGeometry(.65,14,14),new THREE.MeshBasicMaterial({color:0x19e6e6}));scene.add(pulse);
let pulseIndex=0,pulseT=0;

const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();
renderer.domElement.addEventListener('pointerdown',e=>{mouse.x=e.clientX/innerWidth*2-1;mouse.y=-(e.clientY/innerHeight)*2+1;ray.setFromCamera(mouse,camera);const hits=ray.intersectObjects([...groups.values()].flatMap(g=>g.children),true);const hit=hits.find(h=>h.object.userData.node);if(hit)show(hit.object.userData.node)});
function show(d){hero.classList.add('fade');drawer.classList.add('open');drawer.setAttribute('aria-hidden','false');drawerContent.innerHTML=`<div class="kicker">ATG PROTOCOL DISTRICT</div><h2>${d.name}</h2><p>${d.role}</p><div class="meta"><div class="chip">SURFACE<b>AVAILABLE</b></div><div class="chip">RUNTIME<b>DEMO</b></div><div class="chip">FLOW<b>${sequence.includes(d.id)?'CORRIDOR':'SUPPORT'}</b></div><div class="chip">AUTHORITY<b>BOUNDED</b></div></div><a href="${d.href}">OPEN SOURCE ↗</a>`;focus(d.id)}
function focus(id){const g=groups.get(id);if(!g)return;controls.target.copy(g.position).add(new THREE.Vector3(0,5,0));const dir=mobileView()?new THREE.Vector3(0,40,75):new THREE.Vector3(0,22,38);camera.position.copy(g.position).add(dir)}
document.querySelectorAll('[data-focus]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-focus]').forEach(x=>x.classList.remove('active'));b.classList.add('active');if(b.dataset.focus==='core'){closeDrawer();controls.target.set(0,4,0);camera.position.set(0,mobileView()?88:52,mobileView()?142:86)}else{const d=DATA.find(x=>x.id===b.dataset.focus);if(d)show(d)}}));

let touring=false,tourStep=0,lastStep=0;document.getElementById('tourBtn').addEventListener('click',()=>{touring=!touring;tourStep=0;lastStep=0;document.getElementById('tourBtn').textContent=touring?'STOP CORRIDOR':'RUN THE CORRIDOR'});
const clock=new THREE.Clock();function animate(){requestAnimationFrame(animate);const t=clock.getElapsedTime();groups.forEach((g,i)=>{g.userData.beacon.rotation.y=t*(.6+i*.03);g.userData.beacon.position.y=g.userData.data.h+8+Math.sin(t*1.4+i)*.4});pulseT=(pulseT+.008)%1;const ai=pulseIndex%(sequence.length-1),a=groups.get(sequence[ai]).position,b=groups.get(sequence[ai+1]).position;pulse.position.lerpVectors(a,b,pulseT);pulse.position.y=.9+Math.sin(t*5)*.2;if(pulseT>.99)pulseIndex++;
 if(touring){if(!lastStep||t-lastStep>3.2){const id=sequence[tourStep%sequence.length];show(DATA.find(x=>x.id===id));tourStep++;lastStep=t;if(tourStep>sequence.length){touring=false;document.getElementById('tourBtn').textContent='RUN THE CORRIDOR'}}}
 controls.update();renderer.render(scene,camera)}animate();
addEventListener('resize',()=>{if(!drawer.classList.contains('open')){camera.position.set(0,mobileView()?88:52,mobileView()?142:86)}camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)});
