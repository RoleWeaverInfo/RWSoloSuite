# RWSoloSuite — Role Weaver Module Studio 0.19.0

## Material and lighting presets (0.19.0)

Open **Areas & rooms → Materials and lighting**. Choose the surface finish and lighting mood independently, or use **Use recommended combination**. Adjust brightness, fog density and outdoor weather, then **Update generated area**. Color swatches show the palette; inspect final shading in Aurora or NWN. **Restore original look** returns to the existing surfaces and basic lighting. Existing projects keep their original appearance until a preset is selected. These edits work offline and do not require a model request.

| Area | Material choices | Lighting choices |
| --- | --- | --- |
| Castle | Grey stone/oak; pale limestone/dark oak; dark slate/walnut | Warm torchlit hall; cool stone hall |
| Cave | Earth/weathered rock; cool basalt | Dim amber cavern; blue cavern haze |
| Forest | Mossy floor; dry woodland floor | Soft daylight; moonlit woodland |
| Desert | Golden sand/sandstone; red sand/rust sandstone | Clear sun; warm dusk colors |
| Winter | Fresh snow/grey rock; blue frost/dark rock | Clear winter daylight; overcast snow flurries |

Dungeons also offer the castle finishes and cavern lighting. Brightness ranges from 0.35× to 1.6×; fog density is 0–80%. Lighting remains fixed for consistent atmosphere. Outdoor weather uses a 65% chance of rain or snow when enabled, so precipitation may start or stop during play. Interior presets cannot enable rain or snow. Area lighting changes ambient/directional colors, fog, skybox and native tile-light colors; existing furnishing light sources remain part of the room design.

Measured rooms get original floor/wall textures and coordinated wooden door finishes. Their stair/dais geometry, walkmeshes, furniture positions and authored carpet colors remain intact. Native areas retain their authored shapes, UVs, collision and full tile palette; finishes recolor selected ground/rock textures while preserving detail, mipmaps and transparency. Trees, water, props and custom furnishings keep their own finishes. Each area receives separate resource names, so a dry forest and a mossy forest can coexist in the same module. Native areas with a material finish now include a generated HAK; share the complete ZIP.

