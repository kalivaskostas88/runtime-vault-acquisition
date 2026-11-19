# CC0 visual source inspection, no third-party geometry copied.
# Julien Kaspar professional workflow: Blender Fundamentals 4.5 LTS / Basic Sculpting;
# CC0 reference: Poly Haven "Carved Wooden Elephant", Greg Zaal.
import pathlib,requests,hashlib,json,io
from PIL import Image,ImageOps,ImageDraw,ImageFont
out=pathlib.Path("v068_reference");out.mkdir(exist_ok=True)
source="https://polyhaven.com/a/carved_wooden_elephant"
refs={}
canvas=Image.new("RGB",(1600,980),"#f5f5f5")
d=ImageDraw.Draw(canvas)
def get(name):
    url=f"https://cdn.polyhaven.com/asset_img/renders/carved_wooden_elephant/{name}.png?height=750&quality=95"
    r=requests.get(url,timeout=30,headers={"User-Agent":"ANIMATION_VIDEO_MASTERY V068 research/educational CC0"})
    r.raise_for_status()
    im=Image.open(io.BytesIO(r.content)).convert("RGB")
    f=out/(name+".png");f.write_bytes(r.content)
    refs[name]={"url":url,"sha256":hashlib.sha256(r.content).hexdigest(),"bytes":len(r.content),"size":im.size,"mime":r.headers.get("Content-Type")}
    return im
for i,name in enumerate(("orth_front","orth_side","orth_top","preview")):
    im=get(name)
    thumb=ImageOps.contain(im,(740,420))
    x=20+(i%2)*800+(740-thumb.width)//2
    y=35+(i//2)*475+(420-thumb.height)//2
    canvas.paste(thumb,(x,y))
    d.text((35+(i%2)*800,12+(i//2)*475),name,fill="#111111")
canvas.save(out/"V068_LICENSED_CC0_ORTHO_SOURCE_REVIEW.jpg",quality=93)
receipt={"schema":"V068_REAL_CC0_REFERENCE_CAPTURE","source":source,
  "creator":"Greg Zaal","license":"CC0 per official Poly Haven website",
  "teacher_method":"Julien Kaspar / Blender Fundamentals 4.5 LTS / Basic Sculpting",
  "teacher_lesson_url":"https://studio.blender.org/training/blender-fundamentals-45-lts/basic-sculpting/",
  "license_note":"Reference images only; DO NOT use/download existing 3D mesh; original blockout required",
  "images":refs,"model_already_created":False,"independent_artist_approval":False,
  "files_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob("*.*")}}
(out/"V068_REFERENCE_CAPTURE_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
print("V068_CC0_REAL_SOURCE_READY",json.dumps(receipt,ensure_ascii=False),flush=True)
