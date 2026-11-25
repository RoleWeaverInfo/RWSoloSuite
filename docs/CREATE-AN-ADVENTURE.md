# From ChatGPT story and floorplans to a playable NWN module

Start by opening the included **The Emberseal of Briarwatch** example. It contains a complete story, fifteen named character profiles, two linked quests and three annotated floorplans for an indoor keep, walled market/road area and cave. Inspect these in the dashboard before creating your own project. Fresh installations load it automatically; existing installations can use **Load Emberseal example**. The example is already compiled and downloadable in **Build & share**. See its [guide](EMBERSEAL.md). Use a new project ID and module filename when making a separate adventure.

Start small: a short quest, a handful of key characters and two or three areas. ChatGPT helps draft the story, character notes and labeled floorplans. Role Weaver imports the images and uses its own configured API model to turn them into area proposals, NPC profiles, encounters and native NWN resources. A ChatGPT conversation is not itself a Studio project file.

## 1. Draft the adventure in ChatGPT

Copy this prompt and change the details:

> Help me design a 30–60 minute Dungeons & Dragons-style single-player adventure for Neverwinter Nights: Enhanced Edition. Target a level 3 player with one optional companion. Use three areas: a small keep, a walled stone market courtyard with a gate opening onto a farm/forest road, and a cave. A queen asks for the recovery of a stolen royal seal and promises a reward. Include three distinct outdoor encounters, a cave encounter and a final boss. Return: a concise story summary; what the player knows at the start; the quest's stages and completion conditions; clues and optional approaches; rewards; and a table of area connections. Keep locations physically plausible and the quest completable without live AI. Do not invent engine resource IDs or claim that AI dialogue alone transfers items.

Refine the answer until the route and quest make sense. Decide player level, party assumptions, difficulty, tone and scope before building many rooms. Keep the summary and quest stages in a document alongside your floorplans.

## 2. Give every important character useful information

Ask ChatGPT:

> For every NPC and encounter creature in this adventure, write a compact profile: name and short alias; role and home area; appearance; personality and speaking style; goals; facts they know; facts they do not know; secrets and conditions for revealing them; relationship to the player; quest involvement; and whether they speak or communicate nonverbally. Include a queen, two assistants, guards, a baker, armorer, wizard, cleric, peasants and the cave adversaries. Mark merchant and recruitable-companion roles. Give merchants sensible stock categories rather than invented NWN resrefs. Keep each profile consistent with the quest. Avoid modern or out-of-world knowledge.

In Studio, put relevant information into each character's profile/knowledge fields. Give characters only the information they should know. Configure merchant, companion, patrol and ambient conversation options deliberately. Creature conversation can be enabled/disabled by the creator; animals can use nonverbal behavior.

## 3. Make one clear floorplan per area

Ask ChatGPT to produce a drawing brief, then create the image with an image-capable tool. Use a top-down plan rather than a perspective scene. Example prompt:

> Draw a legible, orthographic top-down floorplan for a modest stone keep interior. Use a labeled 1-metre grid, a north arrow, metre dimensions, and a legend. Show an entrance vestibule, guard alcove, clerk's office, audience hall and side passage. Mark each doorway and its clear width, both sides of every connection, and the exterior destination of each exit. Enclose interior rooms with continuous walls. The throne faces the entrance across a red carpet. Add a raised dais with labeled elevation and steps, benches, a clerk's desk, weapon rack, storage chest, banners and braziers. Draw furniture at believable footprint sizes, with facing arrows. Keep walking routes clear. Label required objects separately from optional decoration. Use concise readable labels and no perspective, pools or decorative rooms that were not requested.

For outdoor areas, specify boundaries, terrain, elevation, road widths, gate openings, vegetation density and open travel routes. A courtyard needs continuous walls and an actual gate; a forest should not be interpreted as a set of indoor rooms. For caves, show enclosed chambers and connecting tunnels. For deserts and winter areas, identify the surface, landmarks and visibility. Use different plans for different environments rather than stretching one throne-room template across them.

An annotated plan with a clear scale usually works better than a richly painted scene. Include a text description as well. NWN tiles, available models and walkmeshes constrain the result; expect to review and adjust it.

## 4. Create the project and its areas

1. Start Studio and configure your NWN paths and AI authoring model in **Local settings**. Use a model with image input for floorplan interpretation. Choose your gameplay model separately.
2. Create a project. Add the story summary, player/party expectations and quest information in the adventure design fields. Save it.
3. In **Areas & rooms**, create an area or work on a standalone room design first. You can develop and refine room designs before linking them into an adventure.
4. In **Floor plans and visual references**, upload the image and add its description. Click **Generate from this floor plan**.
5. Review the AI's **objects and scale** checklist before building. Correct missed rooms, dimensions, required furniture and exit locations. You do not need to type the whole checklist yourself; use the generated one as a draft.
6. Apply the reviewed proposal and build/update the area. Generation is a proposal, not a guarantee that every image detail has been reproduced.

## 5. Refine rooms and encounters

