import bpy, json, pathlib, os
from mathutils import Vector

BLEND="/tmp/v8src/bard_stage_v7/BARD_STAGE_V7_MASTER.blend"
OUT=pathlib.Path("/tmp/bard_stage_v8")
OUT.mkdir(parents=True,exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene=bpy.context.scene
scene.render.resolution_x=960
scene.render.resolution_y=540
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
try:
    scene.view_settings.look='AgX - Medium High Contrast'
except Exception:
    pass
scene.view_settings.exposure=-0.98

cam=scene.camera
if cam is None:
    raise RuntimeError("No active camera in V7 master")

proxy=[o for o in bpy.data.objects if o.name.startswith('proxy_')]
if not proxy:
    raise RuntimeError("No proxy objects found in V7 master")

shots=[
  {"id":"S1_MASTER","loc":(0.45,-10.65,2.92),"target":(-1.20,1.25,1.55),"lens":45},
  {"id":"S2_MEDIUM","loc":(-0.10,-8.55,2.78),"target":(-1.22,1.26,1.62),"lens":53},
  {"id":"S3_CLOSE","loc":(-0.62,-6.75,2.66),"target":(-1.22,1.28,1.78),"lens":62},
  {"id":"S4_RETURN","loc":(0.12,-9.10,2.84),"target":(-1.18,1.27,1.60),"lens":49},
]

def aim(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

requested=os.environ.get("SHOT_ID","ALL")
selected=[s for s in shots if requested=="ALL" or s["id"]==requested]
if not selected:
    raise RuntimeError(f"Unknown SHOT_ID={requested}")

for sh in selected:
    cam.location=sh["loc"]
    cam.data.lens=sh["lens"]
    aim(cam,sh["target"])
    for o in proxy:
        o.hide_render=True
    scene.render.filepath=str(OUT/f'{sh["id"]}_ENV.png')
    bpy.ops.render.render(write_still=True)
    for o in proxy:
        o.hide_render=False
    scene.render.filepath=str(OUT/f'{sh["id"]}_PROXY.png')
    bpy.ops.render.render(write_still=True)

(OUT/"BARD_STAGE_V8_CAMERAS.json").write_text(json.dumps({"requested":requested,"shots":selected},indent=2))
print(f"BARD_STAGE_V8_CAMERAS_OK requested={requested}")
