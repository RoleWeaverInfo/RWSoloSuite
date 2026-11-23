# Import and edit native missions

Available in Role Weaver Module Studio **1.2.0** for Windows, Linux and macOS. Upgrade both the creator's Studio and players' services before using a general-import mission profile. Emberseal remains the only bundled example; no community module is needed or distributed for the automated tests.

## Review and choose control

1. Import a normal NWN `.mod` under **Module Conversion**, with its required HAK/TLK dependencies. Configure the installed NWN folder so compiled engine calls can be identified. Reimport older reports if they have unknown action IDs or missing scripts.
2. Open **Missions & storyline** and select a journal mission. Choose **Copy to editable Studio mission**. Each draft initially keeps **original module quest** control.
3. In **Mission settings & rewards**, review the recovered description and choose a unique placed NPC as quest giver. The final hand-in follows this selection.
4. Select objective cards. Change **Needs review** to a supported type and bind a native target. Add, remove and reorder objectives. The initial ordering follows journal presentation and is only a suggestion: it is not a recovered execution graph. A name match or compiled call can suggest a target, but you must review it.
5. Inspect **Recovered reward evidence**. A single recoverable literal gold/XP award is suggested; multiple or dynamic amounts start at zero. Calls can be conditional, repeated or unreachable. Choose the intended completion totals rather than assuming that all listed awards should be added together.
6. Check the objective and reward review boxes. Changing objective order/targets or reward amounts clears the corresponding review. Use **Check edits**.
7. Choose **Use editable Studio mission (experimental)** for compatible missions and confirm the warning. Leave others under **Keep original module quest**. Up to 64 drafts can coexist, with up to 20 ordered objectives per mission.
8. **Save conversion edits**, build an AI-enabled copy, install it and start a **new game**. Existing saved games do not migrate to a different mission definition. Switching back to original control also requires a rebuild and new game; the inactive draft remains saved.

Incomplete or blocked drafts can be saved while their control remains original. Private native review notes/arrows remain annotations. Only a reviewed Studio mission's solid objective sequence becomes executable.

## Supported objectives and rewards

| Type | Engine check |
| --- | --- |
| Possess item | The player has an item with the selected native tag. Optional consumption is rechecked at hand-in and occurs then, not at first pickup. Companion storage does not satisfy it. |
| Visit area | The player enters the area with the selected unique native tag. |
| Talk to character | The current objective's uniquely tagged NPC is spoken to nearby through a reached dialogue node, the task menu or an offered AI action. |
| Defeat creature | The selected uniquely placed creature's death is observed. Its original death script is chained; normal combat XP remains native. Death observed before quest acceptance can count. |
| Final hand-in | Return to the selected giver after earlier objectives and required items are checked. Completion gold and XP are paid once. |

The generic importer supports ordered objectives and gold/XP completion rewards. It does not reconstruct arbitrary branches, timed challenges, campaign transitions, scripted item rewards or every native quest condition. Ambiguous/dynamically spawned targets are not silently substituted for uniquely placed creatures.

## What Studio changes

The original module snapshot is read-only. Conversion builds a separate `.mod` with its matching `.rwproject.json`.

For each enabled generic mission, Studio replaces its journal category and suppresses identified `AddJournalQuestEntry`, `RemoveJournalQuestEntry`, `GiveGoldToCreature` and `GiveXPToCreature` call sites. Engine argument expressions, branches, local variables and other calls remain. Direct quest writes in dialogue fields are removed for the selected tag. Other journal categories and map/placement resources retain their native data.

This is deliberately narrower than rewriting a whole script. A shared script can retain another mission's journal calls, but shared or ambiguously attributed rewards block takeover. Dynamic journal tags, unreadable/truncated scripts, missing dependencies, unresolvable helper calls, deferred-action scripts being patched, dependency-owned writer scripts, and associated item/destruction/spawn effects need further work or a dedicated adapter. The dashboard lists the reason. It still permits reviewing and editing an inactive draft.

The export includes `preservation.json` with the actual changed resource hashes and selected call sites. `original-scripts` backs up replaced native bytecode and any original source/debug files. Because a reliable source decompiler is not provided, patched native scripts remain compiled-only in the converted module: their stale `.nss`/`.ndb` files are removed so Aurora cannot silently restore the old journal/reward code. Generated Studio runtime source is included and maps remain editable in Aurora.

Native conditions and non-reward effects still execute. A new objective can disagree with a native variable, dialogue gate or prerequisite even if static isolation succeeds. A clean build is not proof of a complete playthrough. Retaining original control gives the broadest compatibility.

## Playing and testing

At a quest giver, choose **Discuss our tasks.**, or type `!missions <name or alias>` nearby. `!missions` alone works when exactly one eligible quest character is nearby. The task menus work without an AI request. AI conversations can offer acceptance, a current talk objective or checked hand-in; the service cannot assert kills, inventory possession, completion or payment.

Test acceptance, every objective, missing/consumed items, changed gold/XP, repeated reward requests, death before acceptance, save/reload and a second mission left native. Also test original dialogue prerequisites, transitions and side quests. State and payment guards live in the module's saved engine state; they do not depend on a service restart.

The dedicated adapter for the separately obtained legacy test adventure retains its extra chest and persuasion support. The general importer is not tied to that module, and does not bundle or restore it.
