#!/usr/bin/env python3
"""V083 official public Blender Studio teacher video discovery, exact source only.
No subscriber bypass, no video download until clip selection/rights preflight.
"""
import requests, bs4, pathlib, json, re, hashlib, urllib.parse
O=pathlib.Path("research/animation_v083");O.mkdir(parents=True,exist_ok=True)
pages={
 "BLENDER_STUDIO_BASIC_SCULPTING":"https://studio.blender.org/training/blender-fundamentals-45-lts/basic-sculpting/",
 "BLENDER_STUDIO_DETAILED_SCULPTING":"https://studio.blender.org/training/blender-fundamentals-45-lts/detailed-sculpting/",
 "KASPAR_FINISHING_HEAD":"https://studio.blender.org/training/stylized-character-workflow/5d3a1ccafa5e1feb5a30783b/"}
r={"schema":"V083_REAL_PROFESSIONAL_ROOT_ATTACHMENT_VIDEO_DISCOVERY",
 "date":"2026-11-19","new_full_video_watched":False,"audio_listened":False,
 "original_media_copied_to_library":False,"pages":{}}
s=requests.Session();s.headers["User-Agent"]="Mozilla/5.0 (academic educational source survey, public resources only)"
for name,url in pages.items():
 d={"url":url,"video_clips":[],"source_type":"OFFICIAL_PUBLIC_PAGE_PROBE_NOT_VIDEO_STUDY"}
 try:
  page=s.get(url,timeout=45);d["status"]=page.status_code
  d["final_url"]=page.url;d["length"]=len(page.content)
  d["html_sha256"]=hashlib.sha256(page.content).hexdigest()
  page.raise_for_status()
  tree=bs4.BeautifulSoup(page.text,"html.parser")
  d["page_text_mentions_remesh"]=len(re.findall(r"\b(?:remesh|voxel|merge|join|ears?)\b",tree.get_text(" ",strip=True),re.I))
  d["explicit_media_cc_by_license"]=bool(re.search(r"\bCC[- ]BY\b",tree.get_text(" ",strip=True),re.I))
  for i,video in enumerate(tree.select("video")):
   source=video.find("source")
   if not source or not source.get("src"):continue
   media=urllib.parse.urljoin(url,source["src"])
   if urllib.parse.urlsplit(media).hostname not in ("studio.blender.org","cloud.blender.org"):continue
   h=video.find_previous(["h1","h2","h3","h4","h5"])
   d["video_clips"].append({"index":i,"preceding_heading":h.get_text(" ",strip=True)[:145] if h else None,
     "media_path":urllib.parse.urlsplit(media).path,
     "src_origin_host":urllib.parse.urlsplit(media).hostname})
 except Exception as ex:d["error"]=repr(ex)[:450]
 r["pages"][name]=d
r["status"]="OFFICIAL_PUBLIC_PROFESSIONAL_VIDEO_INDEX_RECORDED_NO_WATCHING"
(O/"V083_OFFICIAL_TEACHER_ROOT_VIDEO_INDEX.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
print("V083_REAL_TEACHER_VIDEO_INDEX",json.dumps(r,ensure_ascii=False)[:25000],flush=True)
