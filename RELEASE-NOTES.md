# 0.21.0-rc1 — native desktop packages and getting-started guides

See [this release's notes](docs/RELEASE-0.21.0.md) and [installation instructions](docs/INSTALLATION.md). Added Windows/Linux/macOS release automation, Linux and macOS builds for x64 and ARM64, platform-specific workspaces/compiler discovery/secure key stores, confirmed service shutdown, cross-platform adventure launchers, guided provider setup, and player/ChatGPT authoring guides.

# 0.20.0-rc2 — Windows installer

- Windows Setup includes an isolated 64-bit Python runtime. End users do not need to install Python, pip or development tools.
- A Start-menu entry and optional desktop shortcut start the service through `Role Weaver Module Studio.exe`. NWN remains a separate, manual launch.
- The installer runs for the current user. Projects, builds, downloaded asset caches, settings and encrypted keys live in `%LOCALAPPDATA%\RoleWeaver\ModuleStudio`, outside the installed program. Upgrades and uninstall leave that workspace intact.
- Shared-adventure launchers detect the installed Studio through its per-user registration. The source ZIP remains available for developers using their own Python.
- Setup checks the service mutex before upgrades or uninstall, rather than terminating a running service. Runtime versions and download hashes are pinned in `installer/runtime-lock.json`; build instructions are in `installer/README.md`.
- This is an unsigned release candidate. Code signing and distribution are separate release steps.

## 0.20.0-rc1 — release preparation

- Blue dashboard theme, readable focus states and responsive branding using the supplied Role Weaver Module Studio artwork.
- Browser startup splash with service readiness, a four-second transition and an option to stay on the splash.
- One service-only entry point: **Start Role Weaver.cmd**. It enables the local AI bridge without starting NWN. Existing Studio shortcuts forward to this entry point.
- Newly exported adventures include a service launcher that installs their module/HAKs and registers the matching AI profile. Start NWN separately afterward. Existing saves and prior export archives are not rewritten.
- The area testing button installs a standalone test module without opening NWN.
- Clean release packaging with a SHA-256 checksum, explicit source allowlist, no personal examples/workspaces, and checks against known OpenAI/Gemini credentials.
- Python 3.10+ remains a prerequisite. This candidate is a Windows ZIP, not a self-contained executable or installer. It has not been published to GitHub.

Includes the existing area authoring, visual catalog, native room groups, measured walls/scale/placement, platforms/stairs, carpets, connected doorways, and material/lighting presets. The preset button's review-state fix is included.
