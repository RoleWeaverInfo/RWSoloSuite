# Module Studio validation

## Bundled Windows installer — 0.20.0-rc2

- Built **dist/Role-Weaver-Module-Studio-0.20.0-rc2-Setup-x64.exe**, 14,543,717 bytes, SHA-256 **996845bab7f4cbb46295e135465da892725e903e40a67317c8eae44b183e03b3**. The 155-file payload includes Python 3.13.17 x64, its license, the native service launcher, Studio resources and the NWScript compiler. The runtime and Inno Setup 7.1.1 downloads are hash-pinned; the downloaded Inno installer signature was verified. The resulting Role Weaver installer is **unsigned**. No GitHub release was published.
- **310 tests passed under the bundled Python runtime** (90.186 seconds). After the final service-version reuse guard and guide corrections, **16 focused installer/release tests passed** and the final installer was rebuilt and smoke-tested again. The full-suite log is `data/installer-smoke-1794896305259877400/bundled-python-regressions.log`.
- The actual silent Setup installed into an isolated folder containing spaces. Its EXE started the service with external Python removed from PATH and deliberately invalid PYTHONHOME/PYTHONPATH. HTTP checks covered the saved workspace and branding routes. The installed compiler/resources built a native test module using the existing NWN installation. The exported adventure bootstrap found the installed application through its per-user registration and forwarded the module/player arguments without external Python; a diagnostic entry script verified forwarding without registering the test adventure in the user's primary service.
- Setup refused an upgrade while the service mutex was held. Reinstallation preserved the saved test project and DPAPI-encrypted dummy key. Uninstall removed the application and its registration while retaining the separate test workspace and key. Final lifecycle evidence: `data/installer-smoke-result.json`, test folder `data/installer-smoke-1794896576829191400`. The test installation was removed; the user's existing source service and projects were left intact.
- Default program files are installed per user under `%LOCALAPPDATA%\Programs\Role Weaver Module Studio`; persistent projects, settings and credentials live separately under `%LOCALAPPDATA%\RoleWeaver\ModuleStudio`. Source checkouts retain their existing `data` directory. Existing source data is not automatically migrated. Start-menu and optional desktop shortcuts start the service; they do not launch NWN.
- No live provider request, NWN launch or Aurora launch was performed. Installer behavior was checked on this Windows machine, not a separate clean Windows VM. The release candidate still requires publisher code signing for a signed public release.

## Blue theme and service-only release candidate — 0.20.0-rc1

- **304 tests passed** in the full regression suite (183.167 seconds). The 42 focused release/startup/export checks also passed. Game and browser launches in legacy launcher tests are simulated; their printed “Starting NWN” messages do not represent engine launches. No live AI request was made. JavaScript and PowerShell syntax checks pass.
- New **Start Role Weaver.cmd** starts/reuses the service, enables the bridge, and opens a local browser splash. The old root `Play Adventure.cmd`, `Start-Adventure.ps1` and `play.py` entry points are removed. Existing Studio shortcuts forward to the new service bootstrap. New adventure ZIPs install their MOD/HAKs and register the exact build profile without opening NWN or replacing an author's draft. The area test action now installs a separate test module for manual NWN startup. Old exports and saves are preserved.
- Tests cover missing-key startup, service reuse, older-version rejection, matching/mismatched/missing adventure profiles, author-draft preservation, running-game installation guards, server cleanup, local image MIME and route allowlisting, splash readiness/transition/stay/error behavior, and credential scanning across ZIP stream chunks. Existing module/export regression checks still pass.
- Inspected the running dashboard, splash and player-service page in the browser. The supplied PNG is displayed intact, the top-left brand uses the same artwork, and blue backgrounds/controls replace the green theme. The splash fits a 1280 × 720 viewport and its stay button cancels the transition. The editor showed no captured console errors. No NWN or Aurora application was launched. Mobile layout and other screen sizes have not been visually verified.
- Built **dist/Role-Weaver-Module-Studio-0.20.0-rc1-windows.zip**, 3,453,934 bytes / 117 files, with SHA-256 **5c46106a0648f351d6cc8bb088b11b1c3953e38587fe35e4ea4d7bd2d4a4c9db** and a separate checksum file. It contains the source runtime, branding, compiler/license and release instructions, with no personal data directory, examples, settings, API keys or downloaded HAKs. It requires Python 3.10+ and is not a bundled executable/installer. Nothing was published to GitHub.
- Extracted that actual ZIP into a temporary project folder, started its isolated service on port 8767 with a separate NWN user folder and no environment credentials, and checked five HTTP routes. It reported the correct version, an enabled bridge, no provider key and exactly one blank `area_workshop` project. The shipped PowerShell bootstrap also reused the primary service successfully without opening NWN. The isolated service and temporary folder were cleaned up; the primary service remains running. Results are in `data/release-smoke-result.json`; packaging metadata is in `data/release-package.json`.

## Preset button review-state fix — 0.19.0

- Reproduced `Cannot read properties of null (reading 'errors')` by running the preset control test with the real editor `change()` function. The earlier test used a no-op stand-in and missed that marking a draft dirty clears its review. Preset changes now mark the draft changed before requesting a fresh review. The same ordering defect was corrected in opening connections and carpet add/remove controls.
- **31 focused tests passed** across presets, doorways and carpets. The strengthened controls test covers recommended settings for all five area types, manual changes, reset, undo snapshots, the save handler, incomplete-draft warnings and rollback after a failed review. Doorway/carpet controls also run against the real draft-change code. JavaScript syntax checks pass, and live HTTP responses match both corrected script files. This is a browser-script fix: refresh Studio to load it; no server restart or module rebuild is needed for the button correction.

## Material and lighting presets — 0.19.0

- Full regression run: **294 tests passed** in 86.150 seconds, including 11 new preset tests. JavaScript syntax checks pass. Tests cover all five requested environment families, dungeon compatibility, invalid combinations and ranges, original-look compatibility, native GFF lighting/weather values, authoring controls and undo, and persistence through floorplan interpretation, AI proposal handling, area attachment and playtest creation. Provider calls are mocked; no live AI request was made.
- Native material exports retain full tile palettes and per-area resource identities. Checks cover unchanged model geometry and WOK numeric data, texture alpha/mipmaps, and two differently finished forest areas without resource collisions. Binary edits use known model fields rather than arbitrary byte replacements. The copied retail desert TILE36 definition now declares zero doors because its declared hook does not exist. Installed game resources remain untouched. Measured-room checks preserve carpet, platform and doorway geometry while changing floor/wall/door finishes. A real winter MOD/HAK export confirms snow chance, fog, skybox and light fields. Strict Aurora SET serialization remains enabled.
- Installed **rw_finish.mod**, build **31ae32102e641b42580b**, with **rwceae9f744b0678.hak**. The separate **Throne room - materials and lighting** project uses pale limestone, dark oak doors, warm lighting, brightness 1.0 and fog 4. It preserves the previous three-room layout, 24 furnishings, four fitted doors, two NPC profiles, carpet and dais. The exported textures and GFF fields were checked, and the share ZIP contains the generated HAK. `data/throne-finish-comparison.json` records the export assertions. The previous doorway project/module remains available for comparison.
- Studio restarted after confirming no running NWN or active bridge session. Live HTTP checks confirm **0.19.0**, 11 material choices, 10 lighting choices, the loaded preset controls and the saved comparison project. Both its review and an unsaved brightness/fog variation returned no errors. `data/presets-http-check.json` records these checks. No Aurora or NWN application was launched; final rendered appearance and runtime weather require the user's test. Start a new game in `rw_finish.mod`, since older saves retain their area resources.
- Scope: measured interiors receive coordinated original stone and wooden-door textures; native terrain receives selected ground/rock recoloring with source detail retained. Furnishings, trees, water and authored carpet colors retain their own materials. The interface shows color swatches, not a rendered scene preview. Lighting is fixed; optional outdoor rain/snow uses a 65% chance rather than continuous precipitation. Native material presets add a generated HAK, which must be shared with the module.

