# ANIMATION_VIDEO_MASTERY — Professional-First / No Reinvention Lock

Date: 2026-11-19. Status: **research rule, not an ART_PASS or new Blender experiment**.

## User directive (binding)

> Before getting stuck and inventing a solution, first find how working professionals solve that same problem. If a genuine solution already exists, study and adapt it instead of spending GitHub runs on unguided experimentation.

## Mandatory order, for all following research threads

1. **Diagnose precisely.** Identify the visible artistic defect and the tool/geometry limitation. Specify native project, before photos, provenance SHA and what improvement would look like.
2. **Professional source discovery FIRST.** Search official Blender Studio teacher lessons, CG Cookie / professional project case studies, official Blender documentation, authentic legally accessible video lessons and existing in-project lesson receipts. Prioritize exact problem over generic sculpting tips. Distinguish teacher-demo / verified text from community speculation.
3. **Study decisions, pitfalls and repairs BEFORE executing.** What object structure does the artist begin with? Why? Which tools, controls, order, alternatives and failure cases? Watch and analyze legally accessible video via the proven GitHub/ffmpeg workflow if available without credits. Do not say full AV was studied if only a page, snippets or screenshots were seen. Respect video rights and do not redistribute unlicensed video.
4. **Reuse what already works.** Search `/ANIMATION_VIDEO_MASTERY/INDEX_CURRENT.md`, relevant recipes, antipatterns and existing GitHub Actions scripts. Do not write fresh utility code where a native Blender feature or existing workflow works reliably.
5. **Choose teacher-aligned minimal proof.** State approach, original asset, numeric/art gates, known problems, expected visible change, source links, acceptance/stop criteria and how to compare before/after. One small implementation attempt after teacher work; a narrow repair only when the exact failed assumption is diagnosed.
6. **Separate reality from assertions.** NATIVE/MECHANICAL proof, repeat proof, documented source study, ART self-review and INDEPENDENT professional ART review are different gates. Numeric or pixel pass never equals a convincing animal/character. Keep ART_HOLD unless honestly approved.
7. **Capture knowledge and failures.** Each new method or anti-pattern gets proof, provenance, recipe, QA and Library handoff. Only update INDEX after Library upload/readback/SHA checks.

### Current concrete intervention — V080 / African savanna elephant ear

**Existing source-locked evidence:** V079 authored thick solid ellipsoid-based membrane, output SHA `b04204cd78581b7ebe95731d9ccc3f61ed454d35ebe3ed923d80b08b148a9aea`, +20.2655% volume warning. V080 2 independent native GitHub runs `44526139459` and `44526539169`: outer thickness reduced ~52%, volume -24.9931%, root world displacement 0, 148 head/ear triangle crossings preserved, TECH proof. Independent professional art review NOT achieved; ear still visibly inflated/rigid, root not an organic connection. Two runs are NOT proof that shrinking a closed oval mesh was the right artistic *workflow*. Do not keep blindly tweaking percentage.

**Already documented professional path — examine before any V081 geometry change:**

- Julien Kaspar / Blender Studio, *Sculpting Multiple Objects* (free public lesson text): make a controlled low-poly open/surface base mesh for thin structures; add Subdivision Surface and Solidify for thickness; apply object scale; keep components independent while shaping big forms; use Grab/Smooth and defer remeshing/details. https://studio.blender.org/training/blender-fundamentals-45-lts/using-multiple-objects/
- Official Blender manual, **Solidify Modifier**: generates thickness on a surface; supports vertex group-weighted thickness and rim options. https://docs.blender.org/manual/en/5.0/modeling/modifiers/generate/solidify.html
- CG Cookie professional case study, *Modeling a cute Robin Hood 3D character*: preserve adaptable blockout copy, apply scale and modifiers in sensible order, shape separate ears, defer Boolean / Voxel Remesh until appropriate, then sculpt the seam; thin ear rim after major forms. https://blog.cgcookie.com/posts/modeling-a-cute-robin-hood-like-character-in-blender-2-81/
- Blender Studio Kaspar sculpt critique on thin ear surfaces: sculpting very thin opposing surfaces can unintentionally affect both faces, so do not equate *thinner* with automatically better; consider base thickness, falloff and view. https://studio.blender.org/training/stylized-character-workflow/5d3a1bd54bc3ff1bb9513d3e/
- Blender Artists 2023 discussion *How do you model animal ears in sculpts?*: corroborating community recommendation to model separate thin parts, position and shape first, only then join using Boolean and sculpt transition. Community, not independently verified expert proof. https://blenderartists.org/t/how-to-you-model-animal-ears-in-sculpts/1484040

**Correct next method decision, not yet executed:** Evaluate whether to REBUILD the ear as a single editable mid-surface with non-destructive variable-thickness Solidify + root topology, instead of continuing to compress a pre-existing closed ellipsoid. Important: Solidify is NOT a magic way to fix an already-closed volumetric mesh; to apply it we need an appropriate (possibly retopologized) open surface. Validate that upper/lower planar proportions, front/3/4 and side thickness visibly match African savanna elephant reference before attempting skull integration. Do not claim that an unobserved video was watched, nor that this alternative has passed until native and artistic proof exists.

**No further gratuitous experiments:** Search/watch a real professional demonstration of a comparable thin-flap + rooted attachment first. If none accessible, state source coverage and HOLD instead of pretending a self-invented solution is professional practice. GitHub Actions has already been proven for legally permissible video capture/study without paid credits; check existing recipe/workflow rather than starting a new vendor flow.

**Protected:** GS001/V046; prior source artifacts; all original CC0 photographic references. Keep `ART_HOLD`. Current latest V079 INDEX73 remains canonical until V080 proper closeout; do not inflate version merely for policy note.