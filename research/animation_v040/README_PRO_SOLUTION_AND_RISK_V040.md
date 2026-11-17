# V040 — Επαγγελματικά τεκμηριωμένη δοκιμή πραγματικού αρνητικού οφθαλμικού όγκου

**Ημερομηνία:** 2026-11-17. **Status πριν το run:** `SOURCE_REVIEW_PASS / V039_ACTUAL_5_FRAME_VISUAL_REVIEW / V040_NATIVE_NOT_RUN / ART_HOLD`.

## Ακριβής πρωτογενής κατάσταση
- V039B: original closed cranial shell 11,650 vertices; native actual Draw brow stroke PASS 1,348 displaced, all 8 previews original, FRESH_RELOAD PASS; art never approved.
- Πραγματική εκ νέου οπτική επιθεώρηση V039B σε αυτό το νήμα: `BEFORE_FRONT`, `AFTER_FRONT`, `AFTER_THREE_QUARTER`, `AFTER_TRUE_PROFILE`, `AFTER_LOW` PNG from GitHub `research/animation-v039-original-brow-20261117`, binary fetched/visually inspected, not merely receipt. Findings: two protruding eye masses, jagged center medial seam, continuous lower lid-to-cheek tissue **absent**; features nose/lips/eye globes **absent**. This is an explicit ART_HOLD witness.

## Source-led solution, not copied mesh
- Blender 5.2 official Boolean manual: https://docs.blender.org/manual/en/5.2/modeling/modifiers/generate/booleans.html . Difference removes real volume; EXACT complex solver; manifold prerequisites.
- Blender 5.2 Remesh manual: https://docs.blender.org/manual/en/5.2/sculpt_paint/sculpting/tool_settings/remesh.html . Voxel remeshing changes topology, destroys data layers; **not used** in V040 micro proof because its added variable would confuse attribution.
- Julien Kaspar, Blender Studio, *Sculpting a complete Planar Head*: https://studio.blender.org/training/stylized-character-workflow/5d3a1bd54bc3ff1bb9513d3e/ (public page/text and illustration, not whole course watched). The 3D face needs intentional planes and anatomy, not placed-on masses.
- Julien Kaspar, *File 1 Head Sculpting Lessons*: https://studio.blender.org/training/stylized-character-workflow/5d3a1fe14980f083715e410f/ (public text, not paid video). Brows should in appropriate designs overhang lids, not be two separate donuts.
- V035 prior original AV: Aram Art selected W02 and W05 studied earlier; not a new video watch.

## Pre-execution known antipattern matrix
| ID | Trigger/cause | Preflight prevention/negative test | Stop/repair |
|---|---|---|---|
| AP040-01 | Boolean on open/nonmanifold shell → unpredictable intersections | Base topology all edges exactly 2; wrong manifold in `negative_preflight()` must be rejected | restore original closed mesh; do not guess |
| AP040-02 | Boolean UNION/intersect instead of DIFFERENCE → wrong sign | operation guard and deliberate UNION negative rejection | stop before modification |
| AP040-03 | Solver mismatch FLOAT for close coplanar geometry | EXACT guard and deliberate FLOAT rejection | use official Exact on valid meshes |
| AP040-04 | Cutters insufficiently intersect head → no real cavities | true camera-front-ray center-depth gain required on *each* side | adjust cutter only if new evidence; retain failed first run |
| AP040-05 | Cutters damage other head parts | four remote ray positions frozen + unchanged beyond tolerance | stop; re-evaluate dimensions |
| AP040-06 | Beautiful shaded dents misread as anatomical approval | independent topology/raycast, four before/after fixed views; ART_HOLD | build original character reference and tissue volumes in future |
| AP040-07 | Voxel remesh erases data layers, changes topology, obscures cause | no remesh at all in this scope; explicitly future separate trial | maintain original source and check original mesh |
| AP040-08 | V039 blink/eyelid gate inherited | statuses fresh NOT_RUN; no rig/retopo | separate fresh integration before any inheritance |

## Locked experiment
One dominant changed mechanism: two symmetric **actual Boolean Difference ellipsoid cavities** on a fresh regenerated original V039 *pre-sculpt* closed cranial mesh (NOT the flawed post-brow V039B output). No artist-owned mesh copied. Both cuts are one same method repeated bilaterally. Independent frozen camera 4× before and 4× after renders, exact raycast inwards depth at ±0.44 z=.44, remote control samples at four positions, bmesh topology components/boundaries, actual `.blend`, sha256, source. The surfaces are only **anatomical teaching cavities**, not complete eyelids/eyes/face. `GS001_UNTOUCHED`, `ART_HOLD` unconditionally. On failure do not promote.

## Open risks and limits
- No signed/final original four-view artist character sheet exists. Therefore **full art sculpt is design HOLD**; the V040 run can only prove a CSG orbital cavity mechanism in a synthetic teaching fixture.
- Screenshot evidence from Blender Studio reference belongs to original author; do not redistribute/copy mesh. Cite source page.
- Native Blender execution and artist QA statuses must be filled only from later actual receipts and visual inspection; no future run may be claimed now.