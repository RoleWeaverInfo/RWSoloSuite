# Role Weaver Module Studio

Build single-player Neverwinter Nights: Enhanced Edition adventures with AI-assisted story design, floorplan interpretation, populated areas, quests, merchants and companions. Play locally with optional AI conversations and export standard modules for Aurora editing.

## Get started

Download **version 1.2.0** from [GitHub Releases](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/latest). Application packages include Python: Windows x64 installer, Linux x64/ARM64 archives, and macOS Intel/Apple Silicon apps. See the release notes for supported OS versions and known limitations. The repository and release downloads are public; no GitHub sign-in is required.

- [Installation, API keys and updates](docs/INSTALLATION.md)
- [Talk to AI NPCs and use companions](docs/PLAYER-GUIDE.md)
- [Create an adventure with ChatGPT and Studio](docs/CREATE-AN-ADVENTURE.md)
- [Convert an existing module: step-by-step guide](docs/CONVERT-A-MODULE.md)
- [Included Emberseal adventure](docs/EMBERSEAL.md)
- [Release notes](docs/RELEASE-1.2.0.md)
- [Guardrails and token usage](GUARDRAILS-AND-USAGE.md)

Start Role Weaver before opening NWN. The service opens a local dashboard at `http://127.0.0.1:8766`. Normal startup starts only the service. Install and register the adventure's matching `.mod` and `.rwproject.json`, then open NWN. You can also use **Build & share → Play in NWN** to install and launch an exported build directly. Closing the browser leaves the service running; use **AI service → Stop Role Weaver** when finished.

You need your own NWN:EE installation for its game resources. Aurora editing requires Windows; generated modules can be transferred from Linux/Mac. No game assets, personal workspaces or API keys are distributed with Studio.

## Included example: The Emberseal of Briarwatch

**The Emberseal of Briarwatch** is the only bundled example. Fresh installations open its editable project and include a compiled `rw_ember_v3.mod` build with its matching AI profile, required geometry HAK and three annotated floorplans. Queen Elowen asks you to recover a stolen ward from the goblin chieftain Skarn Ashhand and promises 300 gold. Explore the keep, walled market courtyard and farm/forest road, then Ember Hollow. Designed for levels 3–4 with a two-member party.

Third-party conversion inputs, including Snow Hunt, are not included in the repository or release downloads. Import your own legally obtained modules. Conversion compatibility support does not include the original adventure, extracted profiles, maps, dialogue or content packs.

Use **Build & share → Play in NWN** to install and start the included build, or download **Share / Aurora ZIP** there. The release page also provides **The-Emberseal-of-Briarwatch-1.2.0.zip**, ready for play and Aurora editing. Extract the complete ZIP; its HAK is required. No regeneration or AI generation credit is needed to play the supplied build.

On an existing installation, choose **Load Emberseal example** in the sidebar. An existing Emberseal draft is backed up before replacement; other projects, modules and saves are preserved. Silent Bell, the Courier and their trial modules are not included as examples. The internal `authoring-template.erf` is a build resource, not a selectable adventure.

## Launch, update and play

- **Play in NWN:** install a selected exported build and its packaged dependencies, register its matching AI profile, and open character selection. Exit an existing NWN session first; use NWN's own Load Game menu for saves.
- **Update software:** check public GitHub releases, download the correct platform package, verify its checksum, then install and restart the service and dashboard together. Projects and saved keys are preserved. Automatic installation applies to native packages; source checkouts are never overwritten.
- **In-game service checks:** newly built AI modules report when Role Weaver is unavailable or paused and announce reconnection. Type `!studio` to check without using AI tokens. A module cannot directly start desktop software.
- **Conversation and companion defaults:** new NPCs allow AI conversations, social chat and companion visits. Companions allow movement, accessible container inspection and item exchanges. Creators retain individual controls; animals retain nonverbal profiles, and native storage and item protections remain active.

The included Emberseal build already uses these defaults and service checks. For another existing adventure, choose **Companions** or **Behaviors → Apply conversation & storage defaults to this project**, review the changes, save and rebuild. Start a new game to test the new module; saved games retain their older resources. Existing creator opt-outs stay unchanged unless you apply the defaults.

