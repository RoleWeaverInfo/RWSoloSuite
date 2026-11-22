# Read-only module analyser

This feature is available in the current source checkout; it is not included in the published 1.0.0 packages yet.

Open **Module analyser** in the dashboard sidebar. Choose an existing Neverwinter Nights 1 / Enhanced Edition `.mod` file and click **Import and analyse**. Alternatively, expand **Or use a path on this computer**, enter its full path, and click **Analyse local file**. A `.rwproject.json` file is not required.

Studio makes a private snapshot in its workspace under `module-analysis`. It reads the module without executing its scripts, loading NWN, changing maps, adding AI NPCs or overwriting your editable project. You can leave the page while the analysis runs and return to select the saved report. Keep the service running until it finishes.

If the downloaded adventure has its own dependency folders, enter their parent folder in **Dependency folder (optional)**. Studio searches its subfolders for declared HAK and TLK names. Local-path imports automatically search beside the original module when no explicit dependency folder is supplied. These per-import searches do not change your global content settings or install the packs. Folder search is bounded to eight levels and 50,000 entries, with a warning when exceeded.

## What you can review

- **Overview:** recovered module description, authored story excerpts, resource counts, missing dependencies and limits.
- **Areas:** names, tags, tilesets and tile dimensions; no geometry is regenerated.
- **Characters:** placed creatures and creature blueprints, authored descriptions, dialogue references, classes, faction IDs, inventory resource references and linked scripts. Personality and knowledge are only recoverable to the extent the author expressed them in descriptions and dialogue.
- **Encounters:** native encounter triggers and blueprints, spawn limits and creature definitions. Fixed placed enemies appear under Characters; scripted spawns appear in the script findings.
- **Quests:** journal categories and stages, completion flags, authored text and links to compiled-script evidence. A journal entry number alone does not establish progression order.
- **Dialogue:** NPC and player text, starting nodes, reply links, condition scripts and action scripts. Conditional branches may contradict each other because they represent different playthroughs.
- **Scripts:** compiled `.ncs` disassembly, engine function calls, locally traceable constant arguments, string literals and relative branch targets. Select **Inspect** to see details and download the full decoded listing. Source `.nss` and debug-symbol `.ndb` presence is reported; debug symbols are not interpreted in this version.
- **Dependencies:** declared HAKs and custom talk tables, with found/missing status.

Sections support search and pagination. **Download JSON report** exports the recovered inventory and findings. The script panel shows bounded excerpts; its disassembly download includes every instruction decoded within the stated budget.

## Compiled scripts and reliability

The analyser reads NWScript bytecode directly; original `.nss` source is not required. With a configured NWN installation, it uses that installation's `nwscript.nss` definitions to name engine actions. Without those definitions, it displays numeric action IDs. Quest journal text, dialogue and creature records still work without an installation.

This is static analysis, not full source recovery or a verified walkthrough. Literal arguments are tracked conservatively within a basic block; `null` means unresolved. Calls may be conditional, delayed or unreachable. An `AddJournalQuestEntry` call with a recovered quest tag is stronger evidence than a matching string constant; the report labels this distinction. Dynamic script names, external databases, missing resources and complex state can leave gaps. Unsupported instructions and malformed resources are reported instead of guessed.

The report inventories module definitions first and searches declared HAKs and installed game resources for missing references. It does not simulate runtime override precedence, NWSync, campaign databases or custom engine extensions. Put required HAKs in the configured custom-content folder or NWN `hak` folder and custom TLKs in NWN's `tlk` folder. Configure **Local settings** before importing. Reimport after adding missing dependencies to produce a new snapshot/report.

Uploads accept `.mod` archives below 4 GB. Inspection budgets are separate from upload size: 15,000 resources, 2,000 dialogues, 2,500 scripts, 256 MB of parsed resource data, 64 MB of compiled script data, 8 MB per script and 250,000 instructions per script. Truncation and unsupported data are disclosed. These limits apply only to the analyser, not the area-design HAK catalog.

## Optional AI interpretation

Local inspection does not call an AI provider or need an API key. Expand **Optional AI explanation** and click **Explain with AI** to request a story and quest interpretation from your configured authoring model. Selected text and script excerpts are sent to that provider using your saved key. Usage counts as module creation; the provider's billing and quota rules apply.

The explanation cites numbered evidence entries that you can expand. Missing citations are rejected. Valid citations are not proof that an interpretation is correct: review inferred motives, chronology and quest conditions against the recovered text and scripts. The AI receives bounded excerpts, not every byte of a large module. Module text is treated as untrusted content rather than instructions.

## Keeping and removing reports

**Delete analysis** asks for confirmation and removes only that report and its private snapshot. It does not delete the original module, installed modules, saves or Studio projects. Reports are local and are not automatically shared. Respect the module author's permissions before distributing extracted content.

Importing does **not** convert a conventional module to Role Weaver gameplay. AI NPC conversion, companion injection and replacement of quest scripts remain future work; this analyser supplies the evidence needed to review such a conversion first.