## Fitted doors and connected rooms — 0.18.0

- Full regression run: **282 tests passed**. A subsequent editor-flow check also passed after allowing connections to be added one at a time in an unfinished multi-room draft. Doorway tests cover exact aperture routing, shared 3D walkmesh edges from entrance hall through throne room to side chamber and onto the dais, no side leaks, narrow/double door collision in both open states, native animation/resource identities, SET door hooks and tile dummies, merged custom door-table rows, framed/open passages, invalid height/width/platform approaches, area attachment, editor controls and real MOD/HAK export. JavaScript syntax checks pass. The empty-connection preview regression discovered during the first full run was corrected before the passing run.
- The geometry test uses the accepted carpet project without a new model call. Added destinations are explicitly authored test rooms outside the original floorplan, not a claim that the image included those spaces. The 10 × 20 m throne room, its 2 × 14.1 m runner, 4 × 3 m / 0.45 m dais, all 24 furnishing position records and two NPC profiles remain. Entrance Hall is 10 × 8 m; Side Chamber is 6 × 8 m. The connection gaps are 2 m and 10 m, with clear widths of 2 m and 1.2 m respectively.
- Installed **rw_doors.mod**, build **a9b34ef950b444e1443d**, with **rw53dc2d42c2911c.hak**. Four native Door objects are at (25,18), (25,20), (30,35.6) and (40,35.6), with appearances 5200/5201 referencing fitted original double/single models. All are unlocked and have no transition target. No corridor trigger or passage sign is generated. Entry is (25,14) in the Entrance Hall. Geometry-source contains MDL, DWK, UTD, textures, merged 2DA, SET/palette and WOK resources; share ZIP includes the HAK. `data/throne-doors-comparison.json` records the export assertions.
- Door conventions were cross-checked against installed native MDL/DWK/SET/2DA resources and the [custom-door tutorial](https://neverwintervault.org/article/tutorial/tutorial-creating-custom-doors). Export includes per-tile `_D01` dummies matching ordered SET hooks, closed/open collision states and interaction points, a transparent transition-selection mesh, hinge animations and native blueprints. It uses the DWORD Appearance field rather than exceeding the generic-door byte field. The effective existing custom door table is extended, and the generated HAK precedes other packs. The strict Aurora SET ordering/CRLF validator remains enabled.
- Inspected `data/throne-doors-inspection.png`, rendered from exported tile/door models and furnishing transforms. The render shows the intact hall and runner, connected doorway apertures, and both added rooms. Walls are lowered and most materials are untextured; this is a static geometry inspection, not an engine screenshot or animation test.
- Studio restarted only after confirming no NWN process or active bridge session, and is serving **0.18.0**. Live HTTP checks confirmed the saved **Throne room - connected doorways** project, the destination/style controls, a review without errors, and acceptance of an unsaved temporary framed-opening/height change. No Aurora or NWN application was launched, and no live AI request was made. New-game testing must still confirm Aurora opening, door selection/open/close, movement in both directions and companion following. Do not use an older save for this test.
- Scope: same-area physical corridors in measured interiors. Native terrain and cross-area transition behavior retain their existing implementations. Door frames are generated tile geometry; door objects remain editable in Aurora. Short offset openings that would route through a room are rejected with an alignment/spacing instruction rather than silently cutting the wall. Complex curved/branching passages, richer door materials and keys/quest-gated measured corridors remain future work.

## Selected-item highlight (0.10.5)

The updated `rw_invclick.mod` highlights the selected item with a bright yellow 3-pixel border and translucent yellow fill. Highlight bindings update without rebuilding the window or changing item transfers. Existing saves retain their embedded scripts; see the change in a new game when convenient. AI Player does not need restarting.

User playtest confirmed the preceding build's companion inventory, chest collection into companion storage, and transfer from companion to player. This cosmetic change still needs visual confirmation in-game.

## Current trial: inventory selection and placeholder fix (0.10.4)

Validation: **165 tests passed**, including native compilation, canvas-click selection guards, creature-slot filtering and the transparent texture resource. Build `43d33c7e4b6c76b64e33` contains **45 compiled scripts / 176 resources**. Rendering and mouse interaction remain for the user's in-game verification.

Start a **new game** in **The Silent Bell - Inventory Click Fix** (`rw_invclick.mod`). AI Player 0.10.2 remains compatible; no backend restart is needed.

The item canvas click handler rebuilt the panel and cleared the selected item. It now ignores the trailing canvas click event after mouse selection, and changing quantity preserves selection. A transfer without a selected item gives an explicit instruction. Busy/unavailable transfers also explain why they cannot proceed.

Innate creature weapons/armor and creature-item abilities are excluded from the companion grid. Ordinary belongings remain visible. The large missing-image placeholder is replaced by an embedded transparent TGA; unknown item icons are omitted instead of drawing an error texture. An empty companion inventory now means there are no ordinary carried items or collected supplies.

Playtest: open the inventory and check there is no large red X, bite or eyeball-ability entry. Click an ordinary item and check its full name appears below the grid. Change quantity and verify the selection remains, then use Transfer selected. Also test dragging in both directions, collecting one potion, and closing/reopening. Protected/equipped belongings still cannot be transferred. Actual GUI interaction requires the user's in-game test.

## Previous trial: direct companion inventory panel (0.10.3)

Validation: **164 tests passed**, including installed icon-resource checks and native compilation. After the final text-list fallback routing adjustment, all **7 companion-upgrade checks** passed again. Build `08791f9aa7bc346f9ef5` contains **45 compiled scripts / 175 resources**. Launcher CheckOnly resolves `rw_inventory` and its matching project. The existing AI Player 0.10.2 is compatible and was left running with the game; the new build was registered successfully. No rendering, mouse interaction or actual item transfer is claimed verified in-game.

Start a **new game** in **The Silent Bell - Companion Inventory Trial** (`rw_inventory.mod`). AI Player 0.10.2 remains compatible: these fixes are in the module's native scripts. Existing modules and saves are preserved.

**!companions → select your companion → Companion inventory - visual panel**, or ask the companion to show its inventory. This opens a custom native NUI panel with both inventories; it does not open your normal inventory or place a bag on the ground. Companion contents combine persistent carried storage with the actual creature's belongings. Equipped/protected gear appears with a red frame and cannot be transferred. Click an icon for its full name, count and restriction. Icons represent the item's base type, not its exact composite armor/weapon appearance; custom types without an installed icon retain their names.

Drag an item icon from one side to the other, or select it and press **Transfer selected**. **Quantity: one / whole stack** controls the amount. The panel refreshes after the native transfer confirms, usually within two module heartbeats. The native merchant shop is unchanged. Old player-held satchels remain separately accessible.

Chest errands no longer use the creature-only droppable-on-death flag for chest contents. Plot, cursed, unidentified, equipped and over-limit goods are still guarded. Ask for **one healing potion**: one should enter companion storage and two remain in the trial chest. Ask for the remaining stack to collect both. Item properties and local variables survive the escrow copy; item object identity changes. Inspection alone takes nothing.

Playtest the panel opening without a dropped object; item selection; dragging in both directions; the transfer button; one/whole-stack mode; chest counts; save/reload; companion dismissal and recovery; and Bram's shop. Native compilation and regression checks do not verify rendering or mouse coordinates: those still require the user's in-game test. If drag does not register, report whether the transfer button works.

## Previous trial: companion packs and chest collection (0.10.2)

Validation: the full suite passed **162 tests**. After final recovery-menu and launcher edits, the affected suites passed another **28 checks**. The installed build `bb0a32903a9765136def` contains **44 compiled scripts / 170 resources**. Launcher CheckOnly found the installed module and matching project; AI Player 0.10.2 restarted with its existing key available and bridge enabled. No NWN or Aurora playtest was performed by the agent.

Start a **new game** in **The Silent Bell - Companion Pack Trial** (`rw_packfix.mod`) with AI Player 0.10.2. Older modules and saves are preserved.

The failed potion errand was rejected by an owner-distance check even though the companion had reached the chest. Collection now requires the companion at the accessible chest, not the player. Whole items/stacks go to a persistent companion pack, using a save-local escrow and confirmed destination counts. Item properties and local variables are copied; object identity changes. Ambiguous delivery stops rather than retrying a possible duplicate. Inspection alone never takes items.

**Companion pack - item grid** opens a normal placeable inventory through the player's native chest interaction. It is separate from equipped creature gear and legacy satchels. Use **!companions → Recover companion packs / old satchels** after dismissing a companion. Native merchant stores are unchanged.

Playtest: summon Agathos; open its pack; drag an ordinary item in and out. Stand away from the healing chest, ask Agathos to inspect it, then ask it to collect the entire healing-supplies stack. After the confirmed report, check the chest is empty and the pack contains exactly three supplies. Save/reload and dismiss/resummon to check recovery. Check Bram's shop still opens. GUI interaction, actual transfers and save/reload need the user's in-game verification; compilation alone does not prove them.

## Previous trial: familiar inventory and merchant conversation fix (0.10.1)

Use **Play Adventure.cmd → New Adventure** for **The Silent Bell - Familiar and Merchant Fix** (`rw_tradefix.mod`). Existing modules/saves are preserved. The backend merchant correction also applies to existing rw_trade saves; the native familiar menu changes require a new game in this trial.

The merchant error was a conversation-processing bug, not a missing build: merchant policy was removed from the NPC profile before native stock context read it. The profile is now sanitized after stock context is prepared. Bridge errors distinguish build-loading failures from failures processing a conversation; sanitized diagnostics contain request/build identifiers and exception type, never dialogue or credentials.

**Companion inventory - item grid** now targets the actual party member or familiar (including Agathos), rather than redirecting familiars to the player's inventory. **Recoverable satchel - in your inventory** is a separate, explicitly labelled option; open the named bag in your own inventory. Items placed directly on a familiar are not covered by satchel recovery. Summons use the paired storage list instead of unexpectedly opening only the player inventory. A native summon two-pane item grid is not implemented.

Validation: **162 tests passed**, including a regression through native merchant dialogue, error classification, familiar-versus-satchel dispatch and native compilation (**44 scripts**). The recorded failed rw_trade merchant payload was replayed locally with a stubbed provider: it reached the provider request step successfully; no API call was made and no game state changed. Native familiar inventory rendering and trading still need the user's in-game check.


Current build: `dcab39a773d509876f2e`. SHA256: `414d2315320fc59dbec25a73221041f94c98352dbcf49aeaa999db3062f758d8`.

## Previous trial: visual companion storage and merchant trading (0.10.0)

Use **Play Adventure.cmd → New Adventure** for **The Silent Bell - Visual Trading Trial** (`rw_trade.mod`). This module needs AI Player 0.10.0+ for live merchant conversation. Old modules and saved games are preserved; start a new game to receive the new store resources.

Companions retain **Inventory - item grid**, **Satchel - item grid**, and the text-list fallback. Speak to Bram and choose **Browse goods**, or ask him through AI chat, to open NWN's native store with item icons and normal buy/sell controls. Use its item drag-and-drop and trade confirmation controls. NWN handles the original stock, player belongings and gold. Test one purchase and one sale, reopen the store, and save/reload to check persistence.

Native store prices use NWN item values and Appraise. Haggling supplies a bounded discount to the native store opening; its displayed prices remain authoritative. A discount applies for that open window; reopening checks the offer timer. AI dialogue lists observed store goods, including player buybacks, but does not invent an exact final price. Stock is finite with no automatic replenishment. These stores have unlimited buying funds, pay at most 5,000 gold per item, and charge 100 gold for native identification; NWN enforces its normal eligibility rules.

In Module Studio, **Characters → Merchant shop → Shop interface** selects **Native visual store - buy and sell** or **Text list - fixed prices, buy only**. New merchant definitions default to native. Existing projects without this field remain list shops to preserve authored prices. The per-item price fields apply only to list shops; native pricing does not silently promise those fixed prices. Switch an existing merchant to native and rebuild to use visual trading.

Validation: **160 tests passed**, including native-store resources, finite quantities without NPC duplicates, guarded custom purchase paths, observed buybacks without fabricated prices, and offline native-store compilation. **43 native scripts compiled**. GUI interaction and actual transactions still need the user's in-game playtest; the agent has not launched NWN or Aurora.


Current build: `423fdeb423c5bb0a692b`. SHA256: `12418d637b7e5b0d132f56e2b36bbfdc535e82ca2b8e2e2934b85b36561834a9`.

## Previous trial: native visual companion inventory (0.9.2)

Use **Play Adventure.cmd → New Adventure** for **The Silent Bell - Visual Inventory Trial** (`rw_inventory.mod`). Old saves retain their previous inventory scripts. Existing modules remain intact.

Select a companion with `!companions`, then choose **Inventory - item grid** for a recruited party member or **Satchel - item grid** for a familiar/summon. Party members use NWN's native inventory. For a familiar/summon, your inventory opens: open its named satchel and drag item icons between the bag and your inventory. The satchel remains yours when the creature disappears. Use NWN's native item controls for examining and arranging items.

**Inventory - text list (fallback)** retains the working custom transfer panel. `!companion <alias> inventory` also opens the visual interface; append `inventory list` for the fallback. The AI inventory action uses the visual interface too. Opening through the suite still requires companion ownership and inventory permission; the native panel follows engine item rules. Pending custom handoffs must finish before opening it.

Merchant trading retains the existing purchase panel. This update covers companion storage. Physical room doors and previous AI companion features are included. Native GUI behavior and drag-and-drop still require the user's in-game playtest.


## Previous trial: physical room doorways (0.9.1)

Use **Play Adventure.cmd → New Adventure** for **The Silent Bell - Physical Doorway Trial** (`rw_doorways.mod`). Start a new game; older saves retain their old maps. All previous modules are preserved.

Interior corridor connections now have actual paired stock doorway tiles and native doors that open onto continuous walkable terrain. There are no corridor teleport signs or corridor transition zones. Outdoor connections remain trails; separate areas retain their area transitions. Studio's preview marks each physical doorway at its exported position. Door frames in compact rooms are placed to avoid overlapping, and furniture/actors keep clear of their entrances. Existing AI conversation, companion chest handoff and visual inventory features are included.

Validation: **154 tests passed**, **43 native scripts compiled**, and real installed walkmesh triangles checked through every interior doorway in this compact trial. The checks also verify solid wall geometry beside the openings. This is not an in-game playtest: please test walking through the doors with companions, including the vault's adjacent exits.


Current build: `b371b19c8b6afe407b65`. SHA256: `661ae56d2b996ecc37ed7f7089d65c12ebb5e65153712067356a607e4a109536`. Native resource counts: abbey 3 doors/1 area transition; road 0 doors/2 transitions; vault 5 doors/1 transition. Six doors connect interior rooms; two support area exits.

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


Current automated evidence: **152 tests passed**, including native script compilation and resource/link checks. **43 native scripts compiled** in build `f2568b029e8efe244337`. Four live AI checks passed: take, put, inspect-without-taking and old technical failure history. These do not prove in-game pathfinding or native GUI behavior.

Module SHA256: `d9b84edecce4e4a0f955b913909f4d1cf16ed8d961cc19c54d2954a11d58f634`.

## Previous trial: natural companion tasks (0.8)

Use **Play Adventure.cmd**, choose **New Adventure**, and select a character for **The Silent Bell - Natural Companion Trial** (`rw_natural.mod`). Older modules and saved games keep their embedded scripts; do not use an older save to test this update. AI Player 0.8.0+ is required. Existing modules, Aurora copies and saves are preserved.

Select a companion in `!companions`, choose **Talk freely with AI**, close the panel, then speak normally. Examples:
- "Go ask the merchant what swords he has for sale."
- "Could you look inside that chest and come back and tell me what you find?"

The AI selects one game-offered nearby object and an inspection or visit; the game rechecks exact object identity, ownership, creator/player permissions, speech mode, control, visibility and task availability. Ambiguous targets should prompt a question. A native **task started** receipt confirms dispatch. The companion must actually approach/open/ask and return before a report is confirmed. Contents are not read until the container is open. Locked, trapped or quest-gated containers remain unavailable. No purchase, theft, cross-area travel or quest advancement is added. Animals may inspect nonverbally but cannot conduct verbal visits. Precise commands and the task-selection menu still work without interpretation; natural interpretation requires live AI.

The old chest check incorrectly used GetObjectSeen, which the installed nwscript.nss documents as creature-only. Containers now use proximity and geometric line of sight plus the existing container/lock/trap/quest checks. Nearby observations include container names without exposing their contents.

Merchant controls use 550px content widths, companion controls 580px, and each inventory's contents 230px within separate scrolling panes. Width is applied to individual controls and group viewports only; enclosing row/column dimensions remain unconstrained. This replaces the 150px default widths seen in the screenshots while avoiding equal required parent/child dimensions. Rendering at the player's UI scale remains an in-game acceptance check.

Validation: 146 regression checks passed, including native compilation; five live AI checks passed for merchant phrasing, chest phrasing, negation, quoted speech and ambiguous containers. These language checks use a synthetic nearby scene and do not establish actual movement or GUI appearance. No NWN/Aurora launch performed by the agent.

Current native build: 35c43a718d19c46364b2; SHA-256 72c3015df03c1e48233a166ad5ada4ec0e94001115e93b269b42564b579bae07; 38 compiled scripts.

## Earlier release notes and reference


## Launcher working-directory fix (0.7.3)

The launcher previously started nwmain.exe with the installation root as its working directory. NWN requires the binary directory (`bin/win32`). The reported 3221225477 / 0xC0000005 crash had zero entries in all three installed base-resource keytables, missing PriorityGroups.2da and failed shader/UI resources during initialization, consistent with that path error. The launcher now starts from the binary directory for both New Adventure and Load Saved Game; CheckOnly displays that directory. Errors show the hexadecimal code and actual log location instead of assuming Steam/installation damage.

Source: [Beamdog developer guidance](https://forums.beamdog.com/discussion/67102/instanced-self-contained-installations/p1?new=1).

Run Play Adventure.cmd again. No module rebuild, game reinstall, key change or saved-game conversion is needed for this launcher-only correction. Current test module remains rw_uifix.mod. All 22 launcher tests passed, including new/saved working-directory checks and signed/unsigned access-violation errors. Game processes were simulated; actual launch remains the user's acceptance test. No NWN or Aurora launch was performed by the agent.


## Window sizing correction (0.7.2)

The reported error from rw_errands.mod was: "Error constructing window from json. The constraint cannot be satisfied". This is a layout-constraint failure, not evidence of missing JSON window fields. The previous 0.7.1 field additions alone did not address that sizing conflict.

Removed equal required widths/heights on both enclosing rows and their leaf controls. Rows/columns now size flexibly, controls retain readable heights, and each inventory column has an independent scrolling viewport. Removed the inventory row's fixed 740-pixel height and fixed column widths. Native UI rendering remains for user acceptance; regression checks cannot execute NWN's layout solver.

Use **Play Adventure.cmd** and choose **New Adventure** to load **rw_uifix.mod / The Silent Bell - Window Fix**. This was installed separately because NWN was running. Existing modules (including rw_playfix.mod and rw_errands.mod), saves and the running game are unchanged. Old saves retain their old embedded layouts.


- All 135 regression tests passed, including native compilation. The installed trial passed launcher readiness/context registration with AI Player 0.7.1; no API request or game launch. Eleven existing module files remained byte-identical.

- Targeted checks: bridge mailbox punctuation conversion without action/ID changes; social/visit display text; furniture footprint and actor clearance; chair/table grouping and orientation; non-mutating scale/repetition review; design-time guidance; merchant visit quotes from native observations rather than generated prices.
- Compiled module checks: every declared connection has usable native passage objects with valid arrival waypoints; corridor routes contain adjoining full-floor stock tiles; window JSON key contract matches the installed official nw_inc_nui constructor.
- Native compile and resource checks do not prove GUI rendering, navigation or actual actor behavior. These remain user playtests. The exact sizing error is now documented above; the 0.7.1 key-contract check alone was insufficient.
- New module rw_playfix.mod, build dd3e74dadedbcc925100, SHA-256 fda276592c2d71fc6d4c42e6c0d12ec5ff5aace7d41edb878993d31e65ffb664; 168 resources and 38 compiled scripts. Existing modules and saves preserved.
- No live OpenAI request, NWN launch or Aurora launch performed for this release.

## Historical validation

# Validation — Module Studio 0.7.0

Added a single Windows Play Adventure launcher that readies AI Player, registers the matching module build and opens NWN. A New Adventure / Load Saved Game choice is offered in the same launcher. Native gameplay scripts/module bytes are unchanged for the existing errand release.

- **126 automated checks pass**, including startup readiness, timeout cleanup, key-presence/configuration errors, native build/sidecar matching, character-selection arguments, saved-game arguments, reused/owned service lifecycle, recovery after a reused service stops, duplicate-game prevention, offline bridge pausing, module backups, bundled-module installation, draft-safe registration and portable package privacy. Earlier native gameplay tests remain included.
- The real Play Adventure.cmd → PowerShell → Python path passes -CheckOnly against the installed rw_errands.mod. A completely extracted share ZIP also passes its bootstrap's -CheckOnly with matching module/project and paths containing spaces. These checks start neither NWN nor AI Player and make no OpenAI request.
- A real readiness/context-registration check against Studio 0.7 passed with the installed errand build; the authoring draft remained byte-identical. This check did not start NWN or make an OpenAI request.
- The game arguments were verified against the installed official NWN:EE v74 release notes, Patch 1.66: +LoadNewModule opens the module at premade character selection; +TestNewModule silently chooses the first character and is not used.
- New exports contain a module-specific Play Adventure.cmd, Start-Adventure.ps1 and AI Player runtime. Cached export refreshes update launcher files atomically without rewriting the native module. Packaging uses explicit runtime/source allowlists; player settings, environment files, logs and local histories are excluded.
- Registering a player's build context does not save/overwrite the author's project draft. Existing imported contexts are compared after schema migration; mismatched build IDs/context are refused before game launch.
- The launcher supervises its worker until the game exits, restarts a stopped worker up to three times, and stops only its own worker. An existing AI Player is reused. An active NWN game is never closed or duplicated, and a differing installed module is not replaced while NWN is running.
- No NWN or Aurora instance launched by the agent. Startup/game lifecycle tests use fake game processes; actual Windows/Steam launch, character selection, saved-game selection and sustained in-game responses remain for the user's test. Bridge readiness means local service plus key availability, not API credit/authentication validation.

## Existing trial preserved

- Module: rw_errands.mod
- Build: f0ba3e8e679884d13d20
- SHA-256: 3b8d67ab6b7907d08831872bb3bb16759885acbfc3eec2f92f1bb3521e7e6eb1
- The share ZIP now includes the launcher/runtime; its .mod remains byte-identical. No new game is required solely for the launcher. An older save still needs its own matching build context.

---

## Previous 0.6 validation record

# Validation — Module Studio 0.6.0

Added owner-directed companion inspection and NPC visit/return/report tasks. Supports recruitable party members and the actual owned familiars/summons; nonverbal profiles inspect without invented speech, while verbal visits require a speaking source profile.

- **105 automated checks pass**, including installed-game native compilation for AI-on/off modules and all earlier quest, merchant, companion, patrol/social and UI/speech checks. Added coverage for default-off migration, source/recipient opt-in, matching familiar/summon profiles, distinct actor identities, gated recipient knowledge, bounded answers, no mechanical model actions, bridge visit dispatch, native chest-open/ownership checks, order/permission/epoch guards, disappearance cleanup and return proximity.
- Browser verified source inspection/visit flags and recipient visit opt-in, saving disabled states and restoring the example, plus adventure review. No browser errors/warnings observed. The trial settings were restored to its factory example.
- One real recipient-answer request passed through the previously authorized OpenAI key: 1 request, 285 input tokens and 151 output tokens. The answer used Ilyra's scoped knowledge and action none. Synthetic actor identities were used; this was not an in-game travel/transport test.
- Inspection calls native interaction, requires confirmed GetIsOpen and immediate item ownership before observing contents, and contains no item-taking or reward functions. Opening unavailable containers fails without reading contents. Reports are bounded and flag omitted items.
- Visit transport starts only after arrival and native question speech. Target identity, life/control, opt-in, range, epoch/session/expiry and actual answer delivery are checked before return. Reports require the owner within five metres and LOS. No quest/merchant actions are applied.
- Associate movement uses a bounded lease of native follow/stay/guard flags. Restoration checks both the captured native command and control epoch. Cleanup defers for direct control and does not clear combat actions. Disappeared companions release recipient locks; newer native orders invalidate restoration.
- Studio 0.6 and AI Player are configured locally. No NWN/Aurora instance launched by the agent. Actual pathfinding, NPC chest interaction, recipient speech, cancellation and return timing remain the user's engine playtest.

## Installed trial

- Title: The Silent Bell — Companion Errand Trial
- File: rw_errands.mod
- Build: f0ba3e8e679884d13d20
- SHA-256: 3b8d67ab6b7907d08831872bb3bb16759885acbfc3eec2f92f1bb3521e7e6eb1
- 154 resources, 38 compiled scripts; 3 areas, 7 rooms, 7 NPCs, 2 quests.
- Source task permissions and AI recipients are enabled for the trial. Earlier installed trial modules and saves were preserved. Start a new game to receive the new scripts.

## Limits and acceptance

One task per owner; visible same-area targets within 45 metres; 240 active seconds overall and 90 wall-clock seconds for visit replies. Inspect only accessible unlocked/untrapped containers, no taking or recursive bag search. Visits ask a specific question or the picker default and report the actual answer without quest/reward changes. Source and recipient permissions default off in upgraded projects. Cross-area travel, lock/trap work, theft/item fetching, invisible recipients and unrestricted LLM planning remain unimplemented. Native compilation cannot prove engine action timing; PLAYTEST.md contains the required checks.

---

## Previous 0.5.1 validation record

# Validation — Module Studio 0.5.1

Fixes prompted by user playtest: yellow system-only NPC replies, missing/one-sided companion inventory display, and clipped native panels.

- **92 automated checks pass**, including installed-game native compilation, AI-on/off export and prior quest/merchant/companion/patrol/social regressions.
- Successful NPC/companion replies call SpeakString on the captured actual actor; failures remain SendMessageToPC. Existing ownership, pending-version and story-action guards remain.
- Panels now use an auto-scrolling native group and explicit row widths/heights. Companion windows and merchant windows are resizable. Group/text/row constructors were checked against the installed game's nw_inc_nui.nss via GameAssets; no external UI library or game asset edits.
- Inventory shows both sides concurrently with separate six-entry pages. It enumerates direct inventory plus equipped items, marks restricted entries instead of hiding them, and retains original-object/native transfer checks. Familiar/summon storage remains a distinct owner-held satchel.
- No NWN or Aurora instance launched by the agent, and no additional OpenAI request was needed for these fixes. Actual speech and panel rendering remain for the user's playtest; no claim of engine UI verification.

## Separate installed test build

- Title: The Silent Bell — UI & Speech Fix
- File: rw_ui_fix.mod
- Build: bd87aac992f04bec7956
- SHA-256: 68b9fd1d6722e934ee892287fbfccd7176333dd21bd5828c5029b0b011a0bf77
- 145 resources, 34 compiled scripts; 3 areas, 7 rooms, 7 NPCs, 2 quests.
- Prior installed trials and existing saves preserved. Start a new game to receive these scripts.

---

## Previous 0.5 validation record

# Validation — Module Studio 0.5.0

Added native same-area room patrols and optional two-sided public AI conversations for authored NPCs, with module/per-NPC creator switches. No NWNX or game/client binary changes.

- **90 automated checks pass**, including native AI-on/AI-off module compilation and the existing courier, quest, merchant and companion regressions. New checks cover migration with defaults off, reachable routes, bounds, mutual partner opt-in, profile/privacy isolation, finite non-mechanical responses, player-priority mailbox ordering, yielding between speakers, behavior generation scope, exact pending actor references, interruption/expiry checks and retained native heartbeat/combat.
- JavaScript syntax passes. Browser checks verified global and individual patrol/social switches, saved off states, restored on states, route reordering/restoration, character selection and adventure review. No browser warnings/errors observed. The trial's edited settings were restored. Tomas was subsequently given the same route as Mira to provide a shared meeting stop.
- **One real two-sided exchange passed** through the previously authorized OpenAI key: 2 requests, 608 input tokens and 275 output tokens. Speaker contexts are isolated and responses contain action none. This used synthetic actor identities, not a live NWN transport test.
- Native social delivery requires both actual actors, matching UUID/epoch, ownership/control/life/combat checks, range/LOS/perception and no active player request/conversation. Only emitted public lines are saved. Patrols use native ActionMoveToLocation, with bounded attempts and retries; no teleport.
- Studio 0.5 is running locally with AI Player enabled. Existing projects/builds were preserved. Existing projects migrate with ambient behavior disabled.
- No NWN or Aurora instance launched. Native pathfinding, speech rendering, interruption, native control and save/reload acceptance remain for the user. See PLAYTEST.md.

## Final installed trial

- Title: The Silent Bell — Patrol & Social Trial
- File: rw_ambient.mod
- Build: 96822e969406c35c49a4
- SHA-256: 4c05359609982e43a19a89003225002c5aabaa72f032d5502a61a3d1a8bcc625
- Contents: 3 areas, 7 rooms, 7 NPCs, 2 quests, 145 resources, 34 compiled scripts.
- Mira and Tomas have shared guest-hall/sanctuary patrol stops; both permit public conversation with each other.

## Remaining scope

This release supports authored unowned NPCs, same-area room-centre routes and short nearby exchanges. It does not add cross-area patrols, custom coordinate waypoints, travelling social visits, all-creature social adapters, autonomous town schedules or mechanical actions through social speech. Both NPC profiles must opt in; live social AI needs the player companion and key, while native patrols work offline. User playtesting is required before treating these behaviors as engine-verified.

---

## Previous 0.4 validation record

# Validation — Module Studio 0.4.0

Companion foundation: recruitable party members, existing native familiars and spell summons. No NWNX or game/client binary changes.

- **75 automated tests pass**. Includes native AI-on and AI-off compilation against the installed NWN:EE header/assets, legacy courier/quest/merchant regressions, project migration, profile precedence and validation, actor/owner checks, creator restrictions, secret filtering, finite model actions, mailbox companion dispatch, retained recruit equipment/combat scripts, save-local SQL/history and original-object inventory code.
- JavaScript syntax checks pass. Browser checks verified companion navigation, personality save/restore, custom template addition/removal, Seren's recruitment settings and adventure review. The trial's original settings were restored; no browser warnings/errors were observed.
- **2 live OpenAI companion checks passed** through the previously authorized key: a nonverbal cat follow request and an explicit Seren follow request. 1683 input tokens, 206 output tokens. These use synthetic native snapshots and prove model/adapter behavior, not in-game transport or movement.
- Studio 0.4 and the enabled AI Player are running on 127.0.0.1:8766. Existing local projects/builds were preserved.
- No NWN or Aurora instance was launched. The new module has **not** been played or opened in Aurora. PLAYTEST.md provides the user's acceptance procedure.

## Installed trial

- Title: The Silent Bell — Companion Trial
- Module: rw_companions.mod
- Build: ecc4ccf64e652d742433
- SHA-256: b6e7f047db7d33eaf8b2e198a800ba302a19d95f1d6fd85628c81438f1392a09
- Contents: 3 areas, 7 rooms, 5 NPCs, 2 quests, 135 resources, 32 compiled scripts.
- Installed as a separate file in the local NWN modules folder; prior courier and merchant trials preserved.

## Engine checks still required

Native UI rendering, recruitment/dismissal, party switching and possession, original familiar penalties, native combat, follow/stay/guard behavior and exit travel, resummoning/expiry, stale reply rejection, original-object Give/Take and stack merging, recoverable bags and save/reload. Native compilation/resource assertions cannot prove event timing or action-queue behavior. Inventory confirmation is observational; it never creates replacement items or retries automatically. If a transfer is unconfirmed, inspect actual inventories first.

Satchels are owner-held native containers, not familiar equipment slots. Memories are recent bounded dialogue, not full relationship simulation. Advanced errands, social visits, AI healing/spell/tactics, animal-companion and dominated-creature adapters remain unimplemented.

---

## Previous 0.3 validation record

# Validation — Module Studio 0.3.0

Scope: AI conversation and quest progression, plus native AI/menu merchants. Other AI NPC port features remain on the roadmap.

## Completed

- **61 automated tests pass**, including compilation against the installed NWN:EE header/assets with nwnsc 1.1.5. Native tests cover both AI-enabled and menu-only merchant builds, plus the legacy courier exporter.
- Story tests cover current-NPC action allowlists, prerequisites, branch selection, invalid model actions and native checks against changed objective state. All paths call the shared native quest/reward functions.
- Merchant tests cover upgrading old format-2 projects without mutating them, stock/price/haggle limits, real-observation quote grounding, sold-out stock, restricted model actions, exported inventory resources, native menu wiring and stack-safe delivery preparation.
- Native export verifies every GFF round trip and the MOD resource index. The stock test verifies 11 actual goods on Bram and both merchant menu scripts. Native UI and transactions use no NWNX functions.
- Delivery prepares one unit in an empty temporary native store before copying it into the buyer's inventory. This handles the documented CopyItem behavior of returning an existing merged stack, without resizing or overwriting that existing stack's quantity. Stock is reserved before delivery; failed delivery does not take gold. Exact engine behavior still needs playtesting.
- Native shop events check window token/generation, module-load session, actor, proximity, line of sight, combat, quote price, expiry, stock and funds. Purchases require a native Buy click; the AI has no direct payment/item-transfer action.
- Haggle rolls and offer duration are native. Offer state and stock follow the savegame; the duration counts active module-heartbeat seconds rather than wall time while paused.
- Three **real OpenAI checks passed** using the previously authorized key: an observed dagger price, a requested shop opening, and an explicit sealing branch choice. Total: 3 requests, 2254 input tokens and 287 output tokens. These were model/adapter checks, not an in-game transport test.
- Browser checks verified Bram's merchant card, quantities/prices, stock-line addition/removal, haggling toggle, saving, adventure review and native export. The original sample values were restored after editing. No browser errors or warnings were observed in the final check.
- JavaScript syntax checks pass. Local Studio 0.3 and its player companion are running on 127.0.0.1:8766. Existing local projects/builds were preserved in the Git checkout's ignored data folder.
- No NWN or Aurora instance was launched.

## Installed trial build

- Title: The Silent Bell — AI & Merchant Trial
- Filename: rw_ai_market.mod
- Build: 89751fbc24d1c1ca7a03
- Contents: 3 areas, 7 rooms, 4 NPCs, 2 quests, 112 native resources, 23 compiled scripts
- SHA-256: 71f904c83be6f100fb874256188ebc0722fd07f6fa31cdc9704c185c4eed460c
- Installed in the local NWN user modules folder. The original Missing Courier files remain separate.

## Required user verification

The trial has **not** been played or opened in Aurora. Native compilation and resource checks cannot prove game event timing or UI rendering.

Priority checks: native goods-panel rendering; exact gold/item transfer; potion merges; insufficient funds; sold-out stock; double clicks; offer expiry; AI/menu quest switching; pending-reply rejection; and save/reload before/after purchases and decisions. Also check walkability, exits, party travel, death/respawn and both endings. PLAYTEST.md contains the concrete procedure.

This first merchant release sells eight catalogue goods to players. Buyback, general barter, restocking, familiar/summon adapters, patrols and NPC-to-NPC conversations are not implemented in this release.


Current corrected native build: cb9f5d07b37c8e7f880e; SHA-256 623348ded87a82f81f448b7a625c7832e9a778a1864ca280d949f25551e5cfd7.

Installed window-fix trial: 8002076772c5d7e2bea3; SHA-256 18772a8b7a3ab361a5654e9828129094769a81ac677e70730f5bde3db3cb634d. All 135 tests passed; 12 existing modules remained unchanged.
# Studio 0.12 design workflow — 2026-11-15

- Standalone-workspace follow-up: 193 tests passed, including clean startup without examples, generation without story requirements, and collision-safe copying into an adventure without mutating the workspace. Render checks confirm exactly one floor-plan generation button with zero, one or three images. Requested local reset archived old projects/builds under `data/reset-backups/20261115-224321`; the live Studio now reports one blank area workspace, zero builds and the existing API configuration available.

- Full Python regression suite: 187 tests passed. JavaScript syntax checks passed for both editor scripts.
- Floor-plan interpretation transport verified with a mocked vision provider; author corrections preserve image references and reject removal of story-referenced room IDs. Real image interpretation quality still needs user testing.
- Map moves/resizes reject out-of-bounds or locked edits. Wall connections run native corridor routing and reject duplicate wall ports.
- Room locks restore geometry, content and touching connections after AI changes. Selected-room regeneration keeps other rooms, layouts and quest definitions intact.
- Five native encounter templates validate without a provider call. They are editable starters, not balance guarantees.
- An isolated single-area test compiled into a native module without requiring a finished adventure. Mocked launcher tests verify character-selection launch wiring and refusal to disrupt an already-running game. NWN was not launched by these checks.
- Render checks cover panel controls, lock state, four wall ports, resize handles and image-overlay opacity. Interactive dragging, Aurora opening and in-game area testing remain user acceptance checks.

## Floor-plan output correction — 0.13.2

- Corrected the castle floor selection: tile 175 is the named Bath feature, despite passing walkability checks. Tile 109 uses floor textures without the bath's water texture; its minimap was inspected. New regression checks reject Bath/water features as generic flooring. Earlier claims that 175 was plain flooring were incorrect.
- 226 Python tests pass, including all supported stock walkmesh checks and native compilation. New checks cover replacing obsolete furnished workspace rooms and rejecting legacy floor-plan requests that bypass checklist review.
- UI checks verify that pending proposals block build/Aurora actions until applied or explicitly discarded, and area generation with references routes through the checklist. Measured image labels now take precedence over stale generated descriptions and contradictory older prose.
- The inspected user reference specifies a single 10 × 20 m interior and no separate vestibule. The saved output contained two much larger rooms and no checklist/explicit positions. The exact user interaction that lost the reviewed result was not reproduced; the pending-proposal and bypass guards address identified routes to that outcome. No live AI regeneration or in-game visual fidelity claim is made by these tests.

## Small rooms — 0.13.1 (historical; floor tile corrected in 0.13.2)

- 223 Python tests pass. Seven added checks cover 10 m minimum dimensions, sub-tile scale warnings, resizing, opposing passages, compact NPC/furniture allocation, safe transition arrival coordinates, native compilation and actual stock walkmesh openings across castle, dungeon, cave and forest tilesets.
- One-tile-wide rooms use open corridor passages. Larger rooms retain framed doorways. Castle full-floor tiles use tile 175, whose walkmesh has a clear centre; the previous tile 36 failed the small-room centre check.
- JavaScript syntax and render checks pass; a 6 × 10 m reference shows a 10 × 10 m buildable footprint. No live AI calls, NWN launch or Aurora launch were used. User playtesting remains necessary, especially visual proportions and navigation with a full party.
- Geometry still uses 10 m tiles and existing corridor spacing. This release does not generate sub-tile walls or promise arbitrary centimetre-accurate floor-plan tracing.

## Floor-plan checklist and scale — 0.13.0 (historical)

- 216 automated Python tests pass. Eight new checks cover image-backed checklist extraction, metre-to-tile scale rounding, explicit acceptance of substitutions, exact object counts, source-image use for placement, preservation through area copying/testing, placement errors, and compiled native GIT coordinates/rotation.
- JavaScript syntax and Node render checks pass for the checklist modal, the single floor-plan generation control, cyan object markers and numeric placement fields.
- Native compilation and resource inspection were performed without opening NWN or Aurora. AI requests were mocked; no live provider request or credit was used for this verification. Real image interpretation and visual quality still require user testing.
- Limits remain: 20 × 20 m minimum native rooms, 10 m increments, approximate custom footprints, no new alcove/dais renderer and no full walkmesh reachability validation. Explicit coordinates improve furnishing control; they do not remove these geometry limits.


## Visual catalog and native groups — 0.14.0

- Full regression run: 239 tests passed. New checks cover binary/ASCII model parsing, actual installed dimensions, full-catalog retrieval, PNG visual evidence, oriented footprints, stock appearance export without HAK dependencies, dimensions surviving adventure attachment, fixed group rotations, native door walkmesh seams, forged/mismatched group rejection, obstacle-aware arrivals in cave/forest/desert/winter and native group module compilation. JavaScript syntax checks pass.
- Installed-resource audit on this machine: 1,289 stock placeables indexed, 1,235 with static mesh previews and 54 explicitly unavailable (including invisible/effect-only models). With the imported pack, 2,315 catalog entries are browsable. There are 156 compatible native groups across six stock tilesets; unsupported groups remain visible and disabled.
- Real provider test reused the existing authorized key. The measured image produced one 10 × 20 m nominal room. The initial asset shortlist was poor; retrieval was corrected and the repeated matcher chose actual throne 183, bench 178, brazier 57 and weapon rack 105. Subsequent generation placed 19 props and two NPCs; the diagnostic `rw_catalog_test.mod` compiled 29 scripts and passed native resource round-trip checks. No NWN/Aurora playtest was performed.
- Local evidence: `data/throne-catalog-analysis-v2.json`, `data/throne-catalog-generated.json`, `data/throne-catalog-comparison.json`, and `data/throne-catalog-build.json`. Original `area_workshop` was not changed. The separate saved project is `throne_catalog_test`.
- Comparison is deliberately limited: 18 scheduled prop origins are within about 0.222 m of image-read targets, but that is not a fidelity score. Generic wall-tile geometry expands the walkable bounding extent to about 27.01 × 37.01 m. The throne sits at the intended nominal coordinates but has no raised dais. The first generated bench rotations and floor-level writing supplies also reveal unfinished orientation/height work. Exact walls, external-door destinations, dais, steps, carpet, columns and statues are not reproduced. Later prompting now distinguishes raw model rotation from semantic facing; this needs another visual acceptance pass.
- Shape previews are untextured static geometry, not game screenshots. User visual inspection in Aurora remains required. HAK supporting packs and textures still need valid dependencies and compatible 2DAs; custom terrain/elevation generation is not part of this increment.

Live HTTP checks confirmed Studio 0.14.0, the complete catalog response, throne dimensions, stock-model SVGs at multiple angles, all six group catalogs and one rendered group per environment. Browser automation failed to connect and its Windows fallback could not acquire a current browser window, so on-screen Studio interaction remains unverified. No user application data or settings were changed through UI automation.


## Measured walls, scale, rotation and elevation — 0.15.0

- Full regression suite: **248 tests passed**. Nine new spatial tests cover exact 10 × 20 m and sub-tile floor extents, welded walkmesh vertices, offset/variable-width doorway traversal, closed unused boundaries, unconnected doorway recesses, native outdoor preservation, support chains and cycles, vertical overlap/ceiling rejection, rotation against actual room bounds, editor support controls, and native resource export.
- Generated test HAKs contain matching SET, MDL, WOK, ITP and minimap resources. All exported tile IDs resolve to the generated models; every WOK AABB leaf references an actual face exactly once. The module's HAK dependency and editable geometry sources are present in the share ZIP. These are resource/compiler checks, not a substitute for an engine playtest.
- An additional compiled fixture confirms a real native paper model exports at Z≈0.89 m, placing its model bottom at the desk's measured 0.90 m surface. Ordinary floor-level overlap is still rejected.
- Controlled throne comparison: reused the prior reviewed catalog and nineteen selected objects, with a 10 × 20 m room and two doorway positions taken from the image's written dimensions. One fresh GPT-6 Astra placement request (8,502 input / 1,515 output tokens) passed without repair or manual coordinate corrections. All four bench rotations are now 0° (long axes east–west), papers rest on the desk, and banners have a 1.5 m model-origin elevation offset. The room's walkable bounding extent is 10.6 × 20.6 m including the two short doorway recesses; clear interior remains 10 × 20 m. This is not a new end-to-end image interpretation test.
- Saved separately as `data/projects/throne_spatial_test.json`. Build `b1bd4f1db1a1329de950` produced and installed `rw_spatial.mod` with `rw40721bb70becbd.hak`. The original area workspace was not overwritten. Diagnostics: `data/throne-spatial-comparison.json`, placement response, review, and an untextured inspection render. The render uses the actual exported object transforms and lowers walls for visibility; it is not a screenshot from NWN.
- Studio restarted idle as 0.15.0. Live HTTP checks confirmed the new script is linked and served, the test project is available, and its review is ready with no errors. JavaScript syntax, focused render/interaction assertions and `git diff --check` pass. No browser-window automation, Aurora launch, or NWN launch was performed. The user's playtest must confirm appearance, wall cutaway and movement in the actual engine.
- Limits remain explicit: measured walls are rectangular stone; room origins/corridor routing retain the tile grid; unconnected openings have no destination; raised structural floors/dais/stairs and missing decorations are not fabricated. Outdoor terrain and natural caves retain native geometry. Model bounds are visual bounds and do not prove an irregular tabletop's usable surface.
- Bearing interpretation was checked against the primary [xoreos situated-object loader](https://raw.githubusercontent.com/xoreos/xoreos/master/src/engines/nwn/situated.cpp); walkmesh material IDs and SET/palette definitions were checked against the locally installed NWN resources. No third-party implementation code was copied.


## Aurora crash correction — 0.15.1

The user reported repeatable Aurora crashes opening the generated area, including after regenerating it. Inspection of both newly opened builds (`5de74fd65627d427c0d6` and `f091c4006269229ab5cd`) and the original `rw_spatial` build confirmed the same exporter defect: appended `TILE179`–`TILE214` sections appeared after `[GROUPS]` and the existing group definitions. Files also used LF-only line endings. A normal INI reader ignores section order, which explains why the original archive/resource tests passed despite this incompatibility.

The documented Aurora format requires all tile definitions and their door/sound subsections before `[GROUPS]`, Windows CRLF lines, and a final newline. References: [SET ordering](https://nwn.wiki/spaces/NWN1/pages/38175567/SET), [tileset line endings](https://nwn.wiki/spaces/NWN1/pages/38175063/Tilesets). This is a concrete compatibility defect consistent with the reported crash; an actual successful Aurora opening remains to be confirmed by the user.

The serializer now explicitly orders sections and validates section counts, door/sound adjacency, line endings and the trailing newline before writing the HAK. It preserves the stock cave tileset's omitted optional SECONDARY RULES section. Five new regression tests reproduce the previously accepted bad order, reject bad counts and line endings, and check real castle/dungeon/cave exports. The native build integration test now applies the strict validator to the packaged SET too. **253 tests pass**.

The latest user-generated room (25 placeables and 2 NPCs) was recovered from the most recently opened build, without new AI calls or replacing existing projects. Saved separately as `throne_aurora_fix`, titled **Aurora repair - latest throne room**. Repaired offline build `6d4ed60bc02dc48a0c10` installed `rw_aurorafix.mod` and `rw2133645c447438.hak`. Its 215 tile definitions finish immediately before the group section; all 35 groups follow, and CRLF validation passes. Diagnostics are in `data/aurora-format-fix-build.json`. Existing build/project bytes were left intact.

Studio restarted idle as 0.15.1; live HTTP checks confirmed the repaired project and a ready review with no errors. No Aurora/NWN application launch or new model call was performed. Old exported copies retain their original content; rebuilding through updated Studio produces a new MOD/HAK pair.

The user subsequently confirmed that the repaired file opens in Aurora and that the generated room matches the reference substantially more closely. That confirmation applies to the 0.15.1 baseline, not the new raised geometry below.

## Raised platforms and stairs — 0.16.0

- The full suite passed **261 tests** after the geometry, height propagation, floorplan pipeline and editor changes. Two additional focused checks then passed for a flat rug meeting the bottom tread and correctly rotated tile path nodes: **263 distinct checks in total**. Ten platform tests cover three visible risers, continuous ramp heights, shared-edge traversal from floor to dais, removal of the old floor underneath, nondegenerate triangles, all four approach sides, raised tile seams, footprint/landing/headroom rejection, support-chain heights, safe entry relocation, image-analysis integration, editable controls, attachment to an adventure and native module export.
- A live GPT-6 Astra medium request using the configured existing key extracted the actual floorplan as a 10 × 20 m room, a dais at (3,17) measuring 4 × 3 m and 0.45 m high, and three south-facing steps with 4 m width and 0.90 m total run. The final generic prompt contains no throne-room example coordinates. The request used 4,473 input / 3,751 output tokens; an earlier prompt check also ran. This checked image interpretation only; existing approved furnishings were reused, not regenerated or rematched. Results: `data/throne-platform-inference.json` and its usage record.
- The new separate `throne_platform_test` workspace is titled **Throne room - dais and stairs**. All 25 original furnishing position records and the two NPCs were retained from the user-confirmed `throne_aurora_fix` project. Only the platform geometry and its checklist decisions were added; the previous workspaces remain unchanged. The exported throne origin is Z≈0.45 m with its original X/Y/rotation intact.
- Built and installed `rw_dais.mod`, build **620a9ac00ffe615065f3**, with generated HAK **rw08fbaea41da3cb.hak**. The test export has 618 WOK faces, valid AABB leaf coverage, correctly ordered CRLF SET sections, matching model/walkmesh resources, and the HAK plus editable geometry sources in its share ZIP. `data/throne-platform-comparison.json` records the measurements. Inspection renders use the actual exported models and instance transforms with untextured shading and lowered walls; they are not game screenshots.
- Native instances and entry/encounter/patrol destinations follow the same platform height function as the WOK. Thin floor rugs may touch the stair bottom; furniture may not block the treads or landing. The generated stairs render discrete treads while the walking surface is a continuous slope, consistent with the sloped faces inspected in the installed castle stair models. Coarse tile connectivity now uses shared walkable edges and the documented [path-node shapes](https://nwn.wiki/spaces/NWN1/pages/139689996/Tile+Path+Nodes), with orientation defined by the [SET format](https://nwn.wiki/spaces/NWN1/pages/38175567/SET).
- Studio restarted idle as **0.16.0**. HTTP checks confirmed the new project, served platform/checklist controls, a ready review and successful review of a temporary height edit; that edit was not saved. JavaScript syntax and focused editor assertions pass. No Aurora or NWN application was launched. User testing still needs to confirm Aurora opening, appearance and movement up/down the steps in a **new game**; older saves retain the old area.
- Scope: rectangular measured interiors, one straight cardinal flight per platform, no curved stairs, stacked storeys or newly generated outdoor elevation. Forest/desert/winter/native cave terrain remains unchanged. The short existing carpet is still a selected asset substitute, and external openings still lack destination areas; this increment specifically adds the measured dais and stairs.

## Measured textile carpets — 0.17.0

- Full regression suite: **271 tests passed**. Eight new carpet checks cover exact 2 × 14.1 m dimensions, tile clipping and continuous UVs, border area/physical sizing, opaque red woven TGA content, platform support, rejection of stair/edge crossings and overlaps, floorplan checklist integration without a furniture substitute, area attachment, editor controls, unchanged WOK bytes, valid SET formatting, and native MOD/HAK/share-source packaging.
- One live request through the configured GPT-6 Astra medium authoring model independently read the runner as x=4, y=2, width=2, depth=14.1, color=red, border=none. It also retained the expected 4 × 3 m / 0.45 m dais and three-step dimensions. The generic prompt contains no throne-room coordinates. Usage: 4,803 input / 3,630 output tokens. Saved in `data/throne-carpet-inference.json` and its usage file. Existing furnishings were reused; this was an image-inference check, not a complete regeneration of the room.
- Saved separately as **Throne room - red carpet**, project `throne_carpet_test`. The old short rug placeable was removed; all remaining 24 furnishing position records and the platform geometry match the accepted dais test. Two NPCs remain. The original workspace and `rw_dais.mod` are preserved.
- Built and installed **rw_carpet.mod**, build **33d94fdffb738273d03f**, with generated HAK **rw735b8916921cde.hak**. Actual exported carpet vertices span area coordinates (24,22)–(26,36.1), lie 0.012 m above the floor and split over two native tiles. The throne remains at Z≈0.45 m. The exported texture is the generated red textile. The HAK and editable geometry/texture sources are in the share ZIP; strict Aurora SET ordering and CRLF validation pass. Measurements are recorded in `data/throne-carpet-comparison.json`.
- Inspected `data/throne-carpet-inspection.png`, rendered from the actual exported meshes/transforms with the carpet’s exported average texture color. Other assets remain untextured, walls are lowered for visibility, and game lighting is not reproduced. It shows the long continuous runner meeting the bottom stair, with the drawn 2 m entrance space retained. This is not an NWN screenshot.
- Studio restarted idle as **0.17.0** while leaving the user’s existing Aurora window untouched. HTTP checks confirmed the project, served editor/checklist controls, a ready review without errors and acceptance of a temporary width/color/border edit; the edit was not saved. JavaScript syntax and focused UI checks pass. No Aurora/NWN launch or automated gameplay occurred. User confirmation is still needed for the new export’s appearance and runtime behavior.
- Limits: rectangular, axis-aligned carpets in measured interiors; flat floor/platform support only. Carpets do not add collision, change footstep sounds or drape over stairs. They are part of generated tile geometry; resize/recolor through Studio and rebuild. Outdoor terrain generation, richer material sets, connected destination areas and the proposed next stages remain separate work.
