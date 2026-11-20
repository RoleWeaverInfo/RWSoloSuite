# Role Weaver Module Studio

Build single-player Neverwinter Nights: Enhanced Edition adventures with AI-assisted story design, floorplan interpretation, populated areas, quests, merchants and companions. Play locally with optional AI conversations and export standard modules for Aurora editing.

## Get started

Download the current [release](https://github.com/RoleWeaverInfo/RWSoloSuite/releases). Application packages include Python: Windows x64 installer, Linux x64/ARM64 archives, and macOS Intel/Apple Silicon apps. See the release notes for supported OS versions and candidate limitations. The repository and release downloads are public; no GitHub sign-in is required.

- [Installation, API keys and updates](docs/INSTALLATION.md)
- [Talk to AI NPCs and use companions](docs/PLAYER-GUIDE.md)
- [Create an adventure with ChatGPT and Studio](docs/CREATE-AN-ADVENTURE.md)
- [Release notes](docs/RELEASE-0.21.0.md)
- [Guardrails and token usage](GUARDRAILS-AND-USAGE.md)

Start Role Weaver before opening NWN. The service opens a local dashboard at `http://127.0.0.1:8766`. Normal startup starts only the service. Install and register the adventure's matching `.mod` and `.rwproject.json`, then open NWN. In the latest source version, you can also use **Build & share → Play in NWN** to install and launch an exported build directly. Closing the browser leaves the service running; use **AI service → Stop Role Weaver** when finished.

You need your own NWN:EE installation for its game resources. Aurora editing requires Windows; generated modules can be transferred from Linux/Mac. No game assets, personal workspaces or API keys are distributed with Studio.

## Latest development features

These changes are in the source code and are newer than the published **0.21.0-rc1** application packages. See the [unreleased changelog](RELEASE-NOTES.md) for details.

- **Play in NWN:** install a selected exported build and its packaged dependencies, register its matching AI profile, and open character selection. Exit an existing NWN session first; use NWN's own Load Game menu for saves.
- **Update software:** check public GitHub releases, download the correct platform package, verify its checksum, then install and restart the service and dashboard together. Projects and saved keys are preserved. Automatic installation applies to native packages; source checkouts are never overwritten.
- **In-game service checks:** newly built AI modules report when Role Weaver is unavailable or paused and announce reconnection. Type `!studio` to check without using AI tokens. A module cannot directly start desktop software.
- **Conversation and companion defaults:** new NPCs allow AI conversations, social chat and companion visits. Companions allow movement, accessible container inspection and item exchanges. Creators retain individual controls; animals retain nonverbal profiles, and native storage and item protections remain active.

For an existing adventure, choose **Companions** or **Behaviors → Apply conversation & storage defaults to this project**, review the changes, save and rebuild. Start a new game to test the new module; saved games retain their older resources. Existing creator opt-outs stay unchanged unless you apply the defaults.

## Your AI provider

**Local settings → Set up your AI** guides users to obtain their own Gemini or OpenAI key, save it locally, and choose separate gameplay and authoring models. Gemini offers a limited free tier for eligible models/accounts; OpenAI API usage is paid. Follow the current pricing and terms linked in the interface. A successful model-access check does not verify generation credit, quota or billing.

Saved keys use Windows DPAPI, macOS Keychain or Linux Secret Service and are excluded from project exports. Environment keys remain supported. Gameplay guardrails and token tracking are available in the dashboard.

## Source development and packaging

The source ZIP is separate from the Python-included application downloads. Use Python 3.12+ (release builds use 3.13). Create a virtual environment and install `requirements-guardrails.txt` and `requirements-platform.txt`. On Linux/Mac, build the native NWScript compiler using `python installer/build_nwnsc.py`; CMake, Bison 3+ and a C++ compiler are needed. Start with `python service.py` or the supplied source launcher.

Run `python -m unittest discover -s tests`; JavaScript checks are in `tests/*_checks.js`. Game-dependent tests need your own NWN installation and are skipped when unavailable. See [packaging instructions](installer/README.md) for native application builds and Windows Setup. `python package.py` creates a clean source ZIP. CI runs the native build matrix and publishes tagged release candidates only after all build jobs pass.

## License

See [ROLE-WEAVER-LICENSE.txt](ROLE-WEAVER-LICENSE.txt). Included third-party components retain their own licenses. Respect NWN and custom-content authors' redistribution terms.
