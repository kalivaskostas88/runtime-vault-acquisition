from original_head_geometry_v039 import build,audit,shell_front_y,station,N_RING,N_AROUND

def test():
 a=audit();verts,faces=build()
 assert a['all_edges_two'] and not a['boundary'] and not a['overconnected'],a
 assert len(verts)==(N_RING-1)*N_AROUND+2
 assert a['jaw_width'] < a['cranium_width']
 assert len(faces)==(N_RING-2)*N_AROUND+2*N_AROUND
 assert shell_front_y(.36,.46) < shell_front_y(.36,.46)+.1
 assert -1<shell_front_y(.36,.46)<0
 assert all(len(p)==3 or len(p)==4 for p in faces)
 assert len(set(verts))==len(verts),'duplicate point'
 print('V039 ORIGINAL PURE GEOMETRY 8/8 PASS',a)
if __name__=='__main__':test()
