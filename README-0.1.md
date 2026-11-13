# Role Weaver Solo Studio

A local adventure editor and AI companion for Neverwinter Nights: Enhanced Edition. This first release extends **The Missing Courier** with AI conversations for Edric, Mara and Tavin, an AI DM Assistant, and an Aurora module exporter.

## Start here

1. Double-click **Start Solo Studio.cmd**. The local dashboard opens at **http://127.0.0.1:8766**. Keep its launcher running while playing; Ctrl+C in the launcher stops it. No Python packages need installing.
2. The supplied project is **The Missing Courier — AI Edition**. The new module filename is **mc_courier_ai.mod**. The original `mc_courier.mod` and your `mc_courier_aurora.mod` are separate files.
3. In **AI DM Assistant**, choose **Start companion**. It is already enabled in the Studio instance prepared during implementation. Every new Studio process starts with the companion paused.
4. Start a **new single-player game** in NWN with the AI Edition module. Existing saves of the original module do not acquire the new scripts.
5. Talk to a key NPC and choose **Talk freely with AI**. Close the dialogue and use the normal chat bar:

   ```text
   !ai Where should I look for the courier?
   !talk mara How should I prepare for the cave?
   !talk tavin What happened to you?
   !dm Give me a useful hint without spoiling the quest.
   ```

Stand within 12 metres and in line of sight of an NPC for AI chat. Keep NWN running while a response is pending. Pausing or opening a menu can suspend its heartbeat; resume the game to deliver messages. Replies normally appear after the model response plus the next six-second heartbeat. A request times out after about 100 seconds.

AI is optional. The ordinary conversations, quest item, journal, combat, rewards, death/respawn, and saving remain native NWN features. Use those conversations if Studio or the API is unavailable.

## Author an adventure

- **Story & quest:** write the outline, public summary, tone, quest dialogue, item name and rewards. The private story goes to the DM; NPCs receive the public summary and their own scoped knowledge.
- **Characters:** edit names, appearances, personalities, knowledge, secrets, secret reveal stages, goals, boundaries, greetings and placement. Preview a conversation before building. The preview does not affect the game.
- **Areas & encounters:** add hall/cave areas, NPCs, stock creatures and furnishings; edit every authored encounter. New areas connect to the hall through usable travel signs. The placement diagram shows coordinates, not a walkmesh. Check the exact placement in Aurora.
- **Write with Role Weaver:** describe a change. The model proposes a complete project. Review it, apply it to the editor, then save. It never automatically installs its proposal.
- **Play & export:** build a snapshot, install the `.mod`, or download the Aurora ZIP and `.rwproject.json` companion file. Install backs up a differing existing module to `modules/RoleWeaverBackups` before replacing it.

The recovery template requires `mc_hall`, `mc_cave`, `mc_edric`, `mc_mara`, and `mc_tavin` and their original quest roles. Display names can change. The item stays in the cave cache; return it to the quest giver to finish. Keep prose, directions and reward claims consistent with your edits.

This foundation supports 2–8 template areas, 3–24 NPCs, up to 24 encounters and 64 extra furnishings. Creature choices currently are goblin and rat; decoration choices include tables, chairs, beds, shelves, barrels, crates, chests, signs and candles. Supplied hall/cave layouts already contain furnishings. New quest structures, arbitrary terrain generation, custom items and a broad creature catalogue are future work.

## DM Assistant during play

The dashboard shows the connected character, current area, quest stage and party member levels, classes, AC and current/max HP. Ask for a hint, scene narration or pacing suggestion. The DM may propose an existing **director encounter** in the current area; deployment requires an explicit button click. You can also choose an authored director encounter yourself. The game acknowledgement is the evidence that an action actually happened.

Placed encounters exist from the start. Director encounters are optional and can be deployed once per save. The native game checks the session, character, area, allowed encounter, distance, party health and combat state before applying the request. Move at least six metres from its map marker. Deployment is rejected during combat or below 50% combined nearby-party HP.

For enabled party scaling, creature count is `base + floor((nearby living party size - 1) / 2)`, with one additional creature at average party level 4 or higher, capped at the authored maximum (1–6). This is a transparent starting heuristic, not comprehensive encounter balance: it does not adjust creature statistics, equipment, spell resources or tactics. The DM can consider the richer snapshot when advising whether to deploy at all.

**Remove its creatures** removes only creatures created by that director encounter. It does not reset its spent flag, grant rewards, or change the authored encounters. Narration, spawn and cleanup are the only dashboard game actions; there is no arbitrary script-execution endpoint.

## Aurora and sharing

Open `Documents/Neverwinter Nights/modules/mc_courier_ai.mod` in Aurora. All areas, placed creatures, conversations, items, placeables, journal data and NWScript source/compiled scripts are native module resources. Save your Aurora edition under a separate filename. Retain the `sp_*` scripts, their module event hooks and the original quest resources for AI integration.

Studio project files and Aurora edits are separate authoring formats. Aurora changes are **not imported back** into the Studio form editor. Rebuilding uses the Studio project, not an Aurora-edited `.mod`. If you alter quest mechanics or tags in Aurora, update the corresponding profiles/scripts deliberately; otherwise AI context can become inaccurate.

For another computer, copy the Studio package and the `.mod` plus `.rwproject.json`. Import the companion file in Studio so it knows the build's exact character lore. Choose that computer's NWN installation/user folders in Settings and configure its own `OPENAI_API_KEY`. The launcher uses Python 3.10+ and the bundled Windows NWScript compiler. NWN must be installed to build and play; game asset archives are not bundled.

## API and local data

The launcher reuses the existing `OPENAI_API_KEY` from its process, user or machine environment. It does not write a key file. The tested default is the existing Role Weaver model setting, `gpt-5.6-luna`; change it in Settings if needed. Calls use the OpenAI Responses API with strict JSON schemas and `store: false`. API use is billed to the configured account. Studio caps attempted calls at 60 per hour per process.

AI requests send relevant story/character content, the player's message, recent conversation text and a party snapshot to OpenAI. Credentials never appear in the browser, `.mod`, project JSON or packages. This is local gameplay with optional online AI, not an offline language model.

The dashboard listens only on `127.0.0.1`. Host/origin checks and a per-process request token protect its write endpoints. Authoring projects and immutable build snapshots live in `data/`. The game creates a campaign SQLite database named `rwsp_bridge` in its user `database` folder. Studio recognizes `.sqlite3` and `.sqlite`; it only touches its own `sp_sessions`, `sp_requests` and `sp_commands` tables. Quest state, spent encounters and NPC conversation memory remain in the NWN save. Every module load generates a fresh transport session so old replies cannot advance a reloaded game.

## Verification and development

See **PLAYTEST.md** for the requested in-game and Aurora checks, and **VALIDATION.md** for completed checks. Run automated tests from this directory with:

```text
python -m unittest discover -s tests -v
```

The exporter uses the bundled `vendor/nwnsc/nwnsc.exe` ([upstream v1.1.5](https://github.com/nwneetools/nwnsc/releases/tag/v1.1.5)), with its license included. SQLite and NWScript calls were checked against the installed `ovr/nwscript.nss` and `lang/en/docs/SQLite_README.txt`. The provider follows the [OpenAI structured-output documentation](https://developers.openai.com/api/docs/guides/structured-outputs).

This implements Role Weaver's scoped NPC knowledge, bounded DM proposals and game-authoritative application model for a native local runtime. It does not load the PW add-on's Linux/NWNX/Redis runtime. The original server project is credited in **ROLE-WEAVER-LICENSE.txt** (MIT, RoleWeaverInfo, 2026).
