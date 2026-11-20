# Role Weaver Module Studio

Build single-player Neverwinter Nights: Enhanced Edition adventures with AI-assisted story design, floorplan interpretation, populated areas, quests, merchants and companions. Play locally with optional AI conversations and export standard modules for Aurora editing.

## Get started

Download the current [release](https://github.com/RoleWeaverInfo/RWSoloSuite/releases). Application packages include Python: Windows x64 installer, Linux x64/ARM64 archives, and macOS Intel/Apple Silicon apps. See the release notes for supported OS versions and candidate limitations. Repository access is required while this repository is private.

- [Installation, API keys and updates](docs/INSTALLATION.md)
- [Talk to AI NPCs and use companions](docs/PLAYER-GUIDE.md)
- [Create an adventure with ChatGPT and Studio](docs/CREATE-AN-ADVENTURE.md)
- [Release notes](docs/RELEASE-0.21.0.md)
- [Guardrails and token usage](GUARDRAILS-AND-USAGE.md)

Start Role Weaver before opening NWN. The service opens a local dashboard at `http://127.0.0.1:8766`; it does not start the game. Install and register the adventure's matching `.mod` and `.rwproject.json`, then launch NWN yourself. Closing the browser leaves the service running; use **AI service → Stop Role Weaver** when finished.

You need your own NWN:EE installation for its game resources. Aurora editing requires Windows; generated modules can be transferred from Linux/Mac. No game assets, personal workspaces or API keys are distributed with Studio.

## Your AI provider

**Local settings → Set up your AI** guides users to obtain their own Gemini or OpenAI key, save it locally, and choose separate gameplay and authoring models. Gemini offers a limited free tier for eligible models/accounts; OpenAI API usage is paid. Follow the current pricing and terms linked in the interface. A successful model-access check does not verify generation credit, quota or billing.

Saved keys use Windows DPAPI, macOS Keychain or Linux Secret Service and are excluded from project exports. Environment keys remain supported. Gameplay guardrails and token tracking are available in the dashboard.

## Source development and packaging

The source ZIP is separate from the Python-included application downloads. Use Python 3.10+ (release builds use 3.13). Create a virtual environment and install `requirements-guardrails.txt` and `requirements-platform.txt`. On Linux/Mac, build the native NWScript compiler using `python installer/build_nwnsc.py`; CMake, Bison 3+ and a C++ compiler are needed. Start with `python service.py` or the supplied source launcher.

Run `python -m unittest discover -s tests`; JavaScript checks are in `tests/*_checks.js`. Game-dependent tests need your own NWN installation and are skipped when unavailable. See [packaging instructions](installer/README.md) for native application builds and Windows Setup. `python package.py` creates a clean source ZIP. CI runs the native build matrix and publishes tagged release candidates only after all build jobs pass.

## License

See [ROLE-WEAVER-LICENSE.txt](ROLE-WEAVER-LICENSE.txt). Included third-party components retain their own licenses. Respect NWN and custom-content authors' redistribution terms.
