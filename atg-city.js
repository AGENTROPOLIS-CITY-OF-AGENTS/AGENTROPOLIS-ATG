import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.179.1/+esm';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.179.1/examples/jsm/controls/OrbitControls.js/+esm';
const app=document.getElementById('world'),stage=app.parentElement;
const reduced=matchMedia('(prefers-reduced-motion: reduce)');let paused=reduced.matches;
addEventListener('atg:motion',e=>paused=e.detail.paused);
const scene=new THREE.Scene();scene.background=new THREE.Color(0x05070a);scene.fog=new THREE.Fog(0x05070a,120,240);
const camera=new THREE.PerspectiveCamera(48,1,.1,350);camera.position.set(72,64,94);
const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'low-power'});renderer.setPixelRatio(Math.min(devicePixelRatio,1.6));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.55;app.appendChild(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.target.set(0,7,6);controls.minDistance=25;controls.maxDistance=155;controls.maxPolarAngle=Math.PI*.47;controls.minPolarAngle=.3;
scene.add(new THREE.HemisphereLight(0xd5f5ff,0x182029,3));const sun=new THREE.DirectionalLight(0xeafaff,3.1);sun.position.set(30,70,35);scene.add(sun);const redLight=new THREE.PointLight(0xff2a2a,45,70,2);redLight.position.set(-25,12,20);scene.add(redLight);
const CY=0x19e6e6,RD=0xff2a2a,groups=new Map(),pickable=[];
const data=[
{id:'identity',name:'IDENTITY TOWER',glyph:'IR',x:-31,z:10,h:24,type:'tower',color:CY},
{id:'mandate',name:'MANDATE FORGE',glyph:'MOR',x:-18,z:-13,h:12,type:'forge',color:RD},
{id:'policy',name:'AEGIS POLICY GATE',glyph:'PRA',x:2,z:-24,h:11,type:'gate',color:RD},
{id:'capability',name:'CAPABILITY EXCHANGE',glyph:'RHE',x:24,z:-13,h:13,type:'exchange',color:CY},
{id:'atranic',name:'ATRAL SCRIPT LIBRARY',glyph:'KOR',x:33,z:10,h:19,type:'library',color:CY},
{id:'atralith',name:'ATRALITH CORE',glyph:'SYN',x:20,z:31,h:25,type:'core',color:RD},
{id:'mcp',name:'MCP TERMINAL',glyph:'XEN',x:-1,z:36,h:12,type:'terminal',color:CY},
{id:'verify',name:'VERITY OBSERVATORY',glyph:'ESH',x:-23,z:31,h:26,type:'observe',color:CY},
{id:'receipt',name:'RECEIPT ARCHIVE',glyph:'DOR',x:-35,z:-15,h:12,type:'archive',color:CY},
{id:'core',name:'ATG CIVIC ATRIUM',glyph:'AR',x:0,z:7,h:10,type:'atrium',color:CY}
];
function material(color,extra={}){return new THREE.MeshStandardMaterial({color,roughness:.55,metalness:.3,...extra});}
const stone=material(0x28343f),trim=material(0x4e606a),roof=material(0x111922),glass=material(0x102e39,{metalness:.75,roughness:.2}),ground=material(0x0e151c),sidewalk=material(0x26333e);
function facade(accent,brick=false){const c=document.createElement('canvas');c.width=256;c.height=512;const x=c.getContext('2d');x.fillStyle=brick?'#27303a':'#15252f';x.fillRect(0,0,256,512);if(brick){x.strokeStyle='#4d5561';for(let y=0;y<512;y+=16){x.beginPath();x.moveTo(0,y);x.lineTo(256,y);x.stroke();for(let a=(y%32?0:16);a<256;a+=32){x.beginPath();x.moveTo(a,y);x.lineTo(a,y+16);x.stroke();}}}for(let row=0;row<16;row++)for(let col=0;col<6;col++){x.fillStyle=(row+col)%7===0?'#d7c392':accent===RD?'#ab545b':'#4cbacb';x.fillRect(10+col*41,9+row*32,27,21);x.fillStyle='#09141b';x.fillRect(10+col*41,19+row*32,27,2);x.fillRect(22+col*41,9+row*32,2,21);}const tex=new THREE.CanvasTexture(c);tex.colorSpace=THREE.SRGBColorSpace;return material(0xffffff,{map:tex,emissiveMap:tex,emissive:0xffffff,emissiveIntensity:.22});}
const cyanFacade=facade(CY),redFacade=facade(RD),brickFacade=facade(RD,true);
function box(g,w,h,d,x=0,y=h/2,z=0,mat=stone){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);m.position.set(x,y,z);g.add(m);return m;}
function cylinder(g,r1,r2,h,x=0,y=h/2,z=0,mat=trim,n=24){const m=new THREE.Mesh(new THREE.CylinderGeometry(r1,r2,h,n),mat);m.position.set(x,y,z);g.add(m);return m;}
function signal(g,w,h,d,x,y,z,color){return box(g,w,h,d,x,y,z,material(color,{emissive:color,emissiveIntensity:1.4}));}
function sign(g,label,y,z,w=15){const c=document.createElement('canvas');c.width=1024;c.height=128;const x=c.getContext('2d');x.fillStyle='#05070a';x.fillRect(0,0,1024,128);x.strokeStyle='#19e6e6';x.lineWidth=6;x.strokeRect(3,3,1018,122);x.fillStyle='#dffbff';x.font='bold 52px monospace';x.textAlign='center';x.textBaseline='middle';x.fillText(label,512,64);const tex=new THREE.CanvasTexture(c);tex.colorSpace=THREE.SRGBColorSpace;const m=new THREE.Mesh(new THREE.PlaneGeometry(w,w/8),new THREE.MeshBasicMaterial({map:tex}));m.position.set(0,y,z);g.add(m);}
function lobby(g,width,z,color){box(g,width,3,.18,0,1.7,z,glass);for(let x=-width/2;x<=width/2;x+=width/4)box(g,.12,3,.25,x,1.7,z+.1,trim);signal(g,width+.5,.2,.5,0,3.3,z+.2,color);box(g,width+2,.25,2.2,0,3.8,z+.8,roof);for(let i=0;i<3;i++)box(g,width+2+i*.5,.18,1.2,0,.1+i*.15,z+1.5-i*.4,sidewalk);}
function tier(g,w,h,d,y,mat){box(g,w,h,d,0,y+h/2,0,mat);box(g,w+.4,.4,d+.4,0,y+h,0,trim);}
function pitch(g,w,d,y){const verts=new Float32Array([-w/2,y,-d/2,w/2,y,-d/2,0,y+3,-d/2,-w/2,y,d/2,w/2,y,d/2,0,y+3,d/2]);const geom=new THREE.BufferGeometry();geom.setAttribute('position',new THREE.BufferAttribute(verts,3));geom.setIndex([0,2,1,3,4,5,0,3,5,0,5,2,1,2,5,1,5,4]);geom.computeVertexNormals();g.add(new THREE.Mesh(geom,roof));}
function architecture(d){const g=new THREE.Group();g.position.set(d.x,0,d.z);g.userData.data=d;
box(g,17,.5,17,0,.15,0,sidewalk);
if(d.type==='tower'||d.type==='observe'){tier(g,12,4,12,.5,stone);tier(g,9,14,9,4.5,cyanFacade);tier(g,7,7,7,18.5,cyanFacade);lobby(g,6,6.15,d.color);for(let y=6;y<25;y+=3)box(g,9.3,.16,9.3,0,y,0,trim);if(d.type==='observe'){cylinder(g,5,5,1.2,0,26.5,0,trim);cylinder(g,3,3,2,0,28,0,glass);const dome=new THREE.Mesh(new THREE.SphereGeometry(3,24,12,0,Math.PI*2,0,Math.PI/2),glass);dome.position.y=29;g.add(dome);}else{box(g,3,2,3,0,26.3,0,roof);cylinder(g,.08,.08,5,0,29.5,0,trim);}}
else if(d.type==='forge'){tier(g,14,8,10,.5,brickFacade);pitch(g,14.6,10.6,8.5);lobby(g,5,5.2,RD);for(let i=0;i<3;i++){cylinder(g,.7,1,6,-5+i*3,11,-2,trim);box(g,2,2,.2,4,2.5,5.3,glass);}sign(g,'MOR / MANDATE',6.6,5.4,12);}
else if(d.type==='gate'){for(const x of [-5,5]){box(g,4,10,9,x,5.5,0,redFacade);box(g,4.5,.5,9.5,x,10.7,0,roof);lobby(g,2,4.7,RD);}box(g,14,3,6,0,10,0,redFacade);box(g,14,.4,6.5,0,11.6,0,trim);signal(g,7,.25,.3,0,3.4,4.5,RD);sign(g,'PRA / AEGIS',10.3,3.1,12);for(let x=-3;x<=3;x+=2)box(g,.18,2,.18,x,1,5.5,trim);}
else if(d.type==='exchange'){cylinder(g,7,7,2,0,1.2,0,stone);cylinder(g,6.5,6.5,10,0,7,0,cyanFacade,32);for(let i=0;i<12;i++){const a=i/12*Math.PI*2;cylinder(g,.2,.2,10,Math.sin(a)*6.8,7,Math.cos(a)*6.8,trim);}cylinder(g,7.2,7.2,.6,0,12.4,0,trim);const dome=new THREE.Mesh(new THREE.SphereGeometry(6.4,32,16,0,Math.PI*2,0,Math.PI/2),glass);dome.scale.y=.5;dome.position.y=12.5;g.add(dome);lobby(g,4,6.8,CY);sign(g,'RHE / EXCHANGE',4.8,7,12);}
else if(d.type==='library'){tier(g,13,4,12,.5,stone);tier(g,12,13,10,4.5,cyanFacade);box(g,9,2,8,0,18.5,-1,roof);for(let x=-5;x<=5;x+=2)box(g,.25,13,.4,x,11,5.2,trim);lobby(g,7,6.3,CY);sign(g,'KOR / ATRAL SCRIPT',6,5.7,14);}
else if(d.type==='core'){tier(g,14,4,12,.5,stone);for(const x of [-4,4]){box(g,5,20,8,x,14.5,0,x<0?redFacade:cyanFacade);box(g,5.5,.5,8.5,x,24.8,0,trim);}box(g,5,2,4,0,15,0,glass);box(g,5,2,4,0,21,0,glass);lobby(g,7,6.2,RD);sign(g,'SYN / ATRALITH',5.8,6.4,14);}
else if(d.type==='terminal'){tier(g,15,5,10,.5,cyanFacade);const canopy=new THREE.Mesh(new THREE.CylinderGeometry(5,5,16,24,1,true,0,Math.PI),glass);canopy.rotation.z=Math.PI/2;canopy.rotation.x=Math.PI/2;canopy.position.set(0,5.5,0);g.add(canopy);for(let x=-7;x<=7;x+=3.5)box(g,.25,5,.25,x,2.7,5,trim);lobby(g,9,5.3,CY);sign(g,'XEN / MCP TERMINAL',4.3,5.7,15);}
else if(d.type==='archive'){tier(g,15,9,11,.5,stone);box(g,15.8,1,11.8,0,10,0,trim);for(let x=-6;x<=6;x+=2)cylinder(g,.35,.45,8,x,4.7,5.8,trim);box(g,16,1,2,0,9,6,trim);lobby(g,5,5.7,CY);sign(g,'DOR / RECEIPTS',11.4,6,14);for(let x of [-5,5])box(g,2,4,.1,x,5,5.6,cyanFacade);}
else{cylinder(g,8,8,1,0,.7,0,stone);tier(g,11,7,10,1.2,cyanFacade);box(g,12,.5,11,0,8.5,0,trim);lobby(g,7,5.3,CY);sign(g,'AR / ATG',9.8,5.8,10);}
const roofHeight=d.type==='tower'?27:d.type==='observe'?31:d.h+2;
const c=document.createElement('canvas');c.width=1024;c.height=160;const x=c.getContext('2d');x.fillStyle='#05070aee';x.fillRect(0,0,1024,160);x.fillStyle='#19e6e6';x.font='bold 42px monospace';x.textAlign='center';x.fillText(d.name,512,62);x.fillStyle='#e9faff';x.font='30px monospace';x.fillText(d.glyph+' / '+(d.id==='atranic'?'ATRALITH LANGUAGE':'ATG DISTRICT'),512,115);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;const sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:t,depthTest:false}));sprite.scale.set(18,2.8,1);sprite.position.set(0,roofHeight+3,0);g.add(sprite);
g.traverse(obj=>{if(obj.isMesh){obj.userData.node=d;pickable.push(obj);}});scene.add(g);groups.set(d.id,g);
}
// Urban circulation: street slabs, pavements, crossings, street lamps, and planted squares.
const city=new THREE.Group();scene.add(city);box(city,104,.3,106,0,-.4,5,ground);
for(const z of [-4,23]){box(city,102,.05,6,0,-.1,z,material(0x080d13));for(const side of [-1,1]){box(city,102,.15,1.1,0,.05,z+side*3.6,sidewalk);for(let x=-44;x<=44;x+=5)box(city,2,.025,.15,x,-.04,z,trim);}}
for(const x of [-11,12]){box(city,6,.04,100,x,-.05,5,material(0x080d13));for(const side of [-1,1])box(city,1,.12,100,x+side*3.6,.05,5,sidewalk);}
for(const x of [-11,12])for(const z of [-4,23])for(let k=-2;k<=2;k++)box(city,3,.03,.3,x,.04,z+k*.65,trim);
for(let x=-42;x<=42;x+=14)for(const z of [-8,27]){cylinder(city,.12,.15,4,x,2,z,trim);box(city,1.3,.15,.5,x,4,z,material(CY,{emissive:CY,emissiveIntensity:2}));}
for(const [x,z] of [[-45,2],[-44,29],[43,29],[43,-23],[-4,-14],[9,15]]){box(city,3,.4,3,x,.2,z,stone);cylinder(city,.25,.35,2,x,1.3,z,trim);const tree=new THREE.Mesh(new THREE.IcosahedronGeometry(1.7,1),material(0x265b48));tree.position.set(x,3,z);city.add(tree);}
data.forEach(architecture);
// Source glyph artwork mounted on real library and core façades.
fetch('./atg-glyphs.json').then(r=>{if(!r.ok)throw Error('Glyph assets unavailable');return r.json();}).then(glyphs=>{for(const id of ['atranic','atralith']){const g=groups.get(id),record=data.find(d=>d.id===id),art=glyphs.find(a=>a.n===record.glyph);if(!art)continue;new THREE.TextureLoader().load(art.src,texture=>{texture.colorSpace=THREE.SRGBColorSpace;const panel=new THREE.Mesh(new THREE.PlaneGeometry(2.8,3.6),new THREE.MeshBasicMaterial({map:texture}));panel.position.set(0,id==='atranic'?11:10,5.55);g.add(panel);});}}).catch(()=>{});
let down=null;const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();renderer.domElement.addEventListener('pointerdown',e=>down={x:e.clientX,y:e.clientY});renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down.x,e.clientY-down.y)>6){down=null;return;}down=null;const r=renderer.domElement.getBoundingClientRect();mouse.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);ray.setFromCamera(mouse,camera);const hit=ray.intersectObjects(pickable,false)[0];if(hit)dispatchEvent(new CustomEvent('atg:select',{detail:{id:hit.object.userData.node.id}}));});renderer.domElement.addEventListener('pointercancel',()=>down=null);
function focus(id){const g=groups.get(id);if(!g)return;if(id==='core'){controls.target.set(0,7,6);camera.position.set(72,64,94);}else{controls.target.copy(g.position).add(new THREE.Vector3(0,8,0));camera.position.copy(g.position).add(new THREE.Vector3(24,29,42));}controls.update();}
addEventListener('atg:focus',e=>focus(e.detail.id));const sequence=['identity','mandate','policy','capability','atranic','atralith','mcp','verify','receipt'];const pulse=new THREE.Mesh(new THREE.SphereGeometry(.3,8,8),new THREE.MeshBasicMaterial({color:CY}));scene.add(pulse);let elapsed=0,last=performance.now();
function resize(){const w=stage.clientWidth,h=stage.clientHeight;if(!w||!h)return;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();}new ResizeObserver(resize).observe(stage);resize();document.getElementById('worldFallback').hidden=true;dispatchEvent(new Event('atg:ready'));
function animate(now){requestAnimationFrame(animate);const delta=Math.max(0,Math.min((now-last)/1000,.1));last=now;if(document.hidden)return;if(!paused)elapsed+=delta;const step=Math.floor(elapsed/4)%(sequence.length-1);pulse.position.lerpVectors(groups.get(sequence[step]).position,groups.get(sequence[step+1]).position,(elapsed%4)/4);pulse.position.y=.6;controls.update();renderer.render(scene,camera);}requestAnimationFrame(animate);
