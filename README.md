# RWSoloSuite — Role Weaver Module Studio 0.2

An AI-assisted authoring tool for complete, standalone Neverwinter Nights: Enhanced Edition adventures. Describe a story and its world, review the generated game content, edit it, and export a native Aurora module. No persistent-world server is involved.

## From a Git checkout

Run **Start Module Studio.cmd** from this folder. The Silent Bell is initialized automatically. Import **examples/starlight_trial.rwproject.json** for the AI-generated example, or **examples/silent_bell.rwproject.json** to restore a separate copy of the sample. Build modules through **Build & share**; generated modules, runtime data and local settings are excluded from Git.

## Start creating

1. Run **Start Module Studio.cmd**. The editor opens at **http://127.0.0.1:8766**. Python 3.10+ and an installed Windows copy of NWN:EE are required; no Python packages need installing. The bundled compiler is used automatically. Check game and user folders in Settings on another computer.
2. Open an example or choose **New adventure**. Write the storyline, tone, public summary, opening, ending, intended levels and party size.
3. In **Areas & rooms**, specify area type, width/height, room count, appearance and purpose. Generate the room layout, connect the rooms, and edit each exit's side and destination. Preview the exact corridor plan. One tile is 10 metres; north is up.
4. In **AI DM · Adventure design**, select **Complete adventure**, or a narrower scope, and give your instructions. The AI uses your story, room plans and character notes. Existing area type, size and requested room count are preserved. It proposes native quests, characters, dialogue, encounters, items and furnishings. Review the proposal before applying it; the last applied proposal can be undone.
5. Edit the generated content. **Characters** exposes personality, knowledge, secrets, motivation, game notes, ordinary dialogue and optional AI conversation profiles. **Encounters & items** includes combat, ambushes, puzzles, treasure and story interactions. **Quests & endings** defines objectives, prerequisites, rewards and branching decisions.
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

Both are included as editable projects and exported modules. They compile and pass structural checks; **Aurora and in-game playtesting are still required**. See PLAYTEST.md. The original Missing Courier module, the user's Aurora copy and the previous AI edition were preserved.

## Share and edit in Aurora

For ordinary play, share the .mod or its share ZIP. Players copy the .mod into their NWN user modules folder and start a new single-player game. The complete story and native gameplay are in that file; the application, project file, API key and server are unnecessary for ordinary play. NWN:EE itself is required.

Open the .mod in Aurora to inspect and edit areas, placed objects, conversations, journal and NWScript. The ZIP also contains source resources, a layout plan, validation report and .rwproject.json. Use Save As for an Aurora-edited edition. **Aurora changes are not imported back into Studio**; rebuilding from the project does not preserve separate Aurora edits.

To share the authoring tool, distribute Role-Weaver-Module-Studio-0.2.0.zip. The recipient sets their own game paths and API credentials if they want AI generation. No credentials or personal settings are included.

## Optional AI conversations while playing

In **Build & share**, enable optional freeform NPC conversations before building. The normal story still works independently. Players who want live AI run **Start AI Player.cmd**, import the matching .rwproject.json if necessary, and use their own OPENAI_API_KEY.

Speak to an AI-enabled NPC, choose **Talk freely with AI**, close the dialogue and type `!ai Your question` in the normal chat bar. Alternatively use `!talk alias Your question` nearby, or `!dm Give me a hint`. NPC aliases are shown in the character editor. Stand within 12 metres and in line of sight. Keep the game unpaused while waiting; replies are delivered on its heartbeat and requests expire after about 100 seconds. AI conversation can start an offered quest, complete its current talk objective, and select an explicitly chosen authored branch. The ordinary NPC menu uses exactly the same quest state and remains available. Item recovery, combat, visits and object interactions are confirmed by the game. Replies cannot invent new objectives or grant arbitrary rewards.

NPC prompts include their own knowledge, unlocked secrets and the relevant quest context. Secrets can unlock after a selected quest completes. The AI DM receives the full storyline to provide guidance. Recent dialogue and game/party context are sent to OpenAI for these optional live requests. The Responses API uses strict schemas and store: false. Studio limits attempted requests to 60 per hour per process. Settings retain the tested Role Weaver model, gpt-5.6-luna.

The local companion listens only on loopback, with host/origin checks and a request token. Its SQLite mailbox uses the NWN user database rwsp_bridge; old sessions and expired responses are rejected. This adapts Role Weaver's scoped character knowledge and game-authoritative rules without the PW add-on's Linux/NWNX/Redis services. It does not alter the game's party-control system.

## Current authoring boundaries

This is an initial working toolset, not unlimited asset generation. It supports castle interiors, stone dungeons, caves/mines and forests; rectangular rooms/clearings; explicit routed corridors; 16 stock creature templates; three stock NPC appearances; nine furniture types; quest tokens and healing potions. Appearance descriptions guide the AI's selection and placement of those resources and are retained as author notes. They do not create new models, textures, custom terrain types or arbitrary mechanics. Extend such content in Aurora.

Projects support up to 16 areas, 16 rooms per area, 48 NPCs, 64 encounters, 64 items, 100 furnishings and 16 quests with up to 20 objectives each. Overcrowded rooms are rejected during export. The checker catches disconnected rooms, conflicting exits, invalid objective targets, nonterminating branches and common quest-gate deadlocks. Compilation and layout validation cannot prove game event timing, walkability or encounter balance; playtest before sharing a finished adventure.

## Development and provenance

Run `python -m unittest discover -s tests -v` from this directory. Native export tests run when the local NWN installation and compiler are available. See VALIDATION.md for completed checks and remaining tests.

The Windows compiler is [nwnsc v1.1.5](https://github.com/nwneetools/nwnsc/releases/tag/v1.1.5), with its license included. Native API and SQLite calls were checked against the installed nwscript.nss and SQLite_README.txt; tiles were checked against installed .set resources. The provider follows [OpenAI's structured-output documentation](https://developers.openai.com/api/docs/guides/structured-outputs). Role Weaver server code is credited in ROLE-WEAVER-LICENSE.txt (MIT, RoleWeaverInfo, 2026).

The older courier-specific companion is retained at /legacy; its documentation is archived locally as README-0.1.md, PLAYTEST-0.1.md and VALIDATION-0.1.md. Format-1 projects remain separate from the new format-2 module authoring workflow.

