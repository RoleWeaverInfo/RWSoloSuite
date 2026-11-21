# Current example validation

**The Emberseal of Briarwatch** is the sole packaged example in 1.0.0. The pinned build is `11b6a6549ebb36e7b5d1`, with module `rw_ember_v3.mod` and project `emberseal_demo`.

The build preserves the latest revised keep, courtyard/road and cave layouts and embedded floorplans. It contains three areas, fourteen rooms, fifteen named characters, five combat encounters, two quests and 49 compiled scripts. It uses stock assets plus its included generated geometry HAK.

The builder completed native compilation and module resource-index checks. `bundled/emberseal/bundle.json` records SHA-256 hashes for the curated files. Release packaging verifies these hashes and scans for configured credentials, includes only this example, and creates its standalone adventure ZIP.

Tests cover fresh-workspace initialization, safe example re-import and backups, project/build/profile matching, archive contents and required HAK files. The native runtime smoke check confirms the fresh dashboard loads Emberseal and serves its download without a game installation or an AI request. GitHub release jobs validate Windows, Linux and macOS packages before publication.

Manual gameplay and Aurora validation remain required for the latest script revision. Follow [PLAYTEST.md](PLAYTEST.md). Historical Silent Bell and Courier trials are not current examples or release requirements.