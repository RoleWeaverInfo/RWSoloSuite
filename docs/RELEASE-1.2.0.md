# Role Weaver Module Studio 1.2.0

**The general mission importer** is available in the Windows, Linux and macOS packages. Import an existing NWN adventure, review its missions, edit compatible objectives and rewards, and choose original scripts or Studio control separately for each mission. Python and the NWScript compiler are included. **The Emberseal of Briarwatch remains the only included example.**

## New in this release

- **General mission drafts:** copy uniquely tagged native journal missions into the shared visual editor. Review suggested objectives, quest givers, native targets and recovered gold/XP evidence. Unresolved objectives are marked for review; journal order is not treated as a proven walkthrough.
- **Independent control:** keep original scripts for some missions while enabling experimental Studio control for others. Drafts start inactive. Review objective bindings and rewards before enabling takeover; save incomplete drafts in original mode.
- **Editable objectives and rewards:** ordered talk, visit, item-possession and defeat objectives, a selected quest giver/final hand-in, optional item consumption, and gold/XP completion rewards. Native engine checks govern progress and prevent repeat payment; AI cannot assert success.
- **Task menus and AI actions:** compatible converted missions offer **Discuss our tasks.** and `!missions <name or alias>` near the quest character. These menus work without an AI request. AI conversations can offer acceptance, the current talk objective and checked hand-in.
- **Scoped script conversion:** suppress identified journal/reward calls while retaining argument evaluation, branches and other calls. Maps and placements remain byte-identical. Exported preservation reports list changes and back up original scripts. Stale source/debug files for patched native bytecode are removed from the converted copy so Aurora cannot silently restore old rewards.
- **Updated guides and checks:** the new general-import guide explains review, compatibility, testing and backups. Release checks verify the new runtime assets and sole Emberseal example. Game-dependent tests require real NWN archives, and service-presence tests no longer depend on crossing a wall-clock second.

## Downloads

| Platform or content | Download |
| --- | --- |
| Windows 10/11 x64 | [Windows installer](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.2.0/Role-Weaver-Module-Studio-1.2.0-Setup-x64.exe) |
| Linux x64 | [Linux x64 archive](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.2.0/Role-Weaver-Module-Studio-1.2.0-Linux-x64.tar.gz) |
| Linux ARM64 | [Linux ARM64 archive](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.2.0/Role-Weaver-Module-Studio-1.2.0-Linux-arm64.tar.gz) |
| macOS Intel | [macOS x64 app](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.2.0/Role-Weaver-Module-Studio-1.2.0-macOS-x64.zip) |
| macOS Apple Silicon | [macOS ARM64 app](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.2.0/Role-Weaver-Module-Studio-1.2.0-macOS-arm64.zip) |
| Emberseal adventure only | [Adventure and Aurora resources](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.2.0/The-Emberseal-of-Briarwatch-1.2.0.zip) |
| Developer source | [Source ZIP](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/download/v1.2.0/Role-Weaver-Module-Studio-1.2.0-source.zip) |

Linux archives target Ubuntu 24.04 or compatible newer desktops. Mac apps require macOS 15 or later. Windows Setup is unsigned; Mac apps are ad-hoc signed and not Apple-notarized. SHA-256 files accompany downloads. The Windows payload JSON is an installer inventory, not a required user download. Application packages include Python; the developer source ZIP requires Python 3.12+ and dependencies.

## Upgrade and play

Save your work, exit NWN and stop Studio before manually installing. Existing native installations can use **Update software** to download and install the matching release. Your projects, saved keys, builds and installed modules are preserved. Source checkouts are updated separately.

Use **Studio 1.2.0 or later on both creator and player computers** for general-import mission profiles. Keep each `.mod` with its matching `.rwproject.json`. Rebuild and begin a **new game** after changing objectives, rewards or control mode; existing saves retain their old resources. Start Role Weaver before NWN and keep it running for live AI.

Emberseal's reviewed project, module and geometry are unchanged. Every application package includes its project, compiled `rw_ember_v3.mod`, matching profile, geometry HAK and floorplans. The adventure is also available as a separate ZIP. No Snow Hunt files, other community adventures, personal workspaces or API keys are bundled.

## Compatibility and limits

Mission takeover remains **experimental**. The importer is not a full decompiler and does not reconstruct arbitrary branching, timed logic or every reward type. Missing or incomplete script evidence, dynamic journal tags, shared rewards, deferred actions in scripts being patched, dependency-owned writers and associated item/destruction/spawn effects can require a dedicated adapter. The dashboard explains these conflicts and keeps those missions native while allowing inactive draft editing.

Native conditions, local variables and other side effects still run. Edited objectives can contradict them even after static checks pass. Review the preservation report and playtest acceptance, every objective, consumed items, repeat reward requests, save/reload and unrelated quests before sharing. The module's maps remain editable in Aurora; patched native scripts are compiled-only with their originals backed up.

You need your own desktop NWN: Enhanced Edition installation and game assets. NWNX is not required for the added service; conversion does not remove a source module's own extension dependencies. Aurora editing requires Windows. Linux ARM64 Studio support does not imply native NWN game support on ARM64. Live AI uses your own OpenAI or Gemini key and provider limits; local mission analysis, editing and compilation need no AI request.

Publication requires unit/interface checks and packaged runtime/compiler checks on all five targets, plus Windows install/startup/upgrade/uninstall checks. These checks do not constitute a complete NWN playthrough on every platform.

[General mission importer](https://github.com/RoleWeaverInfo/RWSoloSuite/blob/v1.2.0/docs/GENERAL-MISSION-IMPORT.md) · [Convert a module](https://github.com/RoleWeaverInfo/RWSoloSuite/blob/v1.2.0/docs/CONVERT-A-MODULE.md) · [Installation](https://github.com/RoleWeaverInfo/RWSoloSuite/blob/v1.2.0/docs/INSTALLATION.md) · [AI NPCs and companions](https://github.com/RoleWeaverInfo/RWSoloSuite/blob/v1.2.0/docs/PLAYER-GUIDE.md)
