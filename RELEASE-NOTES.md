# 0.20.0-rc1 — release preparation

- Blue dashboard theme, readable focus states and responsive branding using the supplied Role Weaver Module Studio artwork.
- Browser startup splash with service readiness, a four-second transition and an option to stay on the splash.
- One service-only entry point: **Start Role Weaver.cmd**. It enables the local AI bridge without starting NWN. Existing Studio shortcuts forward to this entry point.
- Newly exported adventures include a service launcher that installs their module/HAKs and registers the matching AI profile. Start NWN separately afterward. Existing saves and prior export archives are not rewritten.
- The area testing button installs a standalone test module without opening NWN.
- Clean release packaging with a SHA-256 checksum, explicit source allowlist, no personal examples/workspaces, and checks against known OpenAI/Gemini credentials.
- Python 3.10+ remains a prerequisite. This candidate is a Windows ZIP, not a self-contained executable or installer. It has not been published to GitHub.

Includes the existing area authoring, visual catalog, native room groups, measured walls/scale/placement, platforms/stairs, carpets, connected doorways, and material/lighting presets. The preset button's review-state fix is included.
