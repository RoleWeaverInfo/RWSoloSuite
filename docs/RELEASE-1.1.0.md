# Role Weaver Module Studio 1.1.0

**Module Conversion and editable missions** are now available in the Windows, Linux and macOS application packages. Python, the NWScript compiler and local Guardrails AI validators are included. **The Emberseal of Briarwatch remains the only bundled example.**

## New in this release

- **Module Conversion:** import an existing NWN `.mod`, inspect its story, characters, encounters, quests and dialogue, and analyse compiled NWScript even when source scripts are absent.
- **AI-enabled copies:** add character conversations, observed native-dialogue memory, detected native merchants and companion capabilities while preserving the original maps and placements. Original quest control is the default. NPC profiles can be reviewed and optionally expanded with the authoring model.
- **Shared visual mission editor:** edit generated adventures in **Quests & endings**. Review imported journal stages and script evidence under **Module Conversion → Missions & storyline**, with pan/zoom, notes, journal text edits and undo/redo.
- **Optional executable mission conversion:** copy a supported quest into an inactive draft, edit objectives and rewards, then explicitly opt into Studio control before rebuilding. The first experimental adapter supports Rival Ogre Mages in the audited Snow Hunt 1.01 archive only. Unsupported quests remain native. Snow Hunt must be obtained independently; its module, packs and generated copies are not included or hosted here.
- **Merchant fixes:** stock and personal-history questions remain conversations. Explicit trading requests use the native shop where a safe shortcut exists, retaining access conditions and pricing.
- **Distribution checks:** reject adventure resources outside the pinned Emberseal bundle and exclude third-party local conversion examples. Fixture-driven interface tests now run through their Python harness rather than being invoked without their inputs.

Start with the new [step-by-step conversion guide](https://github.com/RoleWeaverInfo/RWSoloSuite/blob/v1.1.0/docs/CONVERT-A-MODULE.md). It covers import, dependencies, NPC profiles, both mission modes, building, installation, testing and sharing.

## Downloads

| Platform or content | Download |
| --- | --- |
| Windows 10/11 x64 | [Windows installer](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.1.0/Role-Weaver-Module-Studio-1.1.0-Setup-x64.exe) |
| Linux x64 | [Linux x64 archive](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.1.0/Role-Weaver-Module-Studio-1.1.0-Linux-x64.tar.gz) |
| Linux ARM64 | [Linux ARM64 archive](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.1.0/Role-Weaver-Module-Studio-1.1.0-Linux-arm64.tar.gz) |
| macOS Intel | [macOS x64 app](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.1.0/Role-Weaver-Module-Studio-1.1.0-macOS-x64.zip) |
| macOS Apple Silicon | [macOS ARM64 app](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.1.0/Role-Weaver-Module-Studio-1.1.0-macOS-arm64.zip) |
| Emberseal adventure only | [Adventure and Aurora resources](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.1.0/The-Emberseal-of-Briarwatch-1.1.0.zip) |
| Developer source | [Source ZIP](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.1.0/Role-Weaver-Module-Studio-1.1.0-source.zip) |

Linux packages are built on Ubuntu 24.04 for compatible desktops. Mac apps require macOS 15 or later. Windows Setup is unsigned; Mac apps are ad-hoc signed and not Apple-notarized. SHA-256 files accompany downloads. The payload JSON is a technical Windows installer inventory, not a required user download. The source ZIP requires Python 3.12+ and dependencies; application packages do not require a separate Python installation.

## Upgrade and use

Save your work and exit NWN, then use **Update software** in an existing native Studio installation, or install the matching package manually. Workspaces, saved keys, builds and installed adventures are preserved. Source checkouts are updated separately. Start Role Weaver before NWN and leave the service running for live AI.

Converted modules require Studio 1.1.0 or later and their matching `.rwproject.json`. Rebuild and begin a **new game** to adopt module changes; existing saves retain their embedded resources. For ordinary conversion, original menus continue to handle quest actions. Supported Studio-controlled missions also check progression and rewards in NWScript; an AI promise alone cannot pay a reward.

The bundled Emberseal adventure and its reviewed geometry are unchanged from 1.0.0. Fresh workspaces load it automatically; existing users can choose **Load Emberseal example**. Its required geometry HAK and matching AI profile are included in every application package and the separate adventure ZIP.

## Limits and validation

This release does not convert arbitrary compiled quest logic into editable missions. Static script analysis is not a full decompiler or verified walkthrough. Mission takeover is experimental and limited to the explicitly supported adapter; imported quest notes/arrows do not rewrite scripts. Modified source versions, custom extensions, dynamic script names, external HAK dialogue and unusual shops may need manual work. Review preservation reports and playtest before sharing.

You need your own desktop NWN:EE installation and assets. Aurora editing requires Windows. Linux ARM64 Studio support does not imply native NWN game support on ARM64. Use your own AI key for gameplay; optional authoring AI calls and gameplay calls follow your provider's billing and limits. No personal workspaces, third-party module files or API keys are bundled.

Publication is gated on regression/interface checks, packaged runtime/compiler checks on all five targets, and Windows install/startup/upgrade/uninstall checks. These checks do not constitute a complete NWN playthrough on every operating system.

[Installation](https://github.com/RoleWeaverInfo/RWSoloSuite/blob/v1.1.0/docs/INSTALLATION.md) · [Convert a module](https://github.com/RoleWeaverInfo/RWSoloSuite/blob/v1.1.0/docs/CONVERT-A-MODULE.md) · [AI NPCs and companions](https://github.com/RoleWeaverInfo/RWSoloSuite/blob/v1.1.0/docs/PLAYER-GUIDE.md) · [Create an adventure](https://github.com/RoleWeaverInfo/RWSoloSuite/blob/v1.1.0/docs/CREATE-AN-ADVENTURE.md)
