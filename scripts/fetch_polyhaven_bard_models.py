import json, pathlib, urllib.request, hashlib, os

ASSETS=["wooden_stool_01","wooden_table_02","wine_barrel_01","wooden_lantern_01"]
OUT=pathlib.Path("/tmp/bard_stage_v7/models")
OUT.mkdir(parents=True,exist_ok=True)
UA="BardStudioModelFetcher/1.0"

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=60) as r:
        return json.load(r)

def download(url,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=180) as r, open(dst,"wb") as f:
        while True:
            chunk=r.read(1024*1024)
            if not chunk: break
            f.write(chunk)
    h=hashlib.sha256(dst.read_bytes()).hexdigest()
    return {"path":str(dst),"url":url,"bytes":dst.stat().st_size,"sha256":h}

manifest={}
for aid in ASSETS:
    data=get_json(f"https://api.polyhaven.com/files/{aid}")
    try:
        meta=data["blend"]["1k"]["blend"]
    except Exception:
        raise RuntimeError(f"1K blend not found for {aid}; top keys={list(data.keys())}")
    adir=OUT/aid
    blend_name=pathlib.Path(meta["url"]).name
    info={"blend":download(meta["url"],adir/blend_name),"includes":{}}
    for rel,dep in (meta.get("include") or {}).items():
        info["includes"][rel]=download(dep["url"],adir/rel)
    manifest[aid]=info
    print("FETCHED",aid,blend_name,len(info["includes"]),flush=True)

(OUT/"POLYHAVEN_MODEL_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps({k:{"blend":v["blend"]["bytes"],"includes":len(v["includes"])} for k,v in manifest.items()},indent=2))
