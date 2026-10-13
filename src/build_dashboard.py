"""
Build the static TechEngage dashboard (dashboard/index.html).
Embeds post-level data as JSON; Chart.js renders 6 charts.
Filters (post type / topic / weekday) recompute every chart client-side.
"""
import csv
import json
import os

BASE = "/home/hatch/workspace/goals/techengage-social-post-engagement-analysis-10-pts-due-20-oct/hidden_files"
CSV = os.path.join(BASE, "data/processed/hn_stories_clean.csv")
OUT = "/home/hatch/workspace/techengage-social-analysis/dashboard/index.html"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

posts = []
with open(CSV) as f:
    for r in csv.DictReader(f):
        posts.append({
            "t": r["title"][:120],
            "pt": r["post_type"],
            "topic": r["topic"],
            "tl": int(r["title_len"]),
            "s": int(r["score"]),
            "c": int(r["comments"]),
            "wd": r["weekday"],
            "h": int(r["hour_utc"]),
            "d": r["domain"],
        })
data_json = json.dumps(posts)

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TechEngage: Social Post Engagement Analysis</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  * { box-sizing: border-box; }
  body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; background: #0f172a; color: #e2e8f0; }
  header { background: linear-gradient(135deg, #1e3a8a, #7c3aed); padding: 28px 32px; }
  header h1 { margin: 0 0 6px 0; font-size: 26px; }
  header p { margin: 0; opacity: .85; font-size: 14px; }
  .wrap { max-width: 1200px; margin: 0 auto; padding: 24px; }
  .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-bottom: 20px; }
  .kpi { background: #1e293b; border-radius: 10px; padding: 16px; border: 1px solid #334155; }
  .kpi .v { font-size: 28px; font-weight: 700; color: #93c5fd; }
  .kpi .l { font-size: 12px; color: #94a3b8; margin-top: 4px; }
  .filters { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 16px; margin-bottom: 20px; display: flex; gap: 16px; flex-wrap: wrap; align-items: end; }
  .filters label { font-size: 12px; color: #94a3b8; display: block; margin-bottom: 4px; }
  .filters select { background: #0f172a; color: #e2e8f0; border: 1px solid #475569; border-radius: 6px; padding: 8px 10px; font-size: 14px; }
  .filters button { background: #3b82f6; color: #fff; border: 0; border-radius: 6px; padding: 9px 18px; cursor: pointer; font-size: 14px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 16px; }
  .card { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 18px; }
  .card h3 { margin: 0 0 4px 0; font-size: 15px; }
  .card .sub { font-size: 12px; color: #94a3b8; margin-bottom: 10px; }
  .card canvas { max-height: 260px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #334155; }
  th { color: #94a3b8; font-weight: 600; font-size: 12px; }
  footer { text-align: center; color: #64748b; font-size: 12px; padding: 24px; }
  .note { background: #1e293b; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 0 8px 8px 0; font-size: 13px; margin-top: 18px; color: #cbd5e1; }
</style>
</head>
<body>
<header>
  <h1>TechEngage: Social Post Engagement Analysis</h1>
  <p>546 top tech-news stories &middot; Hacker News public API &middot; collected 14 Oct 2026 &middot; task ZR-26-00753</p>
</header>
<div class="wrap">
  <div class="kpis">
    <div class="kpi"><div class="v" id="k-n">-</div><div class="l">Posts in view</div></div>
    <div class="kpi"><div class="v" id="k-score">-</div><div class="l">Median upvotes</div></div>
    <div class="kpi"><div class="v" id="k-com">-</div><div class="l">Median comments</div></div>
    <div class="kpi"><div class="v" id="k-tot">-</div><div class="l">Median total engagement</div></div>
  </div>

  <div class="filters">
    <div><label>Post type</label><select id="f-pt"><option value="">All</option></select></div>
    <div><label>Topic</label><select id="f-topic"><option value="">All</option></select></div>
    <div><label>Weekday</label><select id="f-wd"><option value="">All</option></select></div>
    <div><button onclick="resetFilters()">Reset</button></div>
  </div>

  <div class="grid">
    <div class="card"><h3>Engagement by post type</h3><div class="sub">Median score + comments</div><canvas id="c-pt"></canvas></div>
    <div class="card"><h3>Engagement by title length</h3><div class="sub">Characters in headline</div><canvas id="c-len"></canvas></div>
    <div class="card"><h3>Engagement by topic</h3><div class="sub">Keyword-classified story topic</div><canvas id="c-topic"></canvas></div>
    <div class="card"><h3>Engagement by weekday</h3><div class="sub">UTC day of posting</div><canvas id="c-wd"></canvas></div>
    <div class="card"><h3>Engagement by hour of day</h3><div class="sub">UTC hour of posting (PKT = UTC+5)</div><canvas id="c-hour"></canvas></div>
    <div class="card"><h3>Upvotes vs comments</h3><div class="sub">Each dot is a post (sampled)</div><canvas id="c-scatter"></canvas></div>
  </div>

  <div class="card" style="margin-top:16px">
    <h3>Top posts in current view</h3><div class="sub">Ranked by total engagement</div>
    <div style="overflow-x:auto"><table>
      <thead><tr><th>Title</th><th>Type</th><th>Topic</th><th>Upvotes</th><th>Comments</th></tr></thead>
      <tbody id="top-table"></tbody>
    </table></div>
  </div>

  <div class="note"><b>Method note:</b> headline stat is the median (engagement is heavy-tailed).
  Sample = HN top/best stories, 5-13 Oct 2026 — a study of <i>what wins</i>, not average posts.
  Topic buckets are keyword-based. Weekday/hour patterns come from an 8-day window: treat as directional.</div>
</div>
<footer>TechEngage content planning &middot; public data only (Hacker News API) &middot; no customer data</footer>

<script>
const POSTS = __DATA__;
const WD_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];
const LEN_BUCKETS = ["<=40","41-60","61-80","81-100","100+"];

function lenBucket(n){ if(n<=40) return "<=40"; if(n<=60) return "41-60"; if(n<=80) return "61-80"; if(n<=100) return "81-100"; return "100+"; }
function median(a){ if(!a.length) return 0; const s=[...a].sort((x,y)=>x-y); const m=s.length>>1; return s.length%2 ? s[m] : (s[m-1]+s[m])/2; }

let charts = {};
function filtered(){
  const pt=document.getElementById('f-pt').value, tp=document.getElementById('f-topic').value, wd=document.getElementById('f-wd').value;
  return POSTS.filter(p => (!pt||p.pt===pt) && (!tp||p.topic===tp) && (!wd||p.wd===wd));
}
function agg(rows, key){
  const g={};
  rows.forEach(r=>{ const k=key(r); (g[k]=g[k]||[]).push(r); });
  const out={};
  for(const k in g){ out[k]={ n:g[k].length, s:median(g[k].map(r=>r.s)), c:median(g[k].map(r=>r.c)) }; }
  return out;
}
function bar(id, labels, sVals, cVals){
  if(charts[id]) charts[id].destroy();
  charts[id]=new Chart(document.getElementById(id),{type:'bar',
    data:{labels, datasets:[
      {label:'Median upvotes', data:sVals, backgroundColor:'#3b82f6'},
      {label:'Median comments', data:cVals, backgroundColor:'#a78bfa'}]},
    options:{responsive:true, plugins:{legend:{labels:{color:'#cbd5e1'}}},
      scales:{x:{ticks:{color:'#94a3b8'}}, y:{ticks:{color:'#94a3b8'}, stacked:false}}}});
}

function render(){
  const rows=filtered();
  document.getElementById('k-n').textContent=rows.length;
  document.getElementById('k-score').textContent=Math.round(median(rows.map(r=>r.s)));
  document.getElementById('k-com').textContent=Math.round(median(rows.map(r=>r.c)));
  document.getElementById('k-tot').textContent=Math.round(median(rows.map(r=>r.s+r.c)));

  const pt=agg(rows,r=>r.pt);
  const ptK=Object.keys(pt).sort();
  bar('c-pt',ptK,ptK.map(k=>pt[k].s),ptK.map(k=>pt[k].c));

  const ln=agg(rows,r=>lenBucket(r.tl));
  const lnK=LEN_BUCKETS.filter(k=>ln[k]);
  bar('c-len',lnK,lnK.map(k=>ln[k].s),lnK.map(k=>ln[k].c));

  const tp=agg(rows,r=>r.topic);
  const tpK=Object.keys(tp).sort((a,b)=>(tp[b].s+tp[b].c)-(tp[a].s+tp[a].c));
  bar('c-topic',tpK,tpK.map(k=>tp[k].s),tpK.map(k=>tp[k].c));

  const wd=agg(rows,r=>r.wd);
  const wdK=WD_ORDER.filter(k=>wd[k]);
  bar('c-wd',wdK.map(d=>d.slice(0,3)),wdK.map(k=>wd[k].s),wdK.map(k=>wd[k].c));

  const hr=agg(rows,r=>r.h);
  const hrK=Object.keys(hr).map(Number).sort((a,b)=>a-b);
  if(charts['c-hour']) charts['c-hour'].destroy();
  charts['c-hour']=new Chart(document.getElementById('c-hour'),{type:'line',
    data:{labels:hrK.map(h=>h+':00'),datasets:[{label:'Median total engagement',data:hrK.map(h=>Math.round(hr[h].s+hr[h].c)),borderColor:'#34d399',backgroundColor:'rgba(52,211,153,.15)',fill:true,tension:.3}]},
    options:{responsive:true,plugins:{legend:{labels:{color:'#cbd5e1'}}},scales:{x:{ticks:{color:'#94a3b8'}},y:{ticks:{color:'#94a3b8'}}}}});

  const samp=rows.filter((_,i)=>i%3===0).slice(0,300);
  if(charts['c-scatter']) charts['c-scatter'].destroy();
  charts['c-scatter']=new Chart(document.getElementById('c-scatter'),{type:'scatter',
    data:{datasets:[{label:'Posts',data:samp.map(r=>({x:r.s,y:r.c})),backgroundColor:'rgba(147,197,253,.6)'}]},
    options:{responsive:true,plugins:{legend:{labels:{color:'#cbd5e1'}}},scales:{x:{title:{display:true,text:'Upvotes',color:'#94a3b8'},ticks:{color:'#94a3b8'}},y:{title:{display:true,text:'Comments',color:'#94a3b8'},ticks:{color:'#94a3b8'}}}}});

  const top=[...rows].sort((a,b)=>(b.s+b.c)-(a.s+a.c)).slice(0,10);
  document.getElementById('top-table').innerHTML=top.map(r=>
    `<tr><td>${r.t.replace(/</g,'&lt;')}</td><td>${r.pt}</td><td>${r.topic}</td><td>${r.s}</td><td>${r.c}</td></tr>`).join('');
}
function resetFilters(){ ['f-pt','f-topic','f-wd'].forEach(id=>document.getElementById(id).value=''); render(); }

(function init(){
  const pts=[...new Set(POSTS.map(p=>p.pt))].sort();
  const tps=[...new Set(POSTS.map(p=>p.topic))].sort();
  pts.forEach(v=>document.getElementById('f-pt').insertAdjacentHTML('beforeend',`<option>${v}</option>`));
  tps.forEach(v=>document.getElementById('f-topic').insertAdjacentHTML('beforeend',`<option>${v}</option>`));
  WD_ORDER.forEach(v=>document.getElementById('f-wd').insertAdjacentHTML('beforeend',`<option>${v}</option>`));
  ['f-pt','f-topic','f-wd'].forEach(id=>document.getElementById(id).addEventListener('change',render));
  render();
})();
</script>
</body>
</html>"""

html = html.replace("__DATA__", data_json)
with open(OUT, "w") as f:
    f.write(html)
print(f"dashboard -> {OUT} ({len(html)//1024} KB)")
