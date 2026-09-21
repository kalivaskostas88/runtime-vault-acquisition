import json, urllib.request

ASSETS=["wooden_stool_01","wooden_table_02","wine_barrel_01","wooden_lantern_01"]
UA="BardStudioModelProbe/1.0"

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

for aid in ASSETS:
    data=get_json(f"https://api.polyhaven.com/files/{aid}")
    candidates=[]
    for path,meta in walk(data):
        ps="/".join(path).lower()
        url=meta.get("url","")
        ul=url.lower()
        if any(ext in ul for ext in (".glb",".gltf",".blend",".fbx")):
            candidates.append({
                "path":"/".join(path),
                "url":url,
                "size":meta.get("size"),
                "include":meta.get("include"),
                "preferred":("1k" in ps or "_1k" in ul)
            })
    print("ASSET",aid)
    print(json.dumps(candidates[:30],indent=2))
