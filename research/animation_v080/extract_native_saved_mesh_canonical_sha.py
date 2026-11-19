# SPDX-License-Identifier: GPL-2.0-or-later
"""V080 independent native Blender saved-geometry equivalence extractor.
Open existing .blend with Blender 5.2.2 and canonically hash every actual
mesh WORLD vertex and triangle topology. No art modification; NO SAVE.
Different .blend container bytes ≠ different geometry; prove, don't infer.
"""
import bpy,pathlib,hashlib,json,struct,sys,bmesh
out=pathlib.Path(sys.argv[-1])
need=["V080_NEAR_GRADIENT_THIN_EAR","V080_FAR_GRADIENT_THIN_EAR",
      "V079_NEAR_SAVANNA_FLAP_CANDIDATE","V079_FAR_MIRRORED_SAVANNA_FLAP_CANDIDATE","04_HEAD"]
r={"schema":"V080_NATIVE_SAVED_MESH_SHA256_EXTRACT","version":bpy.app.version_string,
   "art_approved":False,"objects":{}}
assert bpy.app.version_string.startswith("5.2.2")
for name in need:
 ob=bpy.data.objects[name]
 assert ob.type=="MESH"
 h=hashlib.sha256()
 for v in ob.data.vertices:
  p=ob.matrix_world@v.co
  h.update(struct.pack("<ddd",float(p.x),float(p.y),float(p.z)))
 topo=hashlib.sha256()
 for f in ob.data.polygons:
  topo.update(struct.pack("<I",len(f.vertices)))
  for vi in f.vertices:topo.update(struct.pack("<I",int(vi)))
 bm=bmesh.new();bm.from_mesh(ob.data)
 try:
  vol=abs(bm.calc_volume(signed=True))*abs(ob.matrix_world.determinant())
  nmb=sum(1 for e in bm.edges if not e.is_manifold)
 finally:bm.free()
 r["objects"][name]={"verts":len(ob.data.vertices),"faces":len(ob.data.polygons),
  "world_vertex_sha256":h.hexdigest(),"topology_sha256":topo.hexdigest(),
  "volume":vol,"non_manifold_edges":nmb}
r["packed_images"]=sorted([im.name for im in bpy.data.images if im.packed_file])
assert len(r["packed_images"])>=3
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
print("V080_EXACT_SAVED_NATIVE_MESH_SHA256",json.dumps(r,ensure_ascii=False)[:6000])
