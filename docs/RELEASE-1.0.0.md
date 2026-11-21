# Role Weaver Module Studio 1.0.0

**The first stable release** brings AI-assisted single-player module creation and a local AI gameplay service to Neverwinter Nights: Enhanced Edition. This promotes the rc3 feature set, with consistent application/package versions and stable GitHub release publishing. The reviewed Emberseal maps and compiled module are unchanged.

## Included capabilities

- Develop stories, character profiles, quests, encounters and populated areas. Interpret uploaded floorplans, review objects and scale, refine placement in the visual editor, and export standard Aurora-editable modules.
- Use AI NPC conversations, merchants, recruitable companions, familiars and summons, patrols and NPC social conversations in supported modules. The local AI service uses the player's own OpenAI or Gemini key; no NWNX or persistent-world server is required.
- Configure gameplay guardrails, track gameplay/authoring token usage, launch exported adventures through **Play in NWN**, and check for software updates from the dashboard.

## The Emberseal of Briarwatch

The sole bundled example includes the latest indoor keep, walled market courtyard and farm/forest road, and enclosed cave. It contains three areas, fourteen rooms, fifteen named characters, five combat encounters, two linked quests and three annotated floorplans. Designed for levels 3–4 with a two-member party, the adventure follows Queen Elowen's request to recover the stolen Emberseal.

Fresh installations load the editable project and ready-to-play build automatically. Existing installations can choose **Load Emberseal example**; an existing Emberseal draft is backed up before replacement. Its matching AI profile, generated geometry HAK and source resources are included. No CEP pack or AI generation credit is required to use the supplied build.

## Downloads

- **Windows x64:** `Role-Weaver-Module-Studio-1.0.0-Setup-x64.exe` for Windows 10/11.
- **Linux x64 / ARM64:** matching `Role-Weaver-Module-Studio-1.0.0-Linux-*.tar.gz`, built on Ubuntu 24.04.
- **macOS Intel / Apple Silicon:** matching `Role-Weaver-Module-Studio-1.0.0-macOS-*.zip`, for macOS 15 or later.
- **Adventure only:** `The-Emberseal-of-Briarwatch-1.0.0.zip`, also included in all application packages. Extract the complete ZIP; the HAK is required alongside `rw_ember_v3.mod`.
- **Developer source:** `Role-Weaver-Module-Studio-1.0.0-source.zip`; requires Python 3.12+, dependencies and a native compiler for rebuilding.

Application packages include Python, the NWScript compiler and local Guardrails AI validators. SHA-256 files accompany downloads. The payload JSON is a technical Windows installer inventory, not a required user download. Silent Bell and other trial modules are not packaged.

## Upgrade and play

The release is marked **Latest**, not prerelease. Existing rc3 native installations can use **Update software** to download, verify and install 1.0.0. Earlier versions without that button can install the matching package manually. Save your work and exit NWN before updating. Workspaces, builds, saved keys and installed adventures are preserved. Source checkouts are updated separately.

Start Role Weaver before playing and leave its service running for live AI. Conventional authored dialogue and quest menus remain available without AI. Use **Build & share → Play in NWN** for the included build. Start a new game when testing a newly installed module; existing saves retain their embedded resources.

## Compatibility and validation

You need your own desktop NWN:EE installation and game data. Aurora editing requires Windows. Studio's Linux ARM64 package does not imply native NWN game support on ARM64. Downloaded third-party HAK content remains subject to its authors' dependencies and redistribution terms.

Windows Setup remains unsigned; Mac apps are ad-hoc signed and are not Apple-notarized. Publishing 1.0.0 does not change those signing properties or claim manual gameplay certification on every platform. Release automation runs regression/interface checks, packaged runtime/compiler checks on all five targets, and Windows installation/startup/upgrade/uninstall checks before publication. Continue to review and playtest generated adventures.

[Installation](INSTALLATION.md) · [Emberseal guide](EMBERSEAL.md) · [AI NPCs and companions](PLAYER-GUIDE.md) · [Create an adventure](CREATE-AN-ADVENTURE.md)
