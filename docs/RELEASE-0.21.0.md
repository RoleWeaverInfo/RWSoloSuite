# Role Weaver Module Studio 0.21.0-rc1

The first native Linux and macOS release candidate joins the Windows installer. All five application downloads include Python, Guardrails AI validators and an NWScript compiler:

- Windows x64 installer: `Setup-x64.exe` (Windows 10/11).
- Linux x64 and ARM64 portable applications: `Linux-x64.tar.gz` / `Linux-arm64.tar.gz` (Ubuntu 24.04 baseline).
- macOS Intel and Apple Silicon applications: `macOS-x64.zip` / `macOS-arm64.zip` (macOS 15 baseline).

The `source.zip` is for developers and **does** require Python/dependencies. SHA-256 files accompany the downloads. No game files, personal projects or API keys are bundled.

New guides cover installation, AI-NPC conversations, companions, inventory/trading, and creating an adventure from ChatGPT story drafts and labeled floorplans. See the `docs` folder in the distribution or repository.

Guided Gemini/OpenAI setup links to official key pages, securely saves each user's own key, offers separate gameplay/authoring model choices, and can check model metadata access. Gemini offers eligible models on a limited free tier; OpenAI API usage is paid. Metadata checks do not guarantee available generation credit or quota.

Platform ports include native Steam/path detection, per-user workspaces, macOS Keychain/Linux Secret Service support, and a confirmed Stop Role Weaver control on the AI service dashboard. Existing Windows workspaces and key protection are preserved.

These are unsigned Windows / ad-hoc-signed, non-notarized Mac release candidates. Packaged runtime, compiler, dashboard and offline guardrails are checked on native build runners. Gameplay on every operating system has not been manually certified. Own NWN:EE assets are required for module generation; Aurora remains a Windows editor. Studio on Linux ARM64 does not make NWN itself a native ARM64 game.

Stop Role Weaver before updating. Projects live outside the application and are preserved. Start the service before NWN; these packages do not launch the game.
