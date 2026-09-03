---
name: minimax-h3-handmade-reconstruction
version: 1.0.0
display_name: MiniMax H3 Handmade Reconstruction
description: Turn a reference image into a continuity-safe 15-second film showing one maker reconstructing its main subject by hand.
district: Creator District
pack: video-generation
tags: [minimax-h3, image-to-video, timelapse, continuity, provenance]
tier: core
layer: application
chains_from: [reference-image-intake, asset-rights-check]
chains_to: [video-generation, visual-verification, audit-receipt]
orchestrated_by: AGENTROPOLIS Creator Core
---

# MiniMax H3 Handmade Reconstruction

## Job

Create a 15-second reference-image-to-video prompt in which one maker visibly constructs the reference subject from scratch with continuous physical causality.

## Activate when

- "make this image come to life as a handmade build"
- "show how this subject was made"
- "turn this reference into a construction timelapse"
- "create an H3 build-from-scratch video"

## Requires

- One user-supplied or rights-cleared reference image.
- A selected coherent construction method: `clay sculpting`, `miniature fabrication`, `sewing`, `mechanical assembly`, `wood carving`, `metalworking`, or another method appropriate to the subject.
- A runtime with access to a compatible MiniMax H3 image-to-video endpoint. This repository does not imply that credentials or runtime access are present.

## Inputs

- `reference_image` — required image.
- `construction_method` — required; choose one coherent method.
- `subject_hint` — optional clarification when the main subject is ambiguous.
- `aspect_ratio` — optional provider-supported ratio.
- `seed` — optional reproducibility value.

## Canonical prompt

Replace `[CONSTRUCTION_METHOD]` and, only when needed, `[SUBJECT_HINT]`.

> A cinematic creation film follows one maker reconstructing the main subject [SUBJECT_HINT] shown in the referenced image completely from scratch using [CONSTRUCTION_METHOD] as the single continuous construction method. The referenced image defines the finished subject’s complete visible appearance, proportions, structure, materials, colors, clothing or surface details, and distinctive features; ignore its background, framing, lighting, and unrelated elements.
>
> Begin directly on an empty, clean virtual workbench. Use a stable front three-quarter overhead view that keeps the developing subject readable. There is one maker throughout, represented by the same consistent left and right hands and forearms. Show no more than two hands at once.
>
> From 0 to 14 seconds, the entire creation unfolds as a clearly accelerated timelapse with rapid, purposeful hand movement and restrained motion blur. Short jump cuts compress repetitive manual work only after each action has visibly completed. Every cut inherits the exact form and progress left by the previous action.
>
> 0-2 seconds: One hand enters already holding the first foundation material, armature, or base element appropriate to the referenced subject and places it at the center. The second hand steadies it as the maker establishes the initial supporting form.
>
> 2-8 seconds: The maker rapidly develops the subject’s major structure and volumes using [CONSTRUCTION_METHOD]. A living subject is sculpted as one continuous, non-gory form from armature to anatomy; a vehicle or machine is built from chassis to functional structure; an object is formed or assembled from its supporting body outward. Each additional material or component enters from outside the frame while firmly held by one of the maker’s hands, is carried to its destination, and remains under hand control until attached or shaped.
>
> 8-12 seconds: The same hands develop the recognizable outer form and reference-specific features. The maker sculpts, fits, wraps, stitches, fastens, carves, or polishes only where appropriate to [CONSTRUCTION_METHOD] and the subject. Facial features, hair, clothing, body panels, wheels, glass, surfaces, accessories, or equivalent defining elements emerge through visible hand and tool contact, never through spontaneous transformation.
>
> 12-14 seconds: The maker refines proportions, edges, joints, surface transitions, textures, colors, and distinctive details until the developing subject closely matches the referenced image. One hand stabilizes the form while the other performs each final adjustment with a hand-held tool.
>
> 14-15 seconds: The maker removes the last tool by hand and withdraws both hands. The timelapse returns to normal speed as the camera makes a restrained push toward the completed subject and holds on a clean final view.
>
> Materials and components do not need to be visible before use, but anything newly introduced must enter the frame already held by one of the maker’s hands. Nothing moves, assembles, appears, disappears, or changes material independently. Maintain one maker, one continuous subject, one creation position, and one category-appropriate construction method. No assistants, extra hands, detached anatomy, duplicated elements, magical morphing, drawing phase, software interface, cursor, menus, annotations, or text overlays.

## Governance

1. Confirm the reference image is user-provided, licensed, public-domain, or otherwise authorized for the intended use.
2. Do not infer ownership or permission from public availability.
3. Preserve the subject’s identity and material logic; do not silently alter protected brand or character details.
4. Label generated output as synthetic where the publishing surface requires it.
5. Record provider/model identifier, prompt version, input reference hash when available, seed, duration, construction method, output URI, and verification result.
6. Generated does not mean verified. Reject or retry outputs with extra hands, continuity resets, spontaneous components, identity drift, unsafe anatomy, text overlays, or an incomplete final reveal.

## Output

Return:

- compiled prompt
- provider parameters
- continuity checklist
- verification status
- retry notes, if any
- audit receipt fields

## Handoff

Send the compiled prompt and cleared image to the video-generation adapter. Send the resulting video to visual verification. Publish only after the receipt records the verification outcome.
