# Role Weaver Module Studio 1.3.0

**AI dialogue controls and faster conversions** for Windows, Linux and macOS. Choose shorter, more natural replies during play, select nearby NPCs in converted adventures, and resume large profile-generation jobs with visible progress. Python and the NWScript compiler are included. **The Emberseal of Briarwatch is the only bundled example**, refreshed with the new AI response settings.

## New in this release

- **`!npcs` for converted adventures:** select a nearby AI character by name and distance, including characters whose original dialogue has no AI option. Ordinary action-free dialogue exits also receive AI choices regardless of their wording or language. Original quest and payment choices remain available.
- **`!aisettings` during play:** choose Brief, Natural or Detailed replies; Plain, Characterful or Dramatic speech; action descriptions; and follow-up questions. Defaults favor brief, plain speech without repeated greetings or unnecessary questions. Settings are saved with the game and do not require an AI request to change.
- **Companion preferences:** new companions inherit the shared response settings. Existing explicit companion preferences remain; each companion's Reply control can override the shared length.
- **Smoother large conversions:** cached NPC configuration, indexed character lookups and lighter heartbeat snapshots reduce recurring script work. Detailed merchant and companion context is collected for conversation requests. These fixes apply to future conversions and rebuilt copies.
- **Visible, resumable profile generation:** see saved profiles, the current batch, elapsed time and time waiting for the model. Each completed batch is saved. Pause after the current batch or resume unfinished characters after a failure or restart, preserving completed profiles and edits. Progress updates no longer repeatedly rebuild the editor.
- **Authoring request limits:** Studio's former 60-request hourly authoring cap is removed. Gameplay guardrails, token tracking and the provider's own billing and quotas still apply.
- **Longer filenames:** created and converted modules support up to 64 lowercase letters, digits and underscores before `.mod`, starting with a letter. The displayed adventure title remains separate; internal NWN resource IDs retain their short-name limits.
- **Documentation and packaging:** updated installation, conversion, creation and player guides, including a command reference. Emberseal's AI scripts are rebuilt while retaining its reviewed story, area layouts and geometry. Windows and Mac filename checks now compare resolved filesystem paths. Legacy project exports exclude conversion-only scripts that require the newer runtime.

The shared visual mission editor, general mission importer, AI merchants, companions, optional patrols and NPC social conversations remain included. Mission takeover is experimental and requires review and playtesting; source modules remain untouched.

## Downloads

| Platform or content | Download |
| --- | --- |
| Windows 10/11 x64 | [Windows installer](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.3.0/Role-Weaver-Module-Studio-1.3.0-Setup-x64.exe) |
| Linux x64 | [Linux x64 archive](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.3.0/Role-Weaver-Module-Studio-1.3.0-Linux-x64.tar.gz) |
| Linux ARM64 | [Linux ARM64 archive](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.3.0/Role-Weaver-Module-Studio-1.3.0-Linux-arm64.tar.gz) |
| macOS Intel | [macOS x64 app](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.3.0/Role-Weaver-Module-Studio-1.3.0-macOS-x64.zip) |
| macOS Apple Silicon | [macOS ARM64 app](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.3.0/Role-Weaver-Module-Studio-1.3.0-macOS-arm64.zip) |
| Emberseal adventure only | [Adventure and Aurora resources](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.3.0/The-Emberseal-of-Briarwatch-1.3.0.zip) |
| Developer source | [Source ZIP](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.3.0/Role-Weaver-Module-Studio-1.3.0-source.zip) |

Linux archives target Ubuntu 24.04 or compatible newer desktops. Mac apps require macOS 15 or later. Windows Setup is unsigned; Mac apps are ad-hoc signed and not Apple-notarized. SHA-256 files accompany downloads. The Windows payload JSON is an installer inventory, not a required user download. The developer source ZIP requires Python 3.12+ and dependencies.

## Use the new commands

Start Studio before NWN, register the matching `.rwproject.json`, and keep the service running. Enter commands in **Talk**, with the game unpaused and dialogue menus closed.

1. **Converted module:** type `!npcs`, choose an available character within 12 metres, then type a normal question. Use `!end` to finish. Visibility, combat, cutscene and creator permissions still apply. Use `!companions` for familiars and summons.
2. **Created or converted module:** type `!aisettings`, click a setting to cycle its choices, then close the panel and continue talking. The next request uses the new preferences. Save the game to retain them.
3. **Emberseal:** choose **Talk freely with AI**, or use an alias such as `!talk bram what swords do you sell?`. The `!npcs` selector is specific to converted adventures; Emberseal includes `!aisettings` and companion controls.

[Full NPC and companion guide](https://github.com/RoleWeaverInfo/RWSoloSuite/blob/v1.3.0/docs/PLAYER-GUIDE.md) includes defaults, per-companion overrides and troubleshooting.

## Upgrade existing adventures

Save your work and exit NWN before installation. Use **Update software** in an installed native app, or stop Studio and install/extract the matching download manually. Personal projects, keys and saves are preserved; source checkouts are updated separately.

Use **Studio 1.3.0 on creator and player computers** for these features. Updating the service alone does not replace scripts in modules or saves. For an older converted adventure, open its saved analysis, retain its completed profiles, choose **AI profiles & build → Create AI-enabled copy**, install the matching module/profile, and start a **new game**. AI profiles do not need regeneration. Old saved games keep their original runtime scripts.

On an existing workspace, choose **Load Emberseal example** to load the refreshed bundled build; a previous Emberseal draft is backed up. Install its module and included geometry HAK, then start a new game. The filename remains `rw_ember_v3.mod`; the new build has its own matching profile. Emberseal is included in every application package and also offered separately. No Snow Hunt, Pools of Radiance, other community adventure, personal workspace or API key is included.

## Compatibility

Requires your own desktop **Neverwinter Nights: Enhanced Edition**, a browser, and your own OpenAI or Gemini API key for live AI. The added service needs no NWNX or persistent-world server; it does not remove extensions required by a source module. Local analysis, mission editing and compilation need no AI request. Aurora editing requires Windows. Linux ARM64 Studio support does not imply native NWN game support on ARM64.

Release checks cover unit/interface tests and packaged startup/compiler checks on all five targets, plus Windows install/startup/upgrade/uninstall. They do not constitute a complete NWN playthrough on every platform.

[Installation](https://github.com/RoleWeaverInfo/RWSoloSuite/blob/v1.3.0/docs/INSTALLATION.md) · [Convert a module](https://github.com/RoleWeaverInfo/RWSoloSuite/blob/v1.3.0/docs/CONVERT-A-MODULE.md) · [Create an adventure](https://github.com/RoleWeaverInfo/RWSoloSuite/blob/v1.3.0/docs/CREATE-AN-ADVENTURE.md) · [Emberseal](https://github.com/RoleWeaverInfo/RWSoloSuite/blob/v1.3.0/docs/EMBERSEAL.md)
