(()=>{
const TSE = "https://resultados.tse.jus.br/oficial", ELE = "6258";
const $ = id => document.getElementById(id);
const num = x => { if(x==null||x==="") return 0; if(typeof x==="number") return x; const s=String(x).trim(); return s.includes(",") ? +s.replace(/\./g,"").replace(",",".") || 0 : +s || 0; };
const fmt = n => Math.round(n).toLocaleString("pt-BR");
const pct = (n,d=1) => n.toLocaleString("pt-BR",{minimumFractionDigits:d,maximumFractionDigits:d})+"%";
const pp = (n,d=2) => (n>0?"+":n<0?"−":"")+Math.abs(n).toLocaleString("pt-BR",{minimumFractionDigits:d,maximumFractionDigits:d});
const esc = s => String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const LOWER = new Set(["da","de","do","das","dos","e"]);
const title = s => String(s||"").toLowerCase().split(/\s+/).map((w,i)=>i&&LOWER.has(w)?w:w.charAt(0).toUpperCase()+w.slice(1)).join(" ");
const ls = k => { try{ const v=localStorage.getItem(k); return v?JSON.parse(v):null }catch(e){ return null } };

/* ---------- Resultado final ---------- */
function cands(d){
  const out=[];
  (function walk(o,sg){
    if(Array.isArray(o)){ o.forEach(x=>walk(x,sg)); return; }
    if(!o||typeof o!=="object") return;
    const p=o.sg||sg;
    if("vap" in o && (o.nm||o.nmu)){ out.push({n:String(o.n||""), sq:o.sqcand?String(o.sqcand):"", nm:title(o.nmu||o.nm), sg:p||"", vap:num(o.vap), pvap:num(o.pvap)}); return; }
    for(const k in o){ if(k!=="s"&&k!=="v"&&k!=="e"&&typeof o[k]==="object") walk(o[k],p); }
  })(d.carg||d,"");
  return out;
}
async function loadFinal(){
  try{ const r=await fetch("../data/presidente_2t.json",{cache:"no-cache"}); if(r.ok){ const j=await r.json(); if(j.br) return j.br; } }catch(e){}
  for(const base of [TSE]){
    try{ const r=await fetch(`${base}/ele2026/${ELE}/dados/br/br-c0001-e00${ELE}-u.json`,{cache:"no-cache"}); if(r.ok) return await r.json(); }catch(e){}
  }
  return null;
}
async function loadHist(){
  try{ const r=await fetch("../data/historico_2t.json",{cache:"no-cache"}); if(r.ok){ const j=await r.json(); if(j.proj&&j.proj.length) return {pts:j.proj, from:"file"}; } }catch(e){}
  const h = ls("proj:hist:"+ELE);
  return {pts: h||[], from: h&&h.length ? "local" : "none"};
}

/* ---------- Fotos: cópia local, depois TSE, depois iniciais ---------- */
const initials = nm => nm.split(" ").filter(w=>w.length>2).map(w=>w[0]).slice(0,2).join("").toUpperCase();
const photo = c => `<span class="ph" aria-hidden="true">${esc(initials(c.nm))}${c.sq?`<img src="../fotos/${c.sq}.jpeg" data-alt="${TSE}/ele2026/${ELE}/fotos/br/${c.sq}.jpeg" alt="" loading="lazy">`:""}</span>`;
document.addEventListener("error", e=>{ const im=e.target; if(!(im instanceof HTMLImageElement)||!im.closest(".ph")) return; if(im.dataset.alt){ const a=im.dataset.alt; im.dataset.alt=""; im.src=a; } else im.remove(); }, true);
const colorOf = (c,i) => /^PT\b/.test(c.sg) ? "var(--c0)" : /^PL\b/.test(c.sg) ? "var(--c1)" : i ? "var(--c1)" : "var(--c0)";

/* ---------- Métricas de acerto ----------
   Cada leitura guardou: x = % das seções apuradas, pa = projeção da fatia do candidato de menor número,
   lo/hi = faixa de 95%, pc = fatia apurada naquele momento. */
function metrics(pts, finalA){
  const P = pts.filter(p=>p.x<99.5 && p.x>=1);
  if(!P.length) return null;
  const ePj = P.map(p=>Math.abs(p.pa-finalA)*100), eAp = P.map(p=>Math.abs(p.pc-finalA)*100);
  const mean = a => a.reduce((s,v)=>s+v,0)/a.length;
  const winA = finalA>0.5;
  const okW = P.map(p=>(p.pa>0.5)===winA), okB = P.map(p=>finalA>=p.lo && finalA<=p.hi);
  let since=null; for(let i=P.length-1;i>=0;i--){ if(okW[i]) since=P[i].x; else break; }
  const after3 = P.filter(p=>p.x>=3);
  return {n:P.length, x0:P[0].x, x1:P[P.length-1].x,
    maeP:mean(ePj), maeA:mean(eAp),
    maeP3: after3.length? mean(after3.map(p=>Math.abs(p.pa-finalA)*100)) : null,
    win: okW.filter(Boolean).length/P.length*100, band: okB.filter(Boolean).length/P.length*100, since};
}
const CHECK = [1,2,3,5,10,20,30,50,75,90];
function checkpoints(pts){
  const P = pts.filter(p=>p.x<99.5);
  return CHECK.map(c=>P.find(p=>p.x>=c && p.x<c*1.6+2)).map((p,i)=>p?{c:CHECK[i],...p}:null).filter(Boolean);
}

/* ---------- Desenho ---------- */
async function main(){
  const d = await loadFinal();
  if(!d){ $("liveTxt").textContent="Não foi possível carregar o resultado"; $("live").className="live err"; return; }
  const all = cands(d).sort((a,b)=>b.vap-a.vap).slice(0,2);
  const byNum = [...all].sort((a,b)=>a.n.localeCompare(b.n,"pt",{numeric:true}));   // A = menor número, como na projeção
  const C = byNum.map((c,i)=>({...c, col:colorOf(c,i)}));
  const A=C[0], B=C[1], tot=A.vap+B.vap, finalA=A.vap/tot;
  const s=d.s||{}, pst=num(s.pst||d.pst);
  $("liveTxt").textContent = pst>=100 ? "Resultado final" : "Resultado parcial";
  $("updTxt").textContent = d.hg ? `Totalização do TSE: ${d.dg||""} às ${d.hg}` : "";

  const H = await loadHist(), pts = (H.pts||[]).filter(p=>typeof p.pa==="number"), M = metrics(pts, finalA);
  const last = pts.filter(p=>p.x<99.5).slice(-1)[0];

  const win = [...C].sort((a,b)=>b.vap-a.vap);
  $("duo").innerHTML = win.map((c,i)=>{
    const sh = c.vap/tot*100, first = pts.find(p=>p.x>=1);
    const pj = first ? (c===A ? first.pa : 1-first.pa)*100 : null;
    return `<div class="cand${i===0?" first":""}" style="--cc:${c.col}">
      ${photo(c)}
      <div class="who">${i===0?`<span class="tag">Presidente eleito</span>`:""}
        <span class="nm">${esc(c.nm)}</span><span class="pt">${esc(c.sg)} · ${esc(c.n)}</span>
        <span class="now">${fmt(c.vap)} votos${pj!=null?` · a projeção dizia ${pct(pj)} com ${pct(first.x)} apurado`:""}</span></div>
      <div class="pc"><b>${pct(sh,2)}</b><span>${i===0?"venceu":"dos votos válidos"}</span></div></div>`;
  }).join("");

  if(M){
    const W = win[0];
    $("verdict").innerHTML = M.since!=null && M.since<=M.x0+0.01
      ? `A projeção apontou <b>${esc(W.nm)}</b> como vencedor em todas as ${M.n} leituras registradas, desde ${pct(M.x0,2)} das seções apuradas.`
      : M.since!=null
        ? `A projeção apontou <b>${esc(W.nm)}</b> como vencedor de forma definitiva a partir de <b>${pct(M.since,2)}</b> das seções apuradas.`
        : `A projeção não apontou o vencedor correto na última leitura registrada.`;
    $("kpis").innerHTML = `
      <div class="kpi"><b>${pct(M.win,0)}</b><span>das leituras apontaram o vencedor certo</span><small>${M.n} leituras, de ${pct(M.x0,1)} a ${pct(M.x1,1)} apurado</small></div>
      <div class="kpi"><b>${M.maeP.toLocaleString("pt-BR",{maximumFractionDigits:2,minimumFractionDigits:2})} p.p.</b><span>erro médio da projeção</span><small>O percentual apurado errava em média ${M.maeA.toLocaleString("pt-BR",{maximumFractionDigits:2,minimumFractionDigits:2})} p.p.${M.maeP3!=null?` · a partir de 3% apurado: ${M.maeP3.toLocaleString("pt-BR",{maximumFractionDigits:2,minimumFractionDigits:2})} p.p.`:""}</small></div>
      <div class="kpi"><b>${pct(M.band,0)}</b><span>das faixas de 95% continham o resultado final</span><small>O esperado de uma faixa bem calibrada é perto de 95%.</small></div>`;
  } else {
    $("verdict").innerHTML = `O índice de acerto aparece assim que o histórico de leituras da noite for publicado.`;
    $("secChart").hidden = true; $("secTable").hidden = true;
  }
  if(H.from!=="file"){
    $("nohist").innerHTML = H.from==="local"
      ? `<div class="nohist"><b>Estes números vêm das leituras salvas neste navegador.</b> Quem abrir a página em outro aparelho não vai vê-los. Para publicar para todos, baixe o arquivo e coloque-o em <code>site/data/</code> no GitHub com o nome <code>historico_2t.json</code>.<br><button class="btn" id="exp" type="button">Baixar historico_2t.json</button></div>`
      : `<div class="nohist"><b>O histórico de leituras da noite ainda não foi publicado.</b> Ele fica salvo no navegador de quem acompanhou a projeção ao vivo. Abra esta página nesse navegador para ver o índice de acerto e baixar o arquivo.</div>`;
    const b=$("exp"); if(b) b.onclick=()=>{
      const blob=new Blob([JSON.stringify({gerado:new Date().toISOString(), eleicao:ELE, proj:ls("proj:hist:"+ELE)||[], apu:ls("apu:hist:"+ELE)||[]})],{type:"application/json"});
      const a=document.createElement("a"); a.href=URL.createObjectURL(blob); a.download="historico_2t.json"; document.body.appendChild(a); a.click(); a.remove();
    };
  }
  if(M){ renderChart(pts, finalA, C); renderTable(pts, finalA, C); }
}

function renderChart(h, finalA, C){
  h = h.filter(p=>p.x<99.5);
  const W=Math.max(340,Math.min(640,($("chart").clientWidth||640)-28)),H=W<480?220:260,L=36,R=12,T=10,B=26, col=C[0].col;
  const vals=h.flatMap(p=>[p.lo*100,p.hi*100,p.pc*100]).concat(finalA*100);
  const lo=Math.floor(Math.min(...vals,48)-1), hi=Math.ceil(Math.max(...vals,52)+1);
  const x0=Math.max(0,Math.floor(h[0].x/10)*10);
  const X=p=>L+(p-x0)/(100-x0||1)*(W-L-R), Y=v=>T+(hi-v)/(hi-lo)*(H-T-B);
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Projeção, apuração e resultado final">`;
  const step=(hi-lo)>16?4:(hi-lo)>8?2:1;
  for(let v=Math.ceil(lo/step)*step;v<=hi;v+=step) s+=`<line x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)"/><text x="${L-6}" y="${Y(v)+4}" text-anchor="end">${v}%</text>`;
  s+=`<line x1="${L}" x2="${W-R}" y1="${Y(50)}" y2="${Y(50)}" stroke="var(--ink)" opacity=".35" stroke-dasharray="2 4"/>`;
  for(let p=x0;p<=100;p+=(100-x0)>50?20:10) s+=`<text x="${X(p)}" y="${H-6}" text-anchor="middle">${p}%</text>`;
  const band=h.map(p=>`${X(p.x).toFixed(1)},${Y(p.hi*100).toFixed(1)}`).join(" ")+" "+[...h].reverse().map(p=>`${X(p.x).toFixed(1)},${Y(p.lo*100).toFixed(1)}`).join(" ");
  s+=`<polygon points="${band}" fill="${col}" opacity=".16"/>`;
  s+=`<path d="${h.map((p,i)=>`${i?"L":"M"}${X(p.x).toFixed(1)},${Y(p.pc*100).toFixed(1)}`).join("")}" fill="none" stroke="${col}" stroke-width="2" stroke-dasharray="5 4" opacity=".75"/>`;
  s+=`<path d="${h.map((p,i)=>`${i?"L":"M"}${X(p.x).toFixed(1)},${Y(p.pa*100).toFixed(1)}`).join("")}" fill="none" stroke="${col}" stroke-width="2.8" stroke-linejoin="round"/>`;
  s+=`<line x1="${L}" x2="${W-R}" y1="${Y(finalA*100)}" y2="${Y(finalA*100)}" stroke="var(--ink)" stroke-width="1.6"/><text x="${W-R}" y="${Y(finalA*100)-6}" text-anchor="end" style="fill:var(--ink);font-weight:700">resultado: ${pct(finalA*100,2)}</text>`;
  s+=`</svg><div class="legend" style="color:${col}"><span><span class="sw" style="background:currentColor"></span><span style="color:var(--ink2)">Projeção de ${esc(C[0].nm)}</span></span><span><span class="sw box" style="background:currentColor;opacity:.25"></span><span style="color:var(--ink2)">faixa de 95%</span></span><span><span class="sw dash"></span><span style="color:var(--ink2)">apurado naquele momento</span></span><span style="color:var(--ink2)"><span class="sw" style="background:var(--ink)"></span>resultado final</span><span style="color:var(--ink2)">eixo horizontal: % das seções apuradas</span></div>`;
  $("chart").innerHTML=s;
}
function renderTable(pts, finalA, C){
  const rows = checkpoints(pts);
  const f2 = v => v.toLocaleString("pt-BR",{minimumFractionDigits:2,maximumFractionDigits:2});
  $("acc").innerHTML = `<thead><tr><th scope="col">Apurado</th><th scope="col">${esc(C[0].nm)} no apurado</th><th scope="col">Projeção</th><th scope="col">Faixa de 95%</th><th scope="col">Erro do apurado</th><th scope="col">Erro da projeção</th><th scope="col">Resultado dentro da faixa?</th></tr></thead>
  <tbody>${rows.map(r=>{
    const eA=(r.pc-finalA)*100, eP=(r.pa-finalA)*100, inB=finalA>=r.lo&&finalA<=r.hi;
    return `<tr><td>${pct(r.x,2)}</td><td>${pct(r.pc*100,2)}</td><td>${pct(r.pa*100,2)}</td><td>${pct(r.lo*100,1)} a ${pct(r.hi*100,1)}</td><td>${pp(eA)} p.p.</td><td><b>${pp(eP)} p.p.</b></td><td>${inB?"Sim":"Não"}</td></tr>`;
  }).join("")}
  <tr><td>100%</td><td colspan="6">Resultado final: ${esc(C[0].nm)} ${pct(finalA*100,2)} · ${esc(C[1].nm)} ${pct((1-finalA)*100,2)}</td></tr></tbody>`;
}
main();
})();