The native exporter modifies documented model name/texture fields without moving offsets, preserves animations and copies the matching WOK resources. DDS recoloring retains the original compressed texture resolution and alpha blocks, with TGA fallbacks. References: [NWN binary model parser](https://xoreos.org/doxygen/dd/d7a/model__nwn_8cpp_source.html), [NWN DDS formats](https://nwn.wiki/pages/viewpage.action?pageId=38175664). The copied retail desert bridge definition has its nonexistent door hook removed from its declared count; the installed game files remain unchanged. SET section ordering and CRLF validation still apply.

The separate **Throne room - materials and lighting** project / **rw_finish.mod** demonstrates pale limestone, dark oak fitted doors and warm light in the existing three-room layout. The previous grey-stone `rw_doors.mod` remains available for comparison. Start a new game to see the exported appearance; old saves retain their own area resources. Actual Aurora and in-game appearance require the user's check.

## Fitted doors and connected measured rooms (0.18.0)

Measured interiors now build native wooden doors and stone frames at both ends of a physical corridor. Width comes from each wall opening; automatic leaves use a single door below 1.8 m and double doors at 1.8 m or wider. Doors have native opening/closing animations, matching closed/open collision meshes and ordinary NWN interaction. This does not require AI Player or NWNX.

In **Areas & rooms → Room boundaries and scale → Wall openings**, use **Connect this opening to a room**, choose an existing room in the same area and its destination wall. The destination receives a matching opening if needed. Connected openings display their destination. Under **Room and area connections**, choose a working wooden door, framed opening or plain passage, and adjust height and single/double leaves. Use **Update generated area** to export the result. Facing openings must share a width; short gaps need aligned openings. Invalid routes that cut through rooms, undersized walls and raised doorway approaches are rejected. Existing native tiles and transitions between separate areas retain their previous behavior.

The exporter routes aligned connections directly between the measured wall apertures, including gaps smaller than a tile. Native doors are separate editable Aurora objects; frames belong to the generated tiles. Door hooks and their UTD blueprints let Aurora retain the fitted door identity. Generated HAK resources include original MDL/DWK/TGA assets, a merged `doortypes.2da`, and the measured tileset. The generated HAK has first priority while preserving every row and column in the selected effective door table. Keep the complete MOD/HAK/share ZIP together. Native format conventions were checked against installed assets and the [custom-door authoring tutorial](https://neverwintervault.org/article/tutorial/tutorial-creating-custom-doors).

The separate **Throne room - connected doorways** project keeps the original 10 × 20 m hall, 24 furnishings, carpet and dais. It adds two deliberately simple test destinations outside the drawing: a 10 × 8 m **Entrance Hall** to the south and a 6 × 8 m **Side Chamber** to the east. The entrance uses 2 m double doors and a short passage; the side connection uses 1.2 m single doors and a longer passage. Both connections are physical walking routes. Nothing teleports the player to another spot in the original room.

Start a **new game in `rw_doors.mod`**. You begin in the Entrance Hall. Open the north doors, enter the throne room, then use the east door near the dais to reach the Side Chamber. Check opening/closing, travel in both directions and companion following. The installed HAK is included, and the project can also be rebuilt/opened through Studio. Export and geometry checks are automated; Aurora and NWN runtime behavior still need the user's test. Old saves retain old area resources.

## Measured carpets and runners (0.17.0)

Floorplan analysis now extracts rectangular carpets as measured floor coverings, including their position, width, length, color and optional border. They appear in **Review objects and scale → Carpets and runners** and are marked as **Built area geometry** in the checklist. Their dimensions no longer depend on a short native rug model. Existing projects remain compatible.

In **Areas & rooms → Room boundaries and scale → Carpets and runners**, add or edit a carpet and use **Update generated area** to rebuild. X/Y locate its southwest corner in room-local metres; width runs east–west and length north–south. Colors are red, blue, green, purple, brown, cream and gold, with an optional gold or cream border. The map displays its actual footprint and color. Border width stays physically consistent, and the woven texture repeats at a fixed scale rather than stretching a rug image along the entire runner.

Carpets are nonblocking native tile geometry just above the floor, split at tile boundaries with continuous texture coordinates. They do not alter the walkmesh. A carpet may rest entirely on a flat platform; it must stop before stairs and cannot bridge a platform edge. This first version supports axis-aligned rectangles in measured interiors, not draped stair runners or freeform rugs. Change their dimensions in Studio and rebuild; Aurora receives the complete area, generated HAK, and editable MDL/TGA source resources rather than a separately movable rug placeable.

The separate **Throne room - red carpet** project replaces the old short rug with one red **2 × 14.1 m** runner at x=4–6 m and y=2–16.1 m, ending at the bottom dais step. The reference’s 2 m clear entrance space is retained. The dais and the other 24 furnishing placements remain unchanged. The installed test is **rw_carpet.mod** with its generated HAK; start a new game rather than loading an older area save. The complete share ZIP includes all generated resources. Actual Aurora/game appearance still needs the user’s check.

### Suggested next development steps

1. Door assemblies and connected-room tests: matching frames, working door leaves, explicit destination selection, and checks that every intended passage is traversable.
2. Material and lighting presets: coordinated floor, wall, wood, fabric and light choices, with separate treatments for interiors and natural environments.
3. A textured 3D authoring preview with a floorplan overlay, alignment guides, and direct placement/rotation tools. Keep the current Aurora export check as part of the workflow.
4. Placement by room purpose: furniture groups, wall alignment, usable desk surfaces, sightlines and protected movement paths, with local repairs that preserve approved work.
5. Reference tests for forests, caves, deserts and winter areas, then encounter placement that uses cover, entrances, patrol paths and party difficulty.

These are proposed follow-up stages, not features included in 0.17.0.

## Raised platforms and stairs (0.16.0)

Measured stone interiors now support rectangular raised platforms with stairs approaching from any cardinal side. Floorplan analysis extracts their position, upper footprint, height, step count, total run and width. The **Review objects and scale** checklist shows editable platform dimensions and marks the dais/flight as built geometry rather than searching for a pool, fountain or furniture substitute. The ordinary furniture checklist remains separate.

In **Areas & rooms → Room boundaries and scale → Raised platforms and stairs**, add or edit a platform in an existing room, then use **Update generated area**. The map shows its upper footprint and individual treads. Coordinates are metres from the room’s southwest corner; stair offset is measured along the selected platform edge, from west on north/south edges or south on east/west edges. Stairs extend outside the upper footprint. The controls and inference apply to measured interiors; natural outdoor terrain and native room groups retain their existing elevation geometry.

Visible stone treads use the specified riser height and depth. Their native WOK uses a continuous ramp to connect the surrounding floor to the upper surface; the floor beneath the dais is replaced, not overlaid. The same elevation calculation places furniture, NPCs, entry points, encounter waypoints and patrol destinations. **Height above floor** is an additional offset: do not enter the dais height again. Objects supported by furniture inherit that furniture’s raised height. Placement rejects blocked steps, obstructed landings and furniture straddling an edge; flat rugs can approach the bottom tread.

Platforms must fit inside the room, leave a 1 m bottom landing and 2 m headroom, and use rises no higher than 0.30 m, treads at least 0.15 m deep and slopes no steeper than 45°. This version supports one straight flight per rectangular platform, not curved stairs, stacked floors or arbitrary outdoor terrain sculpting. Export preserves the Aurora SET ordering/CRLF fix and includes the generated geometry HAK plus editable source resources. Coarse tile path nodes now follow connected WOK edges rather than assigning every tile a north-only dead end; see the [NWN path-node definitions](https://nwn.wiki/spaces/NWN1/pages/139689996/Tile+Path+Nodes).

The separate **Throne room - dais and stairs** workspace keeps the confirmed 25-object layout. Its `rw_dais.mod` test adds the reference’s 4 × 3 m dais at 0.45 m and three 0.15 m rises / 0.30 m treads across a 4 m stair width. Use a new game for this test; existing saves retain old area resources. The installed module and HAK, and the complete share ZIP, are generated locally. Aurora appearance and in-game stair traversal still need the user’s test.

## Aurora tileset compatibility fix (0.15.1)

The measured-geometry exporter in 0.15.0 appended new tile definitions after the group section and wrote Unix line endings. Aurora requires tile definitions before groups and Windows CRLF lines; a normal INI parser accepts the bad files, so the previous automated checks missed this compatibility error. Export now writes the required section order, keeps door/sound subsections with their tiles, and checks counts and line endings before packaging the HAK.

Refresh Studio and use **Update generated area** or **Open in Aurora** to rebuild an existing draft. No AI regeneration or new API request is needed. Previously exported MOD/HAK pairs and open Aurora copies retain the old format; use a freshly rebuilt copy. The new local **Aurora repair - latest throne room** project preserves the most recently opened generated design in a separate workspace, including its 25 objects. `rw_aurorafix.mod` is its offline test build.

## Measured walls and 3D placement (0.15.0)

New castle and dungeon floorplan analyses use measured stone interiors. Clear room width/depth is preserved in metres, including sub-tile rooms, instead of growing with the stock wall tiles. Floors, wall faces, walkmesh collision, minimaps and an Aurora palette are exported together in a generated HAK. Forest, desert, winter and natural cave designs retain native terrain; a cave may explicitly switch to rectangular stone walls.

**Areas & rooms → Room boundaries and scale** controls clear width/depth, wall height/thickness, passage width, and openings positioned along each wall. Existing drafts can choose **Use measured stone walls**. This mode and native room groups are alternatives. Room origins and corridor routing still use the tile grid; wall shapes are rectangular, not arbitrary tracing. Connect a wall to another room to make a passage. A drawn doorway without a destination becomes a short recess, not an invented exit.

**Precise object placement** adds elevation, model-axis rotation, 90° rotation buttons and **Rest on** relationships. Supported items use the measured parent top surface and move/rotate with it in the editor. Cyan outlines show rotated model bounds; drag positions snap to 0.1 m. Collision checks consider height, and reject objects outside walls, above wall height, blocking access or extending off a supporting surface. Model bounds approximate complex surfaces; Aurora remains the final place to inspect collision, textures and small height adjustments.

The placement model receives the floorplan, actual model previews with local-axis references, actual clear dimensions and support rules. One placement repair is allowed when validation fails. It does not rescale objects or manufacture missing rug assets. In 0.15.0 raised floors still required a native group; 0.16.0 adds the measured platform/stair geometry described above.

A separate **Measured throne room - spatial test** project and `rw_spatial.mod` preserve the original workspace. Its measured room is 10 × 20 m with south/east doorway recesses. A fresh authoring-model placement request aligned the four benches east–west and placed the writing supplies on the desk. This is a geometry/placement diagnostic, not a claim that all requested decoration or the entire floorplan is complete.

Use **Update generated area → Open updated area in Aurora** to inspect a rebuilt copy. Share the **complete ZIP**: measured areas need the generated HAK as well as the MOD. Aurora launch/install and Play Adventure handle these dependencies; manual installation must copy the included HAK files. Editable generated MDL/WOK/SET/ITP/TGA resources are included under `geometry-source/`.

Earlier release notes follow.

## Visual catalog and native groups (0.14.0 — historical)

In **Areas & rooms**, the **Visual asset catalog** now browses the installed NWN placeable appearances alongside imported HAK/ERF placeables. Search covers the whole catalog, with twelve actual-model previews per page. **Dimensions and preview** shows measured model bounds and alternate viewing angles. Invisible, effects-only, missing and unsupported meshes remain listed with an explicit unavailable-preview message. Previews omit textures, lighting, particles and animation; dimensions are visual geometry bounds, not collision bounds.

The floor-plan matcher receives numbered shape contact sheets for up to 48 retrieved candidates per request, plus dimensions and metadata. This is an AI image-cost bound, not an import/catalog size limit. Search splits native names such as `ThroneGood`, handles common furnishing synonyms and avoids duplicate model results from copied HAK appearance tables. Chosen model bounds drive rotated furnishing clearance instead of treating every imported object as a large table. A mismatch is disclosed; native placeables are not automatically rescaled.

Select a room or zone in the visual editor and choose **Choose native room / terrain group**. Groups preserve their complete tile matrix, quarter-turn rotation, authored doorway sides and fixed size. Castle rooms, dungeon/cave floor features, forest landmarks, desert features and winter features use their own installed tilesets. Compatible boundaries and native walkmeshes are checked before export; arrivals and patrol destinations avoid built-in obstacles. Groups requiring unsupported water, elevation, holes or terrain-edge combinations are disabled. Stairs/portals in a feature do not automatically create travel to another area. Custom HAK tilesets remain available for Aurora editing, not automatic group generation.

**Desert** and **Winter / snow** are now area types. Their generated base terrain is flat; arbitrary dunes, elevation and water transitions are not implemented. The same catalog/group workflow applies across environments, rather than being specific to throne rooms.

**Measured-floorplan limitation:** a free room's dimensions describe its nominal floor-tile footprint. Surrounding wall tiles can enlarge the actual clear interior. Native groups have tighter authored interiors but cannot be stretched. Review now calls out this distinction; this release does not claim exact tracing. The throne benchmark exposed remaining work on wall boundaries, prop orientation and vertical/surface placement, besides unavailable dais/step/rug geometry.

The local benchmark is saved separately as **Measured throne room - catalog test**. It is a diagnostic, not an approved visual match. Use **Update generated area**, then **Open updated area in Aurora** to inspect a copy. Your original workspace is preserved. Historical release notes follow.

## Selected-item highlight (0.10.5)

The updated `rw_invclick.mod` highlights the selected item with a bright yellow 3-pixel border and translucent yellow fill. Highlight bindings update without rebuilding the window or changing item transfers. Existing saves retain their embedded scripts; see the change in a new game when convenient. AI Player does not need restarting.

User playtest confirmed the preceding build's companion inventory, chest collection into companion storage, and transfer from companion to player. This cosmetic change still needs visual confirmation in-game.

## Current trial: inventory selection and placeholder fix (0.10.4)

Start a **new game** in **The Silent Bell - Inventory Click Fix** (`rw_invclick.mod`). AI Player 0.10.2 remains compatible; no backend restart is needed.

The item canvas click handler rebuilt the panel and cleared the selected item. It now ignores the trailing canvas click event after mouse selection, and changing quantity preserves selection. A transfer without a selected item gives an explicit instruction. Busy/unavailable transfers also explain why they cannot proceed.

Innate creature weapons/armor and creature-item abilities are excluded from the companion grid. Ordinary belongings remain visible. The large missing-image placeholder is replaced by an embedded transparent TGA; unknown item icons are omitted instead of drawing an error texture. An empty companion inventory now means there are no ordinary carried items or collected supplies.

Playtest: open the inventory and check there is no large red X, bite or eyeball-ability entry. Click an ordinary item and check its full name appears below the grid. Change quantity and verify the selection remains, then use Transfer selected. Also test dragging in both directions, collecting one potion, and closing/reopening. Protected/equipped belongings still cannot be transferred. Actual GUI interaction requires the user's in-game test.

## Previous trial: direct companion inventory panel (0.10.3)

Start a **new game** in **The Silent Bell - Companion Inventory Trial** (`rw_inventory.mod`). AI Player 0.10.2 remains compatible: these fixes are in the module's native scripts. Existing modules and saves are preserved.

**!companions → select your companion → Companion inventory - visual panel**, or ask the companion to show its inventory. This opens a custom native NUI panel with both inventories; it does not open your normal inventory or place a bag on the ground. Companion contents combine persistent carried storage with the actual creature's belongings. Equipped/protected gear appears with a red frame and cannot be transferred. Click an icon for its full name, count and restriction. Icons represent the item's base type, not its exact composite armor/weapon appearance; custom types without an installed icon retain their names.

Drag an item icon from one side to the other, or select it and press **Transfer selected**. **Quantity: one / whole stack** controls the amount. The panel refreshes after the native transfer confirms, usually within two module heartbeats. The native merchant shop is unchanged. Old player-held satchels remain separately accessible.

Chest errands no longer use the creature-only droppable-on-death flag for chest contents. Plot, cursed, unidentified, equipped and over-limit goods are still guarded. Ask for **one healing potion**: one should enter companion storage and two remain in the trial chest. Ask for the remaining stack to collect both. Item properties and local variables survive the escrow copy; item object identity changes. Inspection alone takes nothing.

Playtest the panel opening without a dropped object; item selection; dragging in both directions; the transfer button; one/whole-stack mode; chest counts; save/reload; companion dismissal and recovery; and Bram's shop. Native compilation and regression checks do not verify rendering or mouse coordinates: those still require the user's in-game test. If drag does not register, report whether the transfer button works.

## Previous trial: companion packs and chest collection (0.10.2)

Start a **new game** in **The Silent Bell - Companion Pack Trial** (`rw_packfix.mod`) with AI Player 0.10.2. Older modules and saves are preserved.

The failed potion errand was rejected by an owner-distance check even though the companion had reached the chest. Collection now requires the companion at the accessible chest, not the player. Whole items/stacks go to a persistent companion pack, using a save-local escrow and confirmed destination counts. Item properties and local variables are copied; object identity changes. Ambiguous delivery stops rather than retrying a possible duplicate. Inspection alone never takes items.

**Companion pack - item grid** opens a normal placeable inventory through the player's native chest interaction. It is separate from equipped creature gear and legacy satchels. Use **!companions → Recover companion packs / old satchels** after dismissing a companion. Native merchant stores are unchanged.

Playtest: summon Agathos; open its pack; drag an ordinary item in and out. Stand away from the healing chest, ask Agathos to inspect it, then ask it to collect the entire healing-supplies stack. After the confirmed report, check the chest is empty and the pack contains exactly three supplies. Save/reload and dismiss/resummon to check recovery. Check Bram's shop still opens. GUI interaction, actual transfers and save/reload need the user's in-game verification; compilation alone does not prove them.

## Previous trial: familiar inventory and merchant conversation fix (0.10.1)

Use **Play Adventure.cmd → New Adventure** for **The Silent Bell - Familiar and Merchant Fix** (`rw_tradefix.mod`). Existing modules/saves are preserved. The backend merchant correction also applies to existing rw_trade saves; the native familiar menu changes require a new game in this trial.

The merchant error was a conversation-processing bug, not a missing build: merchant policy was removed from the NPC profile before native stock context read it. The profile is now sanitized after stock context is prepared. Bridge errors distinguish build-loading failures from failures processing a conversation; sanitized diagnostics contain request/build identifiers and exception type, never dialogue or credentials.

**Companion inventory - item grid** now targets the actual party member or familiar (including Agathos), rather than redirecting familiars to the player's inventory. **Recoverable satchel - in your inventory** is a separate, explicitly labelled option; open the named bag in your own inventory. Items placed directly on a familiar are not covered by satchel recovery. Summons use the paired storage list instead of unexpectedly opening only the player inventory. A native summon two-pane item grid is not implemented.

Validation: **162 tests passed**, including a regression through native merchant dialogue, error classification, familiar-versus-satchel dispatch and native compilation (**44 scripts**). The recorded failed rw_trade merchant payload was replayed locally with a stubbed provider: it reached the provider request step successfully; no API call was made and no game state changed. Native familiar inventory rendering and trading still need the user's in-game check.


## Previous trial: visual companion storage and merchant trading (0.10.0)

Use **Play Adventure.cmd → New Adventure** for **The Silent Bell - Visual Trading Trial** (`rw_trade.mod`). This module needs AI Player 0.10.0+ for live merchant conversation. Old modules and saved games are preserved; start a new game to receive the new store resources.

Companions retain **Inventory - item grid**, **Satchel - item grid**, and the text-list fallback. Speak to Bram and choose **Browse goods**, or ask him through AI chat, to open NWN's native store with item icons and normal buy/sell controls. Use its item drag-and-drop and trade confirmation controls. NWN handles the original stock, player belongings and gold. Test one purchase and one sale, reopen the store, and save/reload to check persistence.

Native store prices use NWN item values and Appraise. Haggling supplies a bounded discount to the native store opening; its displayed prices remain authoritative. A discount applies for that open window; reopening checks the offer timer. AI dialogue lists observed store goods, including player buybacks, but does not invent an exact final price. Stock is finite with no automatic replenishment. These stores have unlimited buying funds, pay at most 5,000 gold per item, and charge 100 gold for native identification; NWN enforces its normal eligibility rules.

In Module Studio, **Characters → Merchant shop → Shop interface** selects **Native visual store - buy and sell** or **Text list - fixed prices, buy only**. New merchant definitions default to native. Existing projects without this field remain list shops to preserve authored prices. The per-item price fields apply only to list shops; native pricing does not silently promise those fixed prices. Switch an existing merchant to native and rebuild to use visual trading.

Validation: **160 tests passed**, including native-store resources, finite quantities without NPC duplicates, guarded custom purchase paths, observed buybacks without fabricated prices, and offline native-store compilation. **43 native scripts compiled**. GUI interaction and actual transactions still need the user's in-game playtest; the agent has not launched NWN or Aurora.


## Previous trial: native visual companion inventory (0.9.2)

Use **Play Adventure.cmd → New Adventure** for **The Silent Bell - Visual Inventory Trial** (`rw_inventory.mod`). Old saves retain their previous inventory scripts. Existing modules remain intact.

Select a companion with `!companions`, then choose **Inventory - item grid** for a recruited party member or **Satchel - item grid** for a familiar/summon. Party members use NWN's native inventory. For a familiar/summon, your inventory opens: open its named satchel and drag item icons between the bag and your inventory. The satchel remains yours when the creature disappears. Use NWN's native item controls for examining and arranging items.

**Inventory - text list (fallback)** retains the working custom transfer panel. `!companion <alias> inventory` also opens the visual interface; append `inventory list` for the fallback. The AI inventory action uses the visual interface too. Opening through the suite still requires companion ownership and inventory permission; the native panel follows engine item rules. Pending custom handoffs must finish before opening it.

Merchant trading retains the existing purchase panel. This update covers companion storage. Physical room doors and previous AI companion features are included. Native GUI behavior and drag-and-drop still require the user's in-game playtest.


## Previous trial: physical room doorways (0.9.1)

Use **Play Adventure.cmd → New Adventure** for **The Silent Bell - Physical Doorway Trial** (`rw_doorways.mod`). Start a new game; older saves retain their old maps. All previous modules are preserved.

Interior corridor connections now have actual paired stock doorway tiles and native doors that open onto continuous walkable terrain. There are no corridor teleport signs or corridor transition zones. Outdoor connections remain trails; separate areas retain their area transitions. Studio's preview marks each physical doorway at its exported position. Door frames in compact rooms are placed to avoid overlapping, and furniture/actors keep clear of their entrances. Existing AI conversation, companion chest handoff and visual inventory features are included.

Validation: **154 tests passed**, **43 native scripts compiled**, and real installed walkmesh triangles checked through every interior doorway in this compact trial. The checks also verify solid wall geometry beside the openings. This is not an in-game playtest: please test walking through the doors with companions, including the vault's adjacent exits.


## Previous trial: companion and passage update (0.9)

Start a **new game** in **The Silent Bell - Companion and Passage Trial** (`rw_companion.mod`) through `Play Adventure.cmd`. Exit NWN and restart an older AI Player first; this trial requires AI Player 0.9.0. Old saves keep their embedded dialogue and area resources.

- Familiar/summon native dialogue now offers **Talk freely with AI**, companion controls, visual inventory and the original companion dialogue. After choosing chat and closing dialogue, speak normally in Talk. `!end` finishes the conversation.
- Chest inspection reads actual contents after the companion reaches an unlocked, untrapped, permitted container. It no longer waits for a player container window. It does not advance treasure quests.
- Ask naturally to take or deposit an item. Stand within three metres of the chest for direct handoff. Only one unambiguous, identified, transferable whole item/stack is moved; equipped, protected, cursed, high-value and container items remain excluded. Ask for the whole stack when necessary. No item is cloned or held by an expiring summon. Ownership is checked before a success report.
- **Open visual inventory** uses NWN's native grid for party members. For familiars/summons, open the named companion satchel in your own inventory to drag items. The custom inventory panel remains available. Merchant purchasing still uses its existing panel.
- All connection endpoints now have actual exit zones; supported solid interior boundaries also have stock framed native doors. Corridor terrain remains present. Quest conditions still apply. Followers travel; companions ordered to stay remain behind.
- Under **Encounters → Curated room design**, select a room and a design, preview, then apply. This replaces only that room's decorative furnishings. Story objects and NPCs remain. Presets use sparse purposeful groups; Aurora remains the final visual editor.
- Character replies receive in-world instructions and a filter for common software/game self-references, including the reported failure text. This reduces immersion breaks; it is not a guarantee against every possible generated phrase.

Please test: native familiar/summon dialogue, free chat, chest inspection and reported contents, one-item take/put and stack clarification, native inventory drag/drop, every room connection in both directions, followers, and the revised furniture arrangements. **NWN/Aurora gameplay has not been run by the agent.**


## Previous trial: natural companion tasks (0.8)

Use **Play Adventure.cmd**, choose **New Adventure**, and select a character for **The Silent Bell - Natural Companion Trial** (`rw_natural.mod`). Older modules and saved games keep their embedded scripts; do not use an older save to test this update. AI Player 0.8.0+ is required. Existing modules, Aurora copies and saves are preserved.

Select a companion in `!companions`, choose **Talk freely with AI**, close the panel, then speak normally. Examples:
- "Go ask the merchant what swords he has for sale."
- "Could you look inside that chest and come back and tell me what you find?"

The AI selects one game-offered nearby object and an inspection or visit; the game rechecks exact object identity, ownership, creator/player permissions, speech mode, control, visibility and task availability. Ambiguous targets should prompt a question. A native **task started** receipt confirms dispatch. The companion must actually approach/open/ask and return before a report is confirmed. Contents are not read until the container is open. Locked, trapped or quest-gated containers remain unavailable. No purchase, theft, cross-area travel or quest advancement is added. Animals may inspect nonverbally but cannot conduct verbal visits. Precise commands and the task-selection menu still work without interpretation; natural interpretation requires live AI.

The old chest check incorrectly used GetObjectSeen, which the installed nwscript.nss documents as creature-only. Containers now use proximity and geometric line of sight plus the existing container/lock/trap/quest checks. Nearby observations include container names without exposing their contents.

Merchant controls use 550px content widths, companion controls 580px, and each inventory's contents 230px within separate scrolling panes. Width is applied to individual controls and group viewports only; enclosing row/column dimensions remain unconstrained. This replaces the 150px default widths seen in the screenshots while avoiding equal required parent/child dimensions. Rendering at the player's UI scale remains an in-game acceptance check.

Validation: 146 regression checks passed, including native compilation; five live AI checks passed for merchant phrasing, chest phrasing, negation, quoted speech and ambiguous containers. These language checks use a synthetic nearby scene and do not establish actual movement or GUI appearance. No NWN/Aurora launch performed by the agent.

## Earlier release notes and reference


## Launcher working-directory fix (0.7.3)

The launcher previously started nwmain.exe with the installation root as its working directory. NWN requires the binary directory (`bin/win32`). The reported 3221225477 / 0xC0000005 crash had zero entries in all three installed base-resource keytables, missing PriorityGroups.2da and failed shader/UI resources during initialization, consistent with that path error. The launcher now starts from the binary directory for both New Adventure and Load Saved Game; CheckOnly displays that directory. Errors show the hexadecimal code and actual log location instead of assuming Steam/installation damage.

Source: [Beamdog developer guidance](https://forums.beamdog.com/discussion/67102/instanced-self-contained-installations/p1?new=1).

Run Play Adventure.cmd again. No module rebuild, game reinstall, key change or saved-game conversion is needed for this launcher-only correction. Current test module remains rw_uifix.mod. All 22 launcher tests passed, including new/saved working-directory checks and signed/unsigned access-violation errors. Game processes were simulated; actual launch remains the user's acceptance test. No NWN or Aurora launch was performed by the agent.


## Window sizing correction (0.7.2)

The reported error from rw_errands.mod was: "Error constructing window from json. The constraint cannot be satisfied". This is a layout-constraint failure, not evidence of missing JSON window fields. The previous 0.7.1 field additions alone did not address that sizing conflict.

Removed equal required widths/heights on both enclosing rows and their leaf controls. Rows/columns now size flexibly, controls retain readable heights, and each inventory column has an independent scrolling viewport. Removed the inventory row's fixed 740-pixel height and fixed column widths. Native UI rendering remains for user acceptance; regression checks cannot execute NWN's layout solver.

Use **Play Adventure.cmd** and choose **New Adventure** to load **rw_uifix.mod / The Silent Bell - Window Fix**. This was installed separately because NWN was running. Existing modules (including rw_playfix.mod and rw_errands.mod), saves and the running game are unchanged. Old saves retain their old embedded layouts.


## Playtest fixes (0.7.1)

The preserved 0.7.1 trial is **The Silent Bell - Playtest Fixes** (`rw_playfix.mod`). Run **Play Adventure.cmd**, choose **New Adventure**, and create/select a character. This is a separate module: existing modules, Aurora copies and saves are preserved. Older saved games retain their embedded scripts and layouts and cannot pick up these native fixes.

- Companion controls put **Talk freely with AI** immediately below the name. Nonverbal/disabled profiles explain the restriction. Close the panel and speak in Talk.
- Native errands recognize `Agathos, go to Bram and ask him how much a sword costs.` and `Agathos. Ask Bram how much a sword costs.` Also use `!companion familiar ask bram How much does a sword cost?` (or `summon1`/a recruit alias). A real task-start message confirms dispatch; an ordinary AI reply alone does not. Creator/player permissions, speech mode, same-area visibility and native control still apply.
- Visiting merchants report observed stock/prices; there is no purchase or item transfer through errands.
- The NUI window includes all fields from the installed `nw_inc_nui` constructor, including font and size/edge constraints. Missing row heights are handled explicitly. Inventory and merchant rendering still need an in-game acceptance test.
- The bridge replaces smart apostrophes, quotes and dashes before sending replies to NWN. Other language text is preserved; this is not a universal font/encoding conversion.
- Every room connection has named, usable **Passage to ...** markers and destination waypoints. Corridors remain walkable floor paths; clicking their marker offers an explicit transfer. Cross-area exits also have walk-in triggers. These are passage signs, not door-frame models.
- Automatic arrangement caps new room footprints at 3x3 ten-metre tiles. Author dimensions stay editable. AI furnishing proposals receive purpose/scale/grouping guidance. Stock furniture uses clearance footprints, chairs face tables, wall-side props face inward, and the central travel cross stays clear. Review flags large rooms and repeated/cluttered furnishing. The new trial reduces quiet chambers to 2x2 and removes unnecessary domestic/wilderness clutter.

AI Player **0.7.1+** is required by the updated launcher so a stale worker cannot silently omit the text/companion fixes. No live API call is part of the regression checks.


An AI-assisted authoring tool for complete, standalone Neverwinter Nights: Enhanced Edition adventures. Describe a story and its world, review the generated game content, edit it, and export a native Aurora module. No persistent-world server is involved.

## From a Git checkout

Run **Start Module Studio.cmd** from this folder. A fresh checkout initializes the shipped examples. On an existing installation, import **examples/ai_market.rwproject.json** for the AI-and-merchant trial, **examples/starlight_trial.rwproject.json** for the AI-generated example, or **examples/silent_bell.rwproject.json** to restore a separate sample copy. Build modules through **Build & share**; generated modules, runtime data and local settings are excluded from Git.

## New in 0.3: AI conversations, quests and merchants

- After choosing **Talk freely with AI**, close the menu and speak normally in Talk. You can also address **Bram Ironstock: Hello**, use **!talk bram show me your goods**, or end with **!end**. Follow-up focus lasts three minutes; private channels and OOC prefixes are excluded. Conversation remains within 12 metres and line of sight.
- AI can offer/start a quest, complete a current talk objective and select an explicitly chosen authored branch. Menu dialogue uses the same native quest state, journal, ending and reward logic. Visiting, fighting, retrieving items and using objects still require actual game actions.
- **Characters → Merchant shop** defines finite stock, exact prices, haggling chance, discount and offer duration. AI can generate these fields too. Purchases use the same native goods panel whether opened through chat or the NPC menu. The LLM cannot pay gold, deliver items or choose a discount.
- Shops require proximity within six metres, visibility and no combat. The player clicks **Buy** at the displayed price. The game checks price, stock and funds again, delivers one unit, charges gold, and prints a receipt. Stock and offers are saved in the game. Potion delivery preserves an existing stack by splitting the purchased unit before merging.
- Haggling rolls d100 against the configured chance. Offers include failed rolls, do not stack, and last the configured number of active game seconds. Gold prices round down, minimum one; cheap items may therefore receive a larger effective percentage reduction. New adventures enable live AI at export by default; it can be disabled.

The first shop catalogue contains daggers, short swords, longswords, quarterstaves, shortbows, leather armour, small shields and Cure Light Wounds potions. Each merchant supports up to eight unique stock lines, 1–20 units each, at most 80 goods total, and explicit prices of 1–100000 gold. Haggling supports 0–100% success chance, 0–10% discount and 60–3600 active game seconds. This release sells goods to players; buyback, barter and restocking are future work. It does not require NWNX. **Native shop interaction, item transfers and save/load behavior still need the user's in-game verification.**

## Start creating

1. Run **Start Module Studio.cmd**. The editor opens at **http://127.0.0.1:8766**. Python 3.10+ and an installed Windows copy of NWN:EE are required; no Python packages need installing. The bundled compiler is used automatically. Check game and user folders in Settings on another computer.
2. Open an example or choose **New adventure**. Write the storyline, tone, public summary, opening, ending, intended levels and party size.
3. In **Areas & rooms**, specify area type, width/height, room count, appearance and purpose. Generate the room layout, connect the rooms, and edit each exit's side and destination. Preview the exact corridor plan. One tile is 10 metres; north is up.
4. In **AI DM · Adventure design**, select **Complete adventure**, or a narrower scope, and give your instructions. The AI uses your story, room plans and character notes. Existing area type, size and requested room count are preserved. It proposes native quests, characters, dialogue, encounters, items and furnishings. Review the proposal before applying it; the last applied proposal can be undone.
5. Edit the generated content. **Characters** exposes personality, knowledge, secrets, motivation, game notes, ordinary dialogue, AI conversation profiles and merchant stock/prices. **Encounters & items** includes combat, ambushes, puzzles, treasure and story interactions. **Quests & endings** defines objectives, prerequisites, rewards and branching decisions.
6. Choose **Check adventure**, fix any errors, then build in **Build & share**. Download the .mod, editable project, or share/Aurora ZIP. **Install for playtest** copies the build into your NWN modules folder and backs up a differing existing file.

Generation uses the existing authorized OPENAI_API_KEY from the process, user or machine environment. It does not copy it into a project or package. API generation requires an internet connection and uses your API account. Manual editing, checking, building and ordinary gameplay do not require the key.

## What gets generated

- Native areas with matching tiles, sized rooms, physical corridors and explicit travel exits. Exits have a map marker, a walk-through trigger and a usable passage sign. Cross-area travel takes living party members in the departure area along.
- Placed NPCs with authored Aurora conversations; personality and scoped lore for optional freeform AI chat.
- Placed combat, room-entry ambushes, multiple-choice puzzles, treasure caches, quest items and usable story objects. Every encounter remains editable.
- Quest journal entries and compiled NWScript logic for talk, visit, retrieve, defeat, interact and choice objectives. Choices can lead to different objective paths and outcomes. Main quests conclude with authored ending narration; the module remains open for exploration.
- One-time quest/encounter rewards and save-local progress. Optional creature-count scaling uses nearby living faction members and their levels: base + floor((members - 1) / 2), plus one above the adventure's maximum intended average level, capped by the encounter maximum. It does not rebalance creature statistics or tactics.

Quest decisions and progress use native game rules. AI authoring happens before export. Players can complete the exported story with Studio closed and no API key.

## Examples

**The Silent Bell** is a furnished three-area, seven-room adventure with three key NPCs, a wolf encounter, an inscription puzzle, two quests and a final choice to restore or seal the bell. It demonstrates a connected adventure and branching quest logic.

**The Starlight Trial** was generated through a real AI request from a short observatory story and an author-specified two-room dungeon. It includes two NPCs, combat, a puzzle, furnishings and a six-objective quest with two endings. It demonstrates the storyline-to-module pipeline.

**The Silent Bell — AI & Merchant Trial** adds Bram Ironstock, a finite-stock merchant, to the abbey and enables live AI for the four key characters. Its filename is **rw_ai_market.mod**. This is the 0.3 compiled playtest build.

**The Silent Bell — Companion Trial** adds Seren Ashford, a recruitable abbey guardian, alongside the existing quest and merchant trial. Its filename is **rw_companions.mod**. This is the 0.4 compiled playtest build.

**The Silent Bell — Patrol & Social Trial** adds Mira Fen and Tomas Reed, with shared abbey patrol stops and mutually opted-in public conversation. Its filename is **rw_ambient.mod**. This is the 0.5 compiled playtest build.

**The Silent Bell — UI & Speech Fix** (`rw_ui_fix.mod`) contains the same adventure with the 0.5.1 speech/inventory/panel fixes. This is the current playtest build.

**The Silent Bell — Companion Errand Trial** (`rw_errands.mod`) enables the new 0.6 inspection and owner-directed visit permissions for testing. This is the preserved 0.6 trial; use rw_playfix for the current fixes.

All seven are included as editable example projects. Build the other examples from the editor when needed. They compile and pass structural checks; **Aurora and in-game playtesting are still required**. See PLAYTEST.md. The original Missing Courier module, the user's Aurora copy and the previous AI edition were preserved.

## Share and edit in Aurora

For ordinary play, share the .mod or its share ZIP. Players copy the .mod into their NWN user modules folder and start a new single-player game. The complete story and native gameplay are in that file; the application, project file, API key and server are unnecessary for ordinary play. NWN:EE itself is required.

Open the .mod in Aurora to inspect and edit areas, placed objects, conversations, journal and NWScript. The ZIP also contains source resources, a layout plan, validation report and .rwproject.json. Use Save As for an Aurora-edited edition. **Aurora changes are not imported back into Studio**; rebuilding from the project does not preserve separate Aurora edits.

To share the authoring tool, distribute Role-Weaver-Module-Studio-0.8.0.zip. The recipient sets their own game paths and API credentials if they want AI generation. No credentials or personal settings are included.

## One launcher for playing (0.7)

Double-click **Play Adventure.cmd**. Choose **1** for a new adventure or **2** to load a saved game. The launcher starts or reuses AI Player, checks its readiness and API-key availability, registers the exact module's AI context, then opens NWN. New adventures use the game's normal character-selection screen; saved games open at the main menu so you can choose Load Game. You do not start AI Player separately.

Keep the launcher window open while playing. It supervises the AI worker and can restart it if it exits. When NWN closes, it stops only the worker it started; an AI Player already running before launch is left alone. If NWN is already running, it does not open or close another game; it readies AI and asks you to switch back to the game. It refuses to install a different module version while NWN is running.

The workspace launcher defaults to **rw_natural**. Other installed adventures can be selected with `Play Adventure.cmd -Module module_filename`. `-Resume` opens the saved-game menu directly. `-Offline` plays natively without live AI and pauses any running local AI bridge. `-CheckOnly` verifies paths, the module's embedded build ID and matching project without starting the game/service or spending API credit. Game/user folders can be supplied using `-GameRoot` / `-UserDir`; otherwise configured Studio paths or Steam library discovery are used.

Every newly exported share/Aurora ZIP now includes a module-specific **Play Adventure.cmd**, its bootstrap and an **AI Player** runtime folder. Players must extract the whole ZIP and keep those files together. The launcher installs the .mod into the selected NWN user folder if needed, backing up a differing installed version. Player context registration does not overwrite an author's current project draft. The portable helper is for playing; use the full Studio package for authoring.

NWN:EE, Python 3.10+ and the player's own OPENAI_API_KEY are still required for live AI. Keys, personal settings, runtime logs and game histories are not included in exports. Readiness confirms the local bridge and key presence, not remaining API credit. No PW server or NWNX is involved.

This launcher works with the existing Companion Errand Trial and saves: **its native .mod was not changed for 0.7**. A saved game must still have the matching AI build context; the launcher cannot upgrade old saves or substitute another build's story. The current share ZIP and full Studio package include the matching context for the shipped trial.

## Optional AI conversations while playing

In **Build & share**, enable optional freeform NPC conversations before building. The normal story still works independently. Players who want live AI can use **Play Adventure.cmd** to start AI Player and NWN together, with matching project registration handled automatically. **Start AI Player.cmd** remains available for manual/advanced use. Players use their own OPENAI_API_KEY.

Successful NPC/companion replies use native Talk speech from that actor, with ordinary in-world speech and chat presentation. Connection errors, DM hints and control/transaction receipts remain system messages. Nearby characters may hear ordinary Talk as usual.

Speak to an AI-enabled NPC, choose **Talk freely with AI**, close the dialogue and speak normally in Talk (or use `!ai Your question`). Alternatively use `!talk alias Your question` nearby, or `!dm Give me a hint`. NPC aliases are shown in the character editor. Stand within 12 metres and in line of sight; merchant panels require six metres and no combat. Keep the game unpaused while waiting; replies are delivered on its heartbeat and requests expire after about 100 seconds. AI conversation can start an offered quest, complete its current talk objective, and select an explicitly chosen authored branch. The ordinary NPC menu uses exactly the same quest state and remains available. Item recovery, combat, visits and object interactions are confirmed by the game. Replies cannot invent new objectives or grant arbitrary rewards.

NPC prompts include their own knowledge, unlocked secrets and the relevant quest context. Secrets can unlock after a selected quest completes. The AI DM receives the full storyline to provide guidance. Recent dialogue and game/party context are sent to OpenAI for these optional live requests. The Responses API uses strict schemas and store: false. Studio limits attempted requests to 60 per hour per process. Settings retain the tested Role Weaver model, gpt-5.6-luna.

The local companion listens only on loopback, with host/origin checks and a request token. Its SQLite mailbox uses the NWN user database rwsp_bridge; old sessions and expired responses are rejected. This adapts Role Weaver's scoped character knowledge and game-authoritative rules without the PW add-on's Linux/NWNX/Redis services. It does not alter the game's party-control system.

## AI companions (0.4)

Use **Characters → Party companion** to make an authored NPC recruitable, choose an optional completed-quest requirement, allow movement/inventory and protect essential story characters. The stock guard class, equipment and combat scripts are retained for recruits; refine their statistics and equipment in Aurora. A merchant and a recruit must be separate characters.

Use **Companions** to set 1–7 recruit slots and author familiar/summon personality, knowledge, communication and permissions. AI generation has a **Companions and starting templates** scope that updates companions and supporting NPCs while preserving the rest of the adventure. The suite includes eleven familiar personalities plus two fallback profiles. Exact blueprint matches win over familiar type, then fallback. Existing projects migrate with companion support disabled; enable it explicitly before rebuilding.

During play, type **!companions** to open the native controls. Recruit/dismiss party members, follow, stand ground, guard the actual master, set AI/movement/inventory preferences, reply length and tone, and open inventory. **Talk freely with AI** arms the selected actor; close the panel and speak in Talk. You can also use `!companion seren <message>`, `!companion familiar <message>` or `!companion summon1 <message>`. The list handles ambiguous names. Native commands work with Studio closed; live conversations require the local AI Player and key. Controls require proximity, line of sight and no combat or direct control/possession of the actor.

Familiars and summons are the game's existing associates, created through normal class abilities and spells. This feature grants no spells, creates no replacement creatures, and leaves their normal dismissal controls in place. Animal profiles default to nonverbal reactions; intelligent profiles can speak. Creators can override or disable each profile. Native combat, heartbeat, spawn and possession scripts remain in place; original dialogue/death handlers are chained. A newer native order, death, ownership or settings change invalidates a pending companion reply.

Companion histories and preferences live in module SQLite, inside the save. Familiar memories use owner/caster/type identity across resummoning; each summon has a distinct instance identity. Party histories follow the authored recruit in that owner's save. Histories are bounded to 6,000 characters and 256 profiles, pruning inactive summons first. This is recent conversational memory, not a full relationship simulation.

The inventory panel shows player belongings and companion storage side by side, six entries per side/page. Scroll to reach the lower entries and independent Previous/Next controls. Equipped and protected belongings remain visible; they cannot be transferred until eligible. Familiar/summon satchels begin empty and are distinct from the summoned creature’s innate equipment.

Party inventory exchanges move the original unequipped eligible item or whole stack through native Give/Take actions after the owner clicks it. Plot, cursed, unidentified, container and equipped items, and items valued over 5,000 gold, are shown in the panel with a disabled transfer button and a reason. The explicit click replaces the owner's action queue; possession and combat block exchanges. Transfers are checked on the module heartbeat, never cloned or automatically retried. If unconfirmed, inspect both inventories before trying again.

Familiar/summon storage uses an ordinary **owner-held recoverable satchel**, not the disappearing creature's equipment slots. It remains accessible through normal inventory after dismissal or expiry; use **Recover familiar / summon satchels** in the controls. Empty satchels can be discarded from their panel. Familiar type 255 uses its blueprint in the memory key, so different custom blueprints do not share a familiar history. Bags preserve their actual items independently of history pruning.

This release implements the companion foundation. Item-fetch errands, autonomous collection, relationship scores, healing and AI spell/tactical control remain future work. Version 0.6 adds the bounded inspection and owner-directed visit tasks described below. Compiled native scripts and automated checks have passed; in-game behavior and Aurora opening of this new build still need the user's playtest.

## Patrols and NPC-to-NPC chat (0.5)

Open **Behaviors** for independent **module-wide patrol and social switches**, then select a character and enable either feature for that NPC. Existing projects migrate with both features off. The **Patrols and NPC social behavior** generation scope creates the same editable policies while preserving story, areas, quests and other project settings. Rebuild and start a new game to apply creator changes.

Patrols use an ordered list of 2–16 room stops, a loop or back-and-forth route, walk/run and 6–300 second waits. Rooms must connect through ungated ordinary corridors in the NPC's starting area. NPCs walk with native pathfinding; they do not use exit signs or teleport between areas. Routes only start a new movement near a player (45 metres), do not replace creature heartbeat/combat scripts, and pause for dialogue, shop use, combat, possession or recruitment. Failed paths wait 60 active seconds before retrying; a single movement attempt is bounded to 120 active seconds. Room stops are room centres; custom waypoint coordinates, cross-area routes and patrol visualization are future work.

For social chat, enable both characters, allow each other in their partner lists (empty means any opted-in character), and give each a public topic, cooldown and speech/nonverbal mode. Both characters' AI profiles and the module's live AI export must be enabled, and the local AI Player must be running. Only unowned, idle, mutually visible NPCs within six metres converse, with a player near enough to hear. Recruited companions, familiars/summons and encounter monsters are outside this initial ambient adapter.

Each exchange uses two short model requests: the first speaker receives only their own public profile and this pair's public history; the second receives their own profile and the first public line. Secret fields, gated topics, private player transcripts and the full plot are excluded. Keep sensitive story facts out of unconditional Knowledge and public topics. Social speech cannot trigger quest, inventory, payment or movement actions. The game rechecks both actual bodies, ownership, life/combat/control, visibility, proximity, interruption epochs and expiry before each line. Only emitted public lines enter their pair's bounded, save-local history.

Controls include a global 60–3600 second attempt interval, per-character 60–3600 second cooldowns and 1–12 exchange attempts per active game hour (default six). Failed/interrupted attempts consume the budget. The existing provider's 60-request hourly limit also applies. One exchange runs at a time; player requests are selected first, and queued player work cancels the second model request before it starts. An already-running provider request finishes before the bridge can service the next request. Native player activity can discard its eventual result. No conversation repeats once per creature heartbeat, and paused games do not play old replies after the 90-second wall-clock expiry.

The trial has both caretakers patrol between the guest hall and sanctuary, so their shared stops provide opportunities to meet. Mira waits 30 seconds; Tomas waits 45. Default social cooldown is 180 seconds and the global interval is 120. Keep NWN unpaused to observe movement and speech. NPC visits, travelling to seek a conversation partner, longer autonomous social scenes, town schedules and all-creature social adapters remain future work.

## Native panel fixes (0.5.1)

Merchant and companion windows use native scroll groups, explicit row widths/heights and resizable windows. Scroll to see overflow, including the shop footer, companion chat button and inventory controls. Item names use wrapping text in the inventory. This addresses clipping in the initial native panels; the new build still needs in-game rendering verification at your GUI scale.

## Companion inspection and visits (0.6)

Companions can carry out two owner-directed tasks. **Inspect a nearby container** walks to an accessible visible container, tries its normal native interaction, waits for the game to confirm it is open, observes direct contents and returns to report. It takes no items, opens no locked/trapped container, bypasses no quest gate and reads no contents through a closed lid. Reports list up to 16 direct items within a bounded text/scan budget, mark unidentified items without revealing their real names and disclose when more items were omitted. Bags inside a chest are not recursively searched. This inspection works with live AI disabled.

**Visit an AI NPC and report back** carries the owner's question to a visible opted-in NPC in the same area. On arrival, the companion speaks the question; the recipient receives its own profile, unlocked knowledge and that question, then speaks an answer. The companion stores that actual answer, walks back and reports within five metres of the owner. The answer cannot advance quests, claim rewards, buy goods, transfer items or order either actor. No private player transcripts or other NPC profiles are included. Nonverbal recipients respond nonverbally; a companion must have a speaking profile to conduct a verbal visit. Animals can inspect but give nonverbal reactions plus a factual owner-facing inspection receipt.

In **Characters → Party companion**, or on a familiar/summon template under **Companions**, enable **Allow inspecting accessible containers** and/or **Allow owner-directed NPC visits**. Recipients independently enable **Accept owner-directed companion visits** under **Behaviors** and must have AI enabled. Visits need live AI at export and AI Player running. These permissions default off when old projects are upgraded. Both tasks require creator movement permission and the owner's in-game movement permission; visits also respect AI preferences. Ordinary ambient social opt-in is independent from accepting an owner-directed visit.

Use the companion controls to choose **Inspect a nearby container** or **Visit an AI NPC and report back**. The target picker offers up to eight visible permitted targets; selecting an NPC asks the default question “How can you help us?”. For specific questions/targets, type in Talk:

```text
!companion seren inspect Healing supplies cache
!companion seren ask ilyra Where is Rowan?
!companion familiar ask bram What can you tell us about the abbey?
!companion summon1 status
!companion summon1 cancel
```

The same `inspect`/`check`/`ask`/`talk to` commands can be given during an already-focused companion conversation. Common `please`, `can you`, `could you` and `go` prefixes are recognized; this is a bounded native command parser, not unrestricted LLM task planning. Use an exact container name or the NPC's single-word alias. A generic `check the nearby chest` works only when there is exactly one permitted matching container; ambiguous matches are refused. Unrecognized dialogue remains ordinary conversation and cannot launch invented errands.

The companion must start near the owner, out of combat and direct control. Targets must be visible, accessible, within 45 metres and in the same area. One task per owner runs at a time; the active task is bounded to 240 active seconds, and a visit reply expires after 90 wall-clock seconds. Blocked movement, ownership/control/permission changes, combat, owner area changes, recipient interruptions, summon expiry or newer native orders stop the task. Cancel is available in the companion panel and through the command above. Normal native associate modes are restored only when ownership and the captured native command are unchanged; a newer order must never be overwritten.

Recent confirmed reports join that companion's save-local memory. A save made before an answer does not acquire later knowledge. On reload, old in-flight visit responses are rejected by the native session/identity checks. Fetching contents, cross-area errands, doors/locks/traps, unseen/remote recipients and companion-led quest changes remain outside this release. Actual pathfinding, native chest interaction, interruption and return/report timing still need the user's playtest.

## Current authoring boundaries

### Reviewed floor-plan generation (0.13.1)

**Generate from floor plan** first extracts an AI-generated object checklist and room scale from the selected image and notes. Users do not need to write a checklist. Review the inferred quantities, estimated/measured dimensions, asset choices and uncertain readings; edit only what needs correction. The matcher searches imported HAK placeable metadata and stock objects. Required substitutions and unavailable objects need explicit acceptance before generation. Unsupported details are reported rather than silently represented as generic furniture.

**Generate reviewed area** preserves the approved room dimensions and object quantities, populates characters/encounters, then uses the reference image again to propose explicit furnishing coordinates and rotations. Apply the resulting proposal to save its checklist with the area. **Review saved objects and scale** reopens it. Generation makes several authoring-model calls and requires available provider credit.

Scale is expressed in metres, with the intended dimensions shown beside the buildable dimensions. Rooms now support a minimum 10 × 10 m footprint, including 10 × 20 m narrow chambers, in 10 m increments. Rooms one tile wide connect to corridors through open passages; larger rooms retain stock framed doorways. Sub-10-metre spaces, raised platforms and custom structural geometry still need a different renderer. The AI is instructed to infer modest proportions instead of expanding ordinary rooms into huge halls.

In the visual editor, drag cyan furnishing markers or edit **Precise object placement** coordinates and facing. Coordinates are measured from each room's southwest corner. **Check placement edits** checks bounds, approximate footprints, overlaps, door clearance and the central arrival point. Update the generated area or open it in Aurora to export the edits. Explicit placements are preserved in the native module, not silently relocated. Small-room placement reserves the arrival point and access routes instead of a six-metre cross. Castle floors now use a stock floor tile with a clear centre. Custom footprints are conservative estimates; these checks do not establish complete walkmesh reachability or guarantee visual accuracy. Inspect the exported area in Aurora.

### Visual area workflow (0.12)

Studio now starts with one blank **Standalone area workspace**, without loading the previous example adventures. New projects can be either area workspaces or adventures. Area workspaces do not require a storyline, quests or ending, and hide adventure-only pages. The floor-plan section has a single **Generate from floor plan** button with an image selector. Optional interpretation-only review remains under Advanced layout review.

Use **Update generated area** to save the workspace and compile an isolated native preview, or **Open in Aurora** / **Test this area** to inspect it. When ready, choose a destination and click **Add area to adventure**. This copies the selected area's rooms and content, preserves the standalone workspace, and remaps colliding resource IDs and NPC aliases. Add connections to the adventure and story links afterward. Creating or editing an area never attaches it automatically.

Under **Advanced layout review**, **Interpret and review layout first** remains available for geometry-only work. It makes one image-backed AI request for rooms, connections and stated uncertainties. Correct inferred room names, purposes, dimensions and connection sides, then check and apply the proposed layout. Existing room IDs used by story content or external exits must be retained. The main floor-plan button uses the object-and-scale review described above.

The **Visual area editor** supports dragging rooms, resizing with yellow corner handles, and connecting two wall dots in door mode. Edits snap to native tiles and must pass corridor routing. An optional image overlay helps comparison; it is fitted to the map, not a calibrated tracing. Numeric room controls remain available. Physical door positions within each wall are chosen by the native exporter.

Select a room to lock its geometry, connections and contents against AI proposals, or request a preview that regenerates only that room's content. Locks are saved in the project; unlock before editing its geometry or replacing its layout. **Undo last design change** toggles the previous design snapshot during the current browser session. This is not persistent version history.

Five editable encounter starters are available beside the map: combat, ambush, puzzle, treasure and discovery. Templates require no API and do not interpret the brief; they retain it for editing or subsequent AI room regeneration. The enemy-count selector controls initial count, not a promised balance rating. Combat uses goblins initially and bounded party scaling. Edit enemies, clues, answers and rewards in **Encounters & items**.

**Test this area in NWN** builds a unique, separate module containing just the selected area and starts the local launcher at character selection. It supplies a simple walkthrough quest, disables live AI, removes external transitions and quest gates, and disables ambient behavior. Choose a suitable test character; automatic test-party generation is not included. Internal rooms still need valid connections. Your adventure and existing saves are not modified. The test launcher log is `data/area-test.log`; test builds remain under `data/builds`. Exit NWN before starting a test.

**Open in Aurora** builds the full adventure and opens a separate editable module under `data/aurora`. Choose the area in Aurora's Areas tree. Aurora edits are not imported into Studio. Item-level visual dragging, asset thumbnails, room libraries and persistent project history remain future enhancements.

### Floor plans, downloaded content and provider settings (0.11)

Local settings now separates **in-game conversations** from **area and module authoring**. The existing conversation model remains unchanged; OpenAI authoring defaults to `gpt-6-astra` with `medium` reasoning. Floor-plan interpretation, room regeneration and all authoring proposals use the authoring client. NPC conversations, companions, social exchanges and live DM actions use the conversation client. Both use the selected provider and its existing key. Gemini also has separate conversation and authoring model fields; the reasoning-effort control applies only to OpenAI.

Authoring reasoning requests reserve at least 32,000 output/reasoning tokens and allow up to five minutes per request. `default` omits an explicit reasoning setting for models that do not support it. Stronger models and higher effort can cost more and take longer. These settings improve the model's opportunity to interpret a diagram; native tile geometry and the available furnishing catalog still constrain what Studio can build. See [GPT-6 Astra capabilities](https://developers.openai.com/api/docs/models/gpt-6-astra) and [reasoning settings](https://developers.openai.com/api/docs/guides/reasoning).

Floor-plan references accept PNG, JPEG and WebP files up to 2 MB each, three per area, with optional interpretation notes. Images travel to the selected AI provider only when generating or interpreting, and remain embedded in the editable project. Native geometry is an approximation on a 10-metre tile grid.

Scan a HAK/ERF pack or folder of loose NWN resources in **Downloaded NWN content**. Choose placeables and supporting packs for the project. Selected dependencies are cached by content hash and included with exports. Custom tilesets are discovered for Aurora use; procedural custom-tileset generation is not implemented. Third-party pack combinations still need an Aurora and NWN check.

All scanned placeables are now searchable during area, room, encounter and adventure generation without manual pre-placement. When a library exists, the authoring model first proposes object searches from the brief and reference images. Studio searches the full metadata catalogue (not just the browser's first 200 entries), supplies up to 120 matching candidates, and lets generation choose which ones to place. Unused retrieved candidates are discarded; existing explicit project selections are retained. This adds an authoring request when custom content is available. No HAK binary is sent to the model. Only selected pack dependencies are loaded by the builder, and exports include their entire HAK files rather than extracting individual models. Separate supporting packs still need explicit selection. Raw models, textures, creatures, items and custom terrain do not automatically become placeable furnishings.

The former 512 MB HAK/loose-folder import cap and 40-pack scan cap have been removed. HAK imports index resources on disk, read only placeable metadata, and stream hashing and copying; loose resources are packed as streams. Dependency checks and share ZIP creation also stream data. Available disk space, memory for individual metadata resources, and NWN's archive/engine constraints still apply. This does not alter an already generated area: generate a new proposal, apply it and rebuild to use newly selected content.

**Local settings** supports OpenAI or Gemini, model names and per-provider saved keys. Windows saves keys encrypted for the current user using DPAPI. They are not returned to the browser, embedded in projects or included in share packages. Existing environment keys remain usable. The image transports follow [OpenAI's vision guide](https://developers.openai.com/api/docs/guides/images-vision) and [Gemini's image guide](https://ai.google.dev/gemini-api/docs/image-understanding); provider transport tests use mocks rather than billable calls.

This is an initial working toolset, not unlimited asset generation. It supports castle interiors, stone dungeons, caves/mines and forests; rectangular rooms/clearings; explicit routed corridors; 16 stock creature templates; three stock NPC appearances; nine furniture types; quest tokens and healing potions. Appearance descriptions guide the AI's selection and placement of those resources and are retained as author notes. They do not create new models, textures, custom terrain types or arbitrary mechanics. Extend such content in Aurora.

Projects support up to 16 areas, 16 rooms per area, 48 NPCs, 64 encounters, 64 items, 100 furnishings and 16 quests with up to 20 objectives each. Overcrowded rooms are rejected during export. The checker catches disconnected rooms, conflicting exits, invalid objective targets, nonterminating branches and common quest-gate deadlocks. Compilation and layout validation cannot prove game event timing, walkability or encounter balance; playtest before sharing a finished adventure.

## Development and provenance

Run `python -m unittest discover -s tests -v` from this directory. Native export tests run when the local NWN installation and compiler are available. See VALIDATION.md for completed checks and remaining tests.

The Windows compiler is [nwnsc v1.1.5](https://github.com/nwneetools/nwnsc/releases/tag/v1.1.5), with its license included. Native API and SQLite calls were checked against the installed nwscript.nss and SQLite_README.txt; tiles were checked against installed .set resources. The provider follows [OpenAI's structured-output documentation](https://developers.openai.com/api/docs/guides/structured-outputs). Role Weaver server code is credited in ROLE-WEAVER-LICENSE.txt (MIT, RoleWeaverInfo, 2026).

The older courier-specific companion is retained at /legacy; its documentation is archived locally as README-0.1.md, PLAYTEST-0.1.md and VALIDATION-0.1.md. Format-1 projects remain separate from the new format-2 module authoring workflow.
