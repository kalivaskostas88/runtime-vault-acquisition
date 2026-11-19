#!/usr/bin/env python3
"""V081 identify actual video segment headings, ordered demonstration and sizes
from Blender Studio publicly embeddable free lesson. No licensed media republishing.
"""
import requests,bs4,json,hashlib,pathlib,re,urllib.parse
OUT=pathlib.Path("research/animation_v081");OUT.mkdir(exist_ok=True)
SRC="https://studio.blender.org/training/blender-fundamentals-45-lts/using-multiple-objects/"
sess=requests.Session();sess.headers["User-Agent"]="Mozilla/5.0 (research on publicly accessible official instructional video)"
page=sess.get(SRC,timeout=45);page.raise_for_status()
soup=bs4.BeautifulSoup(page.text,"html.parser")
listings=[]
for i,vid in enumerate(soup.select("video")):
 source=vid.find("source")
 if not source:continue
 url=urllib.parse.urljoin(SRC,source.get("src",""))
 if urllib.parse.urlsplit(url).hostname!="studio.blender.org":continue
 prev=vid.find_previous(["h1","h2","h3","h4","h5","strong"])
 nearest_container=vid.find_parent(["figure","div","section"])
 prior=vid.find_previous(string=True)
 def clean(v):return re.sub(r"\s+"," ",str(v or "")).strip()[:180]
 rec={"index":i,"video_file":urllib.parse.urlsplit(url).path.split("/")[-1],
      "preceding_header":clean(prev.get_text(" ",strip=True) if prev else ""),
      "preceding_immediate_text":clean(prior),
      "media_dom_id":vid.get("id"),"media_dom_class":vid.get("class"),
      "media_attributes":{k:v for k,v in vid.attrs.items() if k in ("data-video-id","title","preload")},
      "path":urllib.parse.urlsplit(url).path}
 try:
  h=sess.head(url,timeout=30,allow_redirects=True)
  rec["head_status"]=h.status_code
  rec["bytes"]=int(h.headers.get("Content-Length","0") or 0)
  rec["media_type"]=h.headers.get("Content-Type","")[:70]
 except Exception as e:rec["head_error"]=str(e)[:130]
 listings.append(rec)
output={"schema":"V081_PUBLIC_PROFESSIONAL_SEGMENT_MAP","source":SRC,"actual_video_count":len(listings),
 "republication_license_on_page":False,"full_video_frames_reviewed":False,
 "clips":listings}
(OUT/"V081_OFFICIAL_FREE_TEACHER_CLIP_ORDER.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
print("V081_REAL_TEACHER_SEGMENT_MAP",json.dumps(output,ensure_ascii=False)[:17000])
