#!/usr/bin/env python3
"""queue/candidates/*.json から選択ページ out/select.html を作る。
ラジオボタンで選び、「選択結果をコピー」で出る短い文をClaudeに貼れば確定する。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
days = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "queue/candidates").glob("*.json"))]
selected = {p.stem for p in (ROOT / "queue/selected").glob("*.json")}
days = [d for d in days if d["date"] not in selected]

html = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>投稿案セレクト</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--fg:#1c1f24;--mut:#6b7280;--acc:#e8641b;--line:#e3e6eb}
@media (prefers-color-scheme:dark){:root{--bg:#14161a;--card:#1d2026;--fg:#eceff3;--mut:#9aa3b0;--line:#2c313a}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,sans-serif;padding:16px}
h1{font-size:20px;margin:0 0 12px}h2{font-size:17px;margin:24px 0 4px}h3{font-size:14px;color:var(--mut);margin:14px 0 6px}
label{display:block;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:6px 0;cursor:pointer}
input:checked+span{color:var(--acc);font-weight:600}label:has(input:checked){border-color:var(--acc)}
.id{color:var(--mut);margin-right:6px;font-size:13px}.note{color:var(--mut);font-size:14px}
button{margin-top:20px;width:100%;padding:14px;border:0;border-radius:10px;background:var(--acc);color:#fff;font-size:16px}
pre{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px;white-space:pre-wrap}
</style></head><body><h1>投稿案セレクト</h1>
<p class="note">各枠から1案を選び、最後の「選択結果をコピー」をClaudeに貼ってください。</p><div id="root"></div>
<button id="copy">選択結果をコピー</button><pre id="out"></pre>
<script>
const DAYS=__DATA__;
const root=document.getElementById('root');
for(const d of DAYS){
  const h=document.createElement('h2');h.textContent=d.date;root.appendChild(h);
  for(const [slot,s] of Object.entries(d.slots)){
    const t=document.createElement('h3');t.textContent=slot.replace('_',' ')+'｜'+s.label;root.appendChild(t);
    if(!s.candidates.length){const n=document.createElement('div');n.className='note';n.textContent=s.note||'案なし';root.appendChild(n);continue}
    for(const c of s.candidates){
      const l=document.createElement('label');
      l.innerHTML='<input type="radio" hidden name="'+d.date+'|'+slot+'" value="'+c.id+'"><span><span class="id">'+c.id+'</span></span>';
      l.querySelector('span').append(c.text);root.appendChild(l);
    }
  }
}
document.getElementById('copy').onclick=()=>{
  const res={};
  document.querySelectorAll('input:checked').forEach(i=>{const [d,s]=i.name.split('|');(res[d]??={})[s.split('_')[1]]=i.value});
  const txt=Object.entries(res).map(([d,v])=>d+' '+Object.entries(v).map(([k,x])=>k+'='+x).join(' ')).join('\\n');
  document.getElementById('out').textContent=txt||'（未選択）';
  try{navigator.clipboard.writeText(txt)}catch(e){}
};
</script></body></html>"""

out = ROOT / "out" / "select.html"
out.parent.mkdir(exist_ok=True)
out.write_text(html.replace("__DATA__", json.dumps(days, ensure_ascii=False)), encoding="utf-8")
print(f"wrote {out}")
