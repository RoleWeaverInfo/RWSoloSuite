> Historical archive: the trial modules and instructions below are obsolete and are not bundled. The current sole example is The Emberseal of Briarwatch (rw_ember_v3.mod); use the current README, installation guide and PLAYTEST.md.

# Validation — 2026-11-13

Release: Role Weaver Solo Studio 0.1.0, foundation/playtest build.

Completed without launching NWN or Aurora:

- **21 automated tests passed.** They cover project structure, placement/scaling bounds, reserved tags, secret reveal rules, prohibited NPC actions, DM encounter allowlists, stale/paused/expired requests, command expiry receipts, database transaction cleanup, HTTP origin/host/token checks, path traversal, secret-free state responses, import/save round trips and native export.
- **18 executable NWScript resources compiled** using nwnsc 1.1.5 against the installed NWN:EE assets/header. Include files remain available in the module as editable source.
- The final two-area module contains **76 resources**. Every generated GFF resource was reparsed and round-tripped; the MOD resource index and byte payloads matched the export inputs.
- A three-area export test verified return travel links, a single quest cache, unique test object tags, AI dialogue choices, custom gold/XP values, compiled event scripts and lack of compiled NWNX dependencies.
- A real OpenAI NPC request for Edric succeeded using the authorized existing environment key. Mara's conversation preview also succeeded through the dashboard, with no quest action requested.
- A real AI authoring request produced an additional furnished cave, one support NPC and one encounter. The validated proposal exported successfully with 18 compiled scripts. It was retained separately under `data/validation-builds`, not applied to the user's sample project.
- The dashboard was inspected in the browser. Story, character, area/encounter, DM and export controls rendered. An NPC preview, build, installation and companion enablement succeeded. No browser console errors were observed. Responsive project controls were corrected during inspection.
- The installed `mc_courier_ai.mod` checksum matches its build manifest. The original `mc_courier.mod` checksum remains `acc8bae4fa48f0cca82170024052ae1d44075e901a9dc2dab2e7ec7794365dce`. The user's `mc_courier_aurora.mod` still exists and was not edited.

Final build ID: `e43a7f4326f5679f1629`.

Final AI module SHA-256:

```text
d0de9fe23d3aa6c1c627900a7dfacab9a2d5ff35766703a103120911d2c49f50
```

Still requires the user's test:

- Opening/saving this AI Edition in Aurora.
- Native in-game SQLite exchange, NPC chat display, party-control interaction and live acknowledgements.
- Quest completion through AI and authored dialogue, exact reward behavior, save/reload behavior, encounter placement and balance.
- Travel and walkmesh checks for newly generated areas.

The automated SQLite tests simulate the mailbox; they do not substitute for an in-game bridge test. Module compilation and GFF validation do not prove walkability or game event timing. See PLAYTEST.md for the concrete checks.
