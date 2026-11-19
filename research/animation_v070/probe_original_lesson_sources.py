#!/usr/bin/env python3
"""V070: evidence-only original Blender Studio teaching-page access probe.
No video extraction, copying content, download, or Blender run in this stage.
Never claim that metadata/text scraping equals actual video/audio study.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin,urlparse
import hashlib,json,datetime,re,requests
ROOT=Path("research/animation_v070");ROOT.mkdir(parents=True,exist_ok=True)
URLS={
 "basic_sculpting":"https://studio.blender.org/training/blender-fundamentals-45-lts/basic-sculpting/",
 "fine_control":"https://studio.blender.org/training/blender-fundamentals-45-lts/fine-control/",
 "multiple_objects":"https://studio.blender.org/training/blender-fundamentals-45-lts/using-multiple-objects/"
}
class Inspect(HTMLParser):
 def __init__(self):
  super().__init__();self.stack=[];self.links=[];self.media=[];self.headings=[];self.fragments=[];self.in_script=False
 def handle_starttag(self,t,attrs):
  d=dict(attrs);self.stack.append(t)
  if t=="a" and d.get("href"):self.links.append(d.get("href"))
  if t in {"video","source","iframe","track"}:self.media.append({"tag":t,"url":d.get("src") or d.get("data-src") or "", "type":d.get("type") or ""})
 def handle_endtag(self,t):
  if self.stack:self.stack.pop()
 def handle_data(self,d):
  s=" ".join(d.split())
  if not s:return
  if any(x in self.stack for x in ("script","style","noscript")):return
  self.fragments.append(s)
  if any(x in self.stack for x in ("h1","h2","h3")):self.headings.append(s[:150])
s=requests.Session();s.headers.update({"User-Agent":"Mozilla/5.0 (compatible; Blender Research Verification; education)"})
out={"schema":"V070_ORIGINAL_TEACHER_LESSON_ACCESS_PROBE","date_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"method":"requests public GET, HTMLParser; no auth, no paywall bypass","native_blender":"NOT_RUN","art":"HOLD","actual_media_watched":False,"audio_listened":False,"pages":{}}
for label,url in URLS.items():
 rec={"url":url,"status":"NOT_ATTEMPTED"}
 try:
  r=s.get(url,timeout=45); rec["http_status"]=r.status_code; rec["final_host"]=urlparse(r.url).netloc;rec["bytes"]=len(r.content);r.raise_for_status()
  parsed=Inspect();parsed.feed(r.text)
  txt=" ".join(parsed.fragments)
  links=[urljoin(url,x) for x in parsed.links]
  explicitly_downloadable=[x for x in links if re.search(r"\.(?:mp4|webm)(?:\?|$)",x,re.I) and urlparse(x).netloc in ("studio.blender.org","cloud.blender.org")]
  media=parsed.media
  rec.update({"status":"PUBLIC_SOURCE_HTML_READ","html_sha256":hashlib.sha256(r.content).hexdigest(),"visible_text_sha256":hashlib.sha256(txt.encode()).hexdigest(),
  "visible_text_chars":len(txt),"headings":list(dict.fromkeys(parsed.headings))[:50],
  "explicit_mp4_links":explicitly_downloadable[:10],"media_elements_count":len(media),
  "media_element_types":[{"tag":x["tag"],"host":urlparse(urljoin(url,x["url"])).netloc if x["url"] else None} for x in media[:20]],
  "free_text_indicator":bool(re.search(r"\bFree\b",txt)),"license_cc_by_explicit":bool(re.search(r"\bCC[- ]?BY\b",txt,re.I))})
  # Store small context snippets for decisions, NOT a reproduction of original lessons.
  examples=[]
  for pat in ("voxel","remesh","Ctrl J","Join","Scale","resolution","finger","open meshes","mask"):
   match=re.search(re.escape(pat),txt,re.I)
   if match:
    examples.append({"term":pat,"context_excerpt":" ".join(txt[max(0,match.start()-45):match.end()+85].split())[:135]})
  rec["short_context_snippets"]=examples
 except Exception as e:rec["status"]="ACCESS_OR_PARSE_HOLD";rec["error"]=str(e)[:250]
 out["pages"][label]=rec
p=ROOT/"SOURCE_ACCESS_RECEIPT.json";p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print("V070_PUBLIC_TEACHER_SOURCE_PROBE",json.dumps({k:{z:v.get(z) for z in ("status","http_status","media_elements_count","explicit_mp4_links","license_cc_by_explicit","visible_text_chars")} for k,v in out["pages"].items()},ensure_ascii=False),flush=True)
