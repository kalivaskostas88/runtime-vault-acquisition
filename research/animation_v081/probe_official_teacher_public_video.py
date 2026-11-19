#!/usr/bin/env python3
"""V081 PROFESSIONAL-FIRST. Probe official Blender Studio publicly accessible
training pages for genuine legally available video, license, subtitles.
Metadata only. No paywall bypass, no copied full AV, no invented watching claims.
Use before attempting any further Blender elephant ear geometry experiment.
"""
import requests,html,json,re,pathlib,urllib.parse,hashlib
from html.parser import HTMLParser
OUT=pathlib.Path("research/animation_v081");OUT.mkdir(parents=True,exist_ok=True)
SOURCES={
 "KASPAR_SCULPTING_MULTIPLE_OBJECTS":"https://studio.blender.org/training/blender-fundamentals-45-lts/using-multiple-objects/",
 "KASPAR_DETAILED_SCULPTING":"https://studio.blender.org/training/blender-fundamentals-45-lts/detailed-sculpting/",
 "KASPAR_FREE_SCULPTING_FUNDAMENTALS_ARCHIVED":"https://studio.blender.org/training/stylized-character-workflow/5d5e6141b01c790d39b7ed4e/"
}
class Tags(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.video_tags=[];self.sources=[];self.meta=[];self.track=[]
 def handle_starttag(self,tag,attr):
  d=dict(attr)
  if tag=="a" and "href" in d:self.links.append(d["href"])
  if tag in ("video","source","track","meta") and any(x in d for x in ("src","content","poster")):
   getattr(self,{"video":"video_tags","source":"sources","track":"track","meta":"meta"}[tag]).append(d)
r={"schema":"V081_PROFESSIONAL_FULL_REAL_VIDEO_ACCESS_PREFLIGHT","license_check":"ON_ORIGINAL_PAGE_ONLY",
   "method":"GET official public webpage, parse exact public video download anchor and tracks",
   "claims":{"full_new_4_5_video_watched":False,"captured_frames_reviewed":False,"audio_listened":False},
   "source_pages":{}}
sess=requests.Session();sess.headers["User-Agent"]="Mozilla/5.0 (compatible; Educational research; public source access only)"
for key,url in SOURCES.items():
 entry={"source":url,"source_claim":"NOT_STUDIED_IN_AV_THIS_RUN"}
 try:
  t=sess.get(url,timeout=45)
  entry["status_code"]=t.status_code;entry["final_domain"]=urllib.parse.urlparse(t.url).netloc
  entry["html_len"]=len(t.content);entry["html_sha256"]=hashlib.sha256(t.content).hexdigest()
  t.raise_for_status()
  dom=Tags();dom.feed(t.text)
  entry["ccby_token_present"]=bool(re.search(r"\bCC[- ]BY\b",t.text,re.I))
  entry["license_near_context"]=re.findall(r".{0,65}(?:license|CC-BY).{0,105}",t.text,re.I)[:6]
  all_links=dom.links+ [d.get("src","") for d in dom.video_tags+dom.sources+dom.track]
  allowed=[urllib.parse.urljoin(url,x) for x in all_links if x and
    any(y in x.lower() for y in (".mp4",".webm",".m3u8",".vtt",".srt","download-source/files","download-subtitle"))]
  # source domain is part of the trust perimeter
  allowed=[x for x in allowed if urllib.parse.urlparse(x).hostname in ("studio.blender.org","cloud.blender.org")]
  entry["public_media_and_track_links"]=allowed[:30]
  entry["video_tag_count"]=len(dom.video_tags)
  entry["source_tag_count"]=len(dom.sources)
  entry["track_tag_count"]=len(dom.track)
  entry["meta_video_entries"]=[x for x in dom.meta if any(q in repr(x).lower() for q in ("video","license"))][:10]
  entry["qualified_for_direct_public_mp4_study"]=bool(entry["ccby_token_present"] and any(x.endswith(".mp4") or ".mp4?" in x for x in allowed))
  entry["source_claim"]="PUBLIC_PAGE_PROBED_NO_FULL_VIDEO_REVIEW"
 except Exception as e:
  entry["error"]=str(e)[:200]
  entry["source_claim"]="ACCESS_HOLD"
 r["source_pages"][key]=entry
p=OUT/"V081_OFFICIAL_PROFESSIONAL_AV_ACCESS_PREFLIGHT.json"
p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
print("V081_OFFICIAL_PUBLIC_VIDEO_PROBE",json.dumps(r,ensure_ascii=False)[:20000])
