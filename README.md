# RWSoloSuite — Role Weaver Module Studio 0.7.3

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

To share the authoring tool, distribute Role-Weaver-Module-Studio-0.7.3.zip. The recipient sets their own game paths and API credentials if they want AI generation. No credentials or personal settings are included.

## One launcher for playing (0.7)

Double-click **Play Adventure.cmd**. Choose **1** for a new adventure or **2** to load a saved game. The launcher starts or reuses AI Player, checks its readiness and API-key availability, registers the exact module's AI context, then opens NWN. New adventures use the game's normal character-selection screen; saved games open at the main menu so you can choose Load Game. You do not start AI Player separately.

Keep the launcher window open while playing. It supervises the AI worker and can restart it if it exits. When NWN closes, it stops only the worker it started; an AI Player already running before launch is left alone. If NWN is already running, it does not open or close another game; it readies AI and asks you to switch back to the game. It refuses to install a different module version while NWN is running.

The workspace launcher defaults to **rw_uifix**. Other installed adventures can be selected with `Play Adventure.cmd -Module module_filename`. `-Resume` opens the saved-game menu directly. `-Offline` plays natively without live AI and pauses any running local AI bridge. `-CheckOnly` verifies paths, the module's embedded build ID and matching project without starting the game/service or spending API credit. Game/user folders can be supplied using `-GameRoot` / `-UserDir`; otherwise configured Studio paths or Steam library discovery are used.

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

This is an initial working toolset, not unlimited asset generation. It supports castle interiors, stone dungeons, caves/mines and forests; rectangular rooms/clearings; explicit routed corridors; 16 stock creature templates; three stock NPC appearances; nine furniture types; quest tokens and healing potions. Appearance descriptions guide the AI's selection and placement of those resources and are retained as author notes. They do not create new models, textures, custom terrain types or arbitrary mechanics. Extend such content in Aurora.

Projects support up to 16 areas, 16 rooms per area, 48 NPCs, 64 encounters, 64 items, 100 furnishings and 16 quests with up to 20 objectives each. Overcrowded rooms are rejected during export. The checker catches disconnected rooms, conflicting exits, invalid objective targets, nonterminating branches and common quest-gate deadlocks. Compilation and layout validation cannot prove game event timing, walkability or encounter balance; playtest before sharing a finished adventure.

## Development and provenance

Run `python -m unittest discover -s tests -v` from this directory. Native export tests run when the local NWN installation and compiler are available. See VALIDATION.md for completed checks and remaining tests.

The Windows compiler is [nwnsc v1.1.5](https://github.com/nwneetools/nwnsc/releases/tag/v1.1.5), with its license included. Native API and SQLite calls were checked against the installed nwscript.nss and SQLite_README.txt; tiles were checked against installed .set resources. The provider follows [OpenAI's structured-output documentation](https://developers.openai.com/api/docs/guides/structured-outputs). Role Weaver server code is credited in ROLE-WEAVER-LICENSE.txt (MIT, RoleWeaverInfo, 2026).

The older courier-specific companion is retained at /legacy; its documentation is archived locally as README-0.1.md, PLAYTEST-0.1.md and VALIDATION-0.1.md. Format-1 projects remain separate from the new format-2 module authoring workflow.