## Your AI provider

**Local settings → Set up your AI** guides users to obtain their own Gemini or OpenAI key, save it locally, and choose separate gameplay and authoring models. Gemini offers a limited free tier for eligible models/accounts; OpenAI API usage is paid. Follow the current pricing and terms linked in the interface. A successful model-access check does not verify generation credit, quota or billing.

Saved keys use Windows DPAPI, macOS Keychain or Linux Secret Service and are excluded from project exports. Environment keys remain supported. Gameplay guardrails and token tracking are available in the dashboard.

## Source development and packaging

Version 1.2.0 includes a **shared visual mission editor**. In **Quests & endings**, AI-generated missions appear as editable mission and objective maps: edit story text, targets, choices, prerequisites and rewards, then check, save and rebuild. These are the generated module's executable quest definitions. In **Module Conversion → Missions & storyline**, review native journal stages with dialogue and compiled-script evidence, edit journal names/text for a new copy, and record private plot notes and reviewed connections. By default, native quest triggers and rewards remain controlled by the original scripts; review arrows do not rewrite them. Both editors support pan/zoom and undo/redo. See the [creation walkthrough](docs/CREATE-AN-ADVENTURE.md#6-edit-the-story-and-missions-visually) and [native mission review guide](docs/MODULE-ANALYSER.md#review-and-edit-native-missions).

**General mission importer, new in 1.2.0:** native journal missions can be copied into editable drafts with suggested objectives, native targets and recovered gold/XP evidence. Choose original scripts or experimental Studio control separately for each mission. Missing evidence and unsupported or shared script effects are flagged; blocked missions can still be edited as inactive drafts. See the [general mission import guide](docs/GENERAL-MISSION-IMPORT.md) for review steps, script backups and playtesting.

Studio includes **Module Conversion** in its own dashboard sidebar tab. Import a normal NWN `.mod` to inspect its story evidence, characters, encounters, journal quests, dialogue branches and compiled NWScript. After review, **Create an AI-enabled copy** adds free-form NPC conversations, native merchant support and companion capabilities while retaining the original maps, encounters and stores. Quest scripts remain native unless a supported mission is explicitly switched to Studio control. The original module remains unchanged. Profiles include authored character descriptions and setting information. **Generate detailed AI profiles** uses your authoring model for richer personalities and backgrounds; review them before conversion. Native NPC lines and player replies are remembered as they occur, while unseen quest branches remain outside AI prompts. Store-linked characters receive AI merchant abilities by default, with per-character controls. AI answers stock questions in chat. Explicit trading requests open the native store directly where a safe shortcut exists, preserving original dialogue gates and pricing scripts. Converted copies require NWN: Enhanced Edition and the updated service. Local analysis and conversion need no API calls; gameplay uses your own key. See the [Module Conversion guide](docs/MODULE-ANALYSER.md) for installation, dependencies, preservation checks and limitations.

The source ZIP is separate from the Python-included application downloads. Use Python 3.12+ (release builds use 3.13). Create a virtual environment and install `requirements-guardrails.txt` and `requirements-platform.txt`. On Linux/Mac, build the native NWScript compiler using `python installer/build_nwnsc.py`; CMake, Bison 3+ and a C++ compiler are needed. Start with `python service.py` or the supplied source launcher.

Run `python -m unittest discover -s tests`; standalone JavaScript checks are in `tests/*_checks.js`. The Python suite supplies input to `tests/*_fixture.js`; those helpers are not standalone commands. Game-dependent tests need your own NWN installation and are skipped when unavailable. See [packaging instructions](installer/README.md) for native application builds and Windows Setup. `python package.py` creates a clean source ZIP containing the pinned Emberseal example and a separate Emberseal adventure ZIP. It never includes personal `data` or other examples. CI runs the native build matrix and publishes tagged releases only after all build jobs pass.

## License

See [ROLE-WEAVER-LICENSE.txt](ROLE-WEAVER-LICENSE.txt). Included third-party components retain their own licenses. Respect NWN and custom-content authors' redistribution terms.