- Use the visual area editor to zoom/pan, select furnishings, inspect their information, rotate them and adjust placement. Save/update the generated room after editing.
- Check wall boundaries, room dimensions, object footprints, facing and vertical placement. Keep doors, stairs and travel routes unobstructed.
- Use **Layouts & connections** to join rooms and area exits. Each connection needs a valid destination. Use physical doorways where required; a label or freestanding wall alone does not enclose a room.
- Use **Materials & lighting** presets appropriate to castle, cave, forest, desert or winter environments, then adjust the supported surfaces/lights.
- In **Assets & placements**, review the full furnishing list, including generated objects. If a build reports “no safe space”, move/remove the named item or increase usable space; regenerating unchanged clutter will not solve it.
- Point the visual asset catalog at your HAK folder or loose resources to index downloaded content. Optional assets are considered when useful. Include required HAK dependencies when sharing, only where their licenses allow redistribution.
- Add the story's NPC profiles and encounters. Review enemy types, quantities, starting positions, patrols, companion roles and party capability/difficulty settings. Keep dialogue clues and quest objectives consistent with the actual placed creatures/items.

## 6. Edit the story and missions visually

Version 1.3.0 includes a visual editor in **Quests & endings**. It uses the same mission definitions as AI generation and the native module builder.

1. Expand **Generate missions with AI**, describe the missions you want, and generate a proposal. Review it and choose **Apply proposal to draft**. Applied mission or full-adventure proposals open the mission editor automatically.
2. Use **Adventure overview** to see main missions, optional missions, prerequisites and the adventure ending. Select a mission to edit its name, purpose, starting NPC, prerequisite missions, completion text and gold/XP rewards. All selected prerequisites must finish before that mission starts. All main missions must finish before the adventure ending appears.
3. Select **Mission objectives** to inspect that mission's executable paths. Click a card to edit its instruction, action and target: talk to an NPC, visit a room, retrieve an item, defeat an encounter, resolve an interaction, or present a player decision in native dialogue.
4. Add objectives or decisions with the map buttons. Change **Next objective** / **Then**, or use **Pick destination on map** and click a destination card. A blank destination means mission completion. Decisions have two to six player choices. New objectives added after a decision need an explicit incoming connection. **Make first objective** changes the entry point; review the resulting paths.
5. Drag the map background to pan. Use **+**, **−**, or Ctrl + mouse wheel to zoom. **Fit** shows every path; **Focus** enlarges the selection. **Jump to objective** finds a card in a long mission. **Story details** edits the summary, storyline, opening and ending. **Undo** / **Redo** restore mission edits during this editing session; they are not saved project history. Applying another AI proposal starts a fresh mission undo history; the AI panel retains its existing proposal undo control.
6. Resolve highlighted missing targets, unreachable objectives and invalid connections. Loops are rejected when linking objectives. Removal requires confirmation; removing an objective reconnects its incoming paths as explained in the confirmation. A mission referenced by other adventure content cannot be removed until those references are cleared.
7. Choose **Check adventure** for full checks, then **Save project**. Rebuild to include edits in the playable module. Editing the map does not change an already exported module or an existing NWN save.

Targets come from the existing characters, rooms, encounters and items in your draft. Add those in their respective dashboard sections when needed. Imported adventures use the shared visual editor under **Module Conversion → Missions & storyline**. Original-journal notes and arrows document your review. Where an audited adapter is available, **Copy to editable Studio mission** offers optional executable objective and reward edits; original control remains the default until you opt in. The first adapter supports Snow Hunt's Rival Ogre Mages. Start with the [conversion walkthrough](CONVERT-A-MODULE.md), or see [native mission review and conversion](MODULE-ANALYSER.md#optional-studio-control-rival-ogre-mages).

## 7. Build, inspect and playtest

The **Module filename** supports up to 64 characters before `.mod`: lowercase letters, digits and underscores, starting with a letter. Omit the extension, for example `the_emberseal_of_briarwatch_ai`. This is separate from the adventure title displayed in NWN. Internal resource IDs (scripts, areas and blueprints) still have NWN's 16-character limit.

Use **Build & share** to generate the `.mod`, matching `.rwproject.json`, dependencies and shareable ZIP. Resolve validation errors before publishing. On Windows, use **Open in Aurora** to inspect an editable module copy. On Mac/Linux, transfer the exported module and required HAKs to a Windows computer with Aurora. Keep a separate copy of hand-edited Aurora work; a new Studio build does not merge arbitrary toolset edits back into the project.

Install with NWN closed, start Role Weaver, register the matching adventure profile, and start a **new game** in NWN. Test:

1. Entry location, every doorway, room transition, area exit, staircase and return route.
2. Quest start, clues, encounters, quest item recovery, return to the quest giver and reward.
3. Native quest menus with AI unavailable, plus AI conversations when enabled.
4. Merchant trades, companion selection, companion inventory and requested container actions.
5. Walkable routes around furnishings, encounter difficulty, lighting and readable dialogue.

Ask ChatGPT to review the final story/connection tables for inconsistencies, but use actual playtesting to verify game behavior. Share the complete exported adventure ZIP and its dependency instructions. Your API keys, local workspace and copyrighted game installation must not be distributed with it. Players supply their own keys and run the service locally.

See [Installation](INSTALLATION.md) and [Player guide](PLAYER-GUIDE.md) for the instructions to give testers.
