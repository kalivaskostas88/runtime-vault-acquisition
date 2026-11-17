from html.parser import HTMLParser
from pathlib import Path
import requests, json, re
u="https://studio.blender.org/training/stylized-character-workflow/5d3a1c494980f083715e40ed/"
class P(HTMLParser):
 def __init__(self):
  super().__init__();self.anchors=[]
 def handle_starttag(self,tag,attrs):
  if tag in ("a","video","source"):
   x=dict(attrs); self.anchors.append({"tag":tag,"href":x.get("href"),"src":x.get("src"),"download":x.get("download"),"title":x.get("title")})
s=requests.Session(); s.headers.update({"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"})
try:
 r=s.get(u,timeout=35); txt=r.text
 p=P();p.feed(txt)
 print("PAGE_STATUS",r.status_code,len(r.content),r.url)
 print("FOUND_LINKS",json.dumps([a for a in p.anchors if any(k in str(a).lower() for k in ("download","mp4","subtitle","video"))][:70])[:8000])
 print("SNIPPETS",[txt[max(0,m.start()-120):m.end()+160] for m in list(re.finditer(r"\\.mp4|download|subtitle",txt,re.I))[:7]])
 result={"url":u,"status":r.status_code,"bytes":len(r.content),"matching_anchors":[a for a in p.anchors if any(k in str(a).lower() for k in ("download","mp4","subtitle","video"))][:100],"snippets":[txt[max(0,m.start()-120):m.end()+160] for m in list(re.finditer(r"\\.mp4|download|subtitle",txt,re.I))[:7]]}
except Exception as e:
 print("PROBE_EXCEPTION",repr(e));result={"url":u,"error":str(e)}
Path("research/animation_v043").mkdir(parents=True,exist_ok=True)
Path("research/animation_v043/probe.json").write_text(json.dumps(result,indent=2))
