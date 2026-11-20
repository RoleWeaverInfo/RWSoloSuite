# Role Weaver Module Studio 0.21.0-rc3

**The Emberseal of Briarwatch** is now the only bundled example. Fresh installations open its full editable adventure and include a ready-to-play build. Existing installations can use **Load Emberseal example**, which backs up an existing Emberseal draft and preserves other projects and installed modules.

The example contains the revised indoor keep, walled market courtyard and farm/forest road, and enclosed Ember Hollow cave: three areas, fourteen rooms, fifteen named NPCs, five combat encounters and two linked quests. All three annotated floorplans, the matching AI profile and generated geometry HAK are included. Play as a level 3–4 character with a two-member party; recover the stolen ward and return it to Queen Elowen for 300 gold.

## Downloads

- Windows x64 Setup, Linux x64/ARM64 packages, and macOS Intel/Apple Silicon apps include Python, the service/dashboard, Guardrails AI and the single Emberseal example.
- **The-Emberseal-of-Briarwatch-0.21.0-rc3.zip** is the standalone adventure/Aurora download. Extract the entire ZIP and install its HAK, not just the `.mod`.
- The developer source ZIP includes the same pinned example. It needs Python 3.12+, dependencies and a native compiler for rebuilding.
- SHA-256 checksum files accompany the downloads. The public repository needs no GitHub sign-in.

Silent Bell, Courier and other trial adventures are not included. The internal authoring template is an `.erf` resource, not another playable module. Existing personal workspaces, installed modules, saves and API keys are not removed during an upgrade.

## Other changes

The unpublished rc2 candidate was superseded by rc3 after updating the Windows installer test to expect the included Emberseal project instead of the former blank workshop.

- **Play in NWN** installs an exported build and its dependencies, registers its AI profile and opens character selection.
- **Update software** checks public releases, verifies downloads and offers installation/restart in native packages. Source checkouts are protected.
- Newly built AI modules check the local service and show disconnected/paused/reconnected messages. `!studio` checks without spending AI tokens.
- New NPCs and companions enable conversations, visits and accessible storage/item exchanges by default. Creator opt-outs and native protections remain available.

The published 0.21.0-rc1 installers predate the update button; install this version once using its platform package. Use a new game for the included module. Native dialogue and quests work offline; live AI requires Role Weaver and your own provider key.

Platform baselines remain Windows 10/11 x64, Ubuntu 24.04 x64/ARM64, and macOS 15 Intel/Apple Silicon. Windows Setup is unsigned; Mac apps are ad-hoc signed, not notarized. Aurora is Windows-only. Compilation and automated package checks do not replace manual gameplay testing on each platform.

[Installation](INSTALLATION.md) · [Emberseal guide](EMBERSEAL.md) · [AI NPCs and companions](PLAYER-GUIDE.md) · [Create your own adventure](CREATE-AN-ADVENTURE.md)
