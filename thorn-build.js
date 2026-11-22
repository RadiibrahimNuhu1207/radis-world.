window.__TRES="running";(async()=>{
// Rebuilds "The Thorn and the Throne" with revised text, reusing the old PDF's cover, front pages and chapter art.
const ls=(src)=>new Promise((ok,err)=>{const s=document.createElement('script');s.src=src;s.onload=ok;s.onerror=err;document.head.appendChild(s);});
if(!window.PDFLib) await ls('https://cdn.jsdelivr.net/npm/pdf-lib@1.17.1/dist/pdf-lib.min.js');
if(!window.fontkit) await ls('https://cdn.jsdelivr.net/npm/@pdf-lib/fontkit@1.1.1/dist/fontkit.umd.min.js');
const {PDFDocument,PDFName,rgb}=PDFLib;
const parts=await (await fetch('https://raw.githubusercontent.com/RadiibrahimNuhu1207/radis-world./ad-media/thorn-revised.json?'+Date.now())).json();
const oldBytes=await (await fetch('/media/books/pdf/the-thorn-and-the-throne.pdf')).arrayBuffer();
const old=await PDFDocument.load(oldBytes);
// locate opener pages in the old PDF (pdf.js already loaded as window.__pdf)
const pj=window.__pdf;const opener={};
for(let n=1;n<=pj.numPages;n++){const t=(await (await pj.getPage(n)).getTextContent()).items.map(i=>i.str.trim());
 for(const s of t){if(/^(PROLOGUE|CHAPTER \d+)$/.test(s)&&opener[s]==null)opener[s]=n-1;if(s==='The End'&&opener.END==null)opener.END=n-1;}}
function jpgOf(idx){const pg=old.getPage(idx);const xo=pg.node.Resources().lookup(PDFName.of('XObject'));
 for(const k of xo.keys()){const st=xo.lookup(k);const f=st.dict.get(PDFName.of('Filter'));if(String(f).includes('DCT'))return st.contents;}throw 'no jpg on page '+idx;}
const gf=n=>fetch('https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/'+n).then(r=>{if(!r.ok)throw n;return r.arrayBuffer()});
const doc=await PDFDocument.create();doc.registerFontkit(fontkit);
doc.setTitle('The Thorn and the Throne');doc.setAuthor('Radi Ibrahim Nuhu');doc.setLanguage('en');
const F={r:await doc.embedFont(await gf('crimsontext/CrimsonText-Regular.ttf'),{subset:true}),i:await doc.embedFont(await gf('crimsontext/CrimsonText-Italic.ttf'),{subset:true}),
 d:await doc.embedFont(await gf('playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf'),{subset:true})};
const W=432,H=648,M={l:48,r:48,t:64,b:66},TW=W-M.l-M.r;
const INK=rgb(.17,.12,.07),SOFT=rgb(.42,.31,.19),ACC=rgb(.55,.27,.08);
const SZ=13.2,LD=20;const TITLE='The Thorn and the Throne';
let page,y,num=0,bg=null;
// front matter: copy old pages before the prologue unchanged
const front=[...Array(opener.PROLOGUE).keys()];
for(const p of await doc.copyPages(old,front)){doc.addPage(p);num++;}
const cache={};const emb=async idx=>cache[idx]||(cache[idx]=await doc.embedJpg(jpgOf(idx)));
function bgPage(im){page=doc.addPage([W,H]);num++;page.drawImage(im,{x:0,y:0,width:W,height:H});y=H-M.t;}
function newPage(){bgPage(bg);const t=num%2==0?'Radi Ibrahim Nuhu':TITLE;const tw=F.i.widthOfTextAtSize(t,9.5);
 page.drawText(t,{x:(W-tw)/2,y:H-38,size:9.5,font:F.i,color:SOFT});const n=String(num);page.drawText(n,{x:(W-F.r.widthOfTextAtSize(n,10.5))/2,y:34,size:10.5,font:F.r,color:SOFT});}
function wrap(text,font,size,width,ind=0){const words=text.split(/\s+/);const lines=[];let cur='',w0=width-ind;
 for(const wd of words){const t=cur?cur+' '+wd:wd;if(font.widthOfTextAtSize(t,size)>w0&&cur){lines.push(cur);cur=wd;w0=width;}else cur=t;}if(cur)lines.push(cur);return lines;}
function justify(line,x,yy,font,size,width,last){const ws=line.split(' ');if(last||ws.length<2){page.drawText(line,{x,y:yy,size,font,color:INK});return;}
 const tot=ws.reduce((a,w)=>a+font.widthOfTextAtSize(w,size),0);const gap=(width-tot)/(ws.length-1);if(gap>10){page.drawText(line,{x,y:yy,size,font,color:INK});return;}
 let cx=x;for(const w of ws){page.drawText(w,{x:cx,y:yy,size,font,color:INK});cx+=font.widthOfTextAtSize(w,size)+gap;}}
function centered(t,font,size,yy,color=INK){page.drawText(t,{x:(W-font.widthOfTextAtSize(t,size))/2,y:yy,size,font,color});}
function spaced(t,font,size,yy,color,sp){const w=[...t].reduce((a,c)=>a+font.widthOfTextAtSize(c,size)+sp,-sp);let x=(W-w)/2;for(const c of t){page.drawText(c,{x,y:yy,size,font,color});x+=font.widthOfTextAtSize(c,size)+sp;}}
function ornament(yy){const cx=W/2;page.drawLine({start:{x:cx-44,y:yy},end:{x:cx-9,y:yy},thickness:.7,color:ACC});page.drawLine({start:{x:cx+9,y:yy},end:{x:cx+44,y:yy},thickness:.7,color:ACC});
 page.drawRectangle({x:cx-3.2,y:yy-3.2,width:6.4,height:6.4,rotate:PDFLib.degrees(45),color:ACC});}
function para(text,{indent=true,drop=false}={}){
 if(drop&&text.length>40){const m=text.match(/^[“"‘]?\S/);const L=m[0];const rest=text.slice(L.length);const DS=52;const dw=F.d.widthOfTextAtSize(L,DS)+7;
  const first=wrap(rest,F.r,SZ,TW-dw).slice(0,3);const used=first.join(' ').split(/\s+/).length;const remText=rest.split(/\s+/).slice(used).join(' ');
  if(y-LD*4<M.b)newPage();page.drawText(L,{x:M.l,y:y-LD*2+5,size:DS,font:F.d,color:ACC});
  first.forEach((l,i)=>{justify(l,M.l+dw,y,F.r,SZ,TW-dw,i==first.length-1&&!remText);y-=LD;});if(first.length<3)y-=LD*(3-first.length);if(remText)para(remText,{indent:false});return;}
 const ind=indent?18:0;const lines=wrap(text,F.r,SZ,TW,ind);
 lines.forEach((l,i)=>{if(y<M.b)newPage();justify(l,M.l+(i==0?ind:0),y,F.r,SZ,TW-(i==0?ind:0),i==lines.length-1);y-=LD;});}
const tocMap=[];
for(const p of parts){if(p.label==='END')continue;const oi=opener[p.label];
 const op=await emb(oi);bg=await emb(oi+1);bgPage(op);tocMap.push([p.label,num]);
 y=H-H*0.42-22;spaced(p.label,F.r,8.5,y,ACC,2.2);y-=30;
 for(const l of wrap(p.title,F.d,21,TW)){centered(l,F.d,21,y);y-=26;}y+=6;ornament(y);y-=34;
 p.p.forEach((t,i)=>para(t,{indent:i>0,drop:i==0}));}
// The End + about
bg=await emb(opener.END);bgPage(bg);y=H-150;centered('The End',F.d,22,y);y-=22;ornament(y);y-=62;centered('About the Author',F.d,18,y);y-=32;
const about=parts.find(p=>p.label==='END').p;about.forEach(t=>{para(t,{indent:false});y-=8;});
const bytes=await doc.save();window.__TPDF=new Blob([bytes],{type:'application/pdf'});
return JSON.stringify({pages:doc.getPageCount(),kb:Math.round(bytes.length/1024),opener,toc:tocMap});
})().then(r=>window.__TRES=r).catch(e=>window.__TRES="ERR "+(e&&e.stack||e));"started"