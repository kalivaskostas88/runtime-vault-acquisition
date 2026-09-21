import json, os, pathlib, urllib.request, hashlib

ASSETS=["medieval_wall_02","medieval_wood"]
OUT=pathlib.Path("/tmp/bard_stage_v6/assets")
OUT.mkdir(parents=True,exist_ok=True)
UA="BardStudioTextureFetcher/1.0"

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=60) as r:
        return json.load(r)

def walk(obj,path=()):
    if isinstance(obj,dict):
        if "url" in obj and isinstance(obj["url"],str):
            yield path,obj
        for k,v in obj.items():
            yield from walk(v,path+(str(k),))
    elif isinstance(obj,list):
        for i,v in enumerate(obj):
            yield from walk(v,path+(str(i),))

wanted_tokens={
    "diff":"diffuse",
    "nor_gl":"normal",
    "rough":"rough",
}
manifest={}
for aid in ASSETS:
    data=get_json(f"https://api.polyhaven.com/files/{aid}")
    entries=list(walk(data))
    chosen={}
    for p,meta in entries:
        ps="/".join(p).lower()
        url=meta.get("url","")
        if "1k" not in ps and "_1k" not in url.lower():
            continue
        if not url.lower().endswith((".jpg",".png")):
            continue
        for token,outname in wanted_tokens.items():
            if token in ps or token in url.lower():
                # Prefer jpg, and the shortest dependency path.
                score=(0 if url.lower().endswith(".jpg") else 1, len(url))
                prev=chosen.get(outname)
                if prev is None or score<prev[0]:
                    chosen[outname]=(score,url,meta)
    if "diffuse" not in chosen:
        raise RuntimeError(f"No 1K diffuse found for {aid}. paths={['/'.join(p) for p,_ in entries][:50]}")
    adir=OUT/aid;adir.mkdir(exist_ok=True)
    manifest[aid]={}
    for kind,(score,url,meta) in chosen.items():
        ext=".jpg" if url.lower().endswith(".jpg") else ".png"
        dst=adir/f"{aid}_{kind}{ext}"
        req=urllib.request.Request(url,headers={"User-Agent":UA})
        with urllib.request.urlopen(req,timeout=120) as r, open(dst,"wb") as f:
            f.write(r.read())
        h=hashlib.sha256(dst.read_bytes()).hexdigest()
        manifest[aid][kind]={"path":str(dst),"url":url,"sha256":h,"bytes":dst.stat().st_size}
        print(aid,kind,url,dst.stat().st_size,h,flush=True)

(OUT/"POLYHAVEN_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
