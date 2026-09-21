import argparse, hashlib, json, pathlib
import cv2
import numpy as np

EXPECTED_SHA="7e28541eac025b511b589644a969d2e383a50dadaf0ce56fa9b2246a298fbb18"
EXPECTED_SIZE=(1024,1536)

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):
            h.update(c)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True)
    ap.add_argument("--outdir",required=True)
    args=ap.parse_args()
    src=pathlib.Path(args.source); out=pathlib.Path(args.outdir); out.mkdir(parents=True,exist_ok=True)
    actual=sha256(src)
    if actual!=EXPECTED_SHA:
        raise RuntimeError(f"Source hash mismatch: {actual} != {EXPECTED_SHA}")
    img=cv2.imread(str(src),cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError("Could not read source image")
    H,W=img.shape[:2]
    if (W,H)!=EXPECTED_SIZE:
        raise RuntimeError(f"Source size mismatch: {(W,H)} != {EXPECTED_SIZE}")

    m=np.full((H,W),cv2.GC_BGD,np.uint8)
    poly=np.array([
      [435,48],[365,75],[325,125],[300,220],[255,315],[225,450],[180,620],[160,830],[120,1040],[85,1160],
      [125,1180],[185,1140],[240,1040],[280,960],[330,980],[360,1200],[285,1360],[315,1450],[430,1510],
      [520,1520],[610,1490],[715,1510],[760,1435],[720,1310],[690,1160],[745,1010],[840,1170],[925,1270],
      [950,1230],[915,1050],[880,850],[845,660],[810,500],[780,350],[720,250],[660,140],[590,80],[530,45]
    ],np.int32)
    cv2.fillPoly(m,[poly],cv2.GC_PR_FGD)
    for x0,y0,x1,y1 in [
      (430,100,590,270),(350,330,690,740),(300,470,660,700),
      (330,750,690,1100),(340,1120,680,1420)
    ]:
        m[y0:y1,x0:x1]=cv2.GC_FGD
    b=18
    m[:b,:]=cv2.GC_BGD; m[-b:,:]=cv2.GC_BGD; m[:,:b]=cv2.GC_BGD; m[:,-b:]=cv2.GC_BGD
    bgd=np.zeros((1,65),np.float64); fgd=np.zeros((1,65),np.float64)
    cv2.grabCut(img,m,None,bgd,fgd,8,cv2.GC_INIT_WITH_MASK)
    mask=np.where((m==cv2.GC_FGD)|(m==cv2.GC_PR_FGD),255,0).astype(np.uint8)
    num,labels,stats,_=cv2.connectedComponentsWithStats(mask,8)
    if num>1:
        idx=1+np.argmax(stats[1:,cv2.CC_STAT_AREA])
        mask=np.where(labels==idx,255,0).astype(np.uint8)
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8),iterations=1)
    mask=cv2.GaussianBlur(mask,(0,0),1.2)
    rgba=cv2.cvtColor(img,cv2.COLOR_BGR2BGRA); rgba[:,:,3]=mask
    rgba_path=out/"BARD_CHARACTER_MATTE_V1_RGBA.png"
    cv2.imwrite(str(rgba_path),rgba)
    report={
      "proof_id":"BARD_CHARACTER_MATTE_V1",
      "source_sha256":actual,
      "source_size":[W,H],
      "matte_sha256":sha256(rgba_path),
      "foreground_area_ratio":float((mask>127).mean()),
      "production_crop_xyxy":[115,35,930,1040],
      "qualification_scope":"upper_body_medium_and_close_integration_only",
      "lower_body_rule":"must_be_hidden_by_stage_front_occlusion"
    }
    (out/"BARD_CHARACTER_MATTE_V1_VALIDATION.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
