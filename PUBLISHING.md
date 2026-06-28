# How to Publish This Marketplace

This file is for you (the maintainer), not for end users. It explains how to take the contents of this folder live so the public can install your plugin.

## One-time setup

1. Create a public GitHub repo named `bluealpha-plugins` under your BlueAlpha org.
2. From this folder, run:
   ```
   git init
   git add .
   git commit -m "Initial public marketplace with bluealpha-marketing-plugin"
   git branch -M main
   git remote add origin https://github.com/bluealpha-labs/bluealpha-mcp-plugins.git
   git push -u origin main
   ```
3. (Optional but recommended) On GitHub, go to **Releases → Draft a new release**, attach the `bluealpha-marketing-plugin.plugin` file (in your Cowork outputs folder), and tag it `v0.2.0`. This gives you a permanent download URL for tutorials.

## What your tutorial viewers will do

**Path A — marketplace install (recommended):**
```
/plugin marketplace add https://github.com/bluealpha-labs/bluealpha-mcp-plugins.git
/plugin install bluealpha-marketing-plugin
```

**Path B — direct file install (lowest friction):**
1. Click your tutorial's download link → grabs the `.plugin` file
2. Drag the file into Claude
3. Click Install

Either way, the first skill they trigger will prompt them to authenticate `bluealpha-mcp`. Once they sign in, everything's wired up.

## Shipping updates

1. Edit the plugin files in `plugins/bluealpha-marketing-plugin/`
2. Bump `version` in both `plugins/bluealpha-marketing-plugin/.claude-plugin/plugin.json` AND in `.claude-plugin/marketplace.json` (the matching entry)
3. Re-zip the plugin folder as a new `.plugin` file for direct download
4. Commit and push — marketplace users will get the update prompt automatically; direct-download users will need to re-download from your release page

## What's in this folder

- `.claude-plugin/marketplace.json` — the manifest Claude reads when someone runs `/plugin marketplace add`
- `plugins/bluealpha-marketing-plugin/` — the actual plugin source
- `README.md` — public-facing landing page on GitHub
- `PUBLISHING.md` — this file (don't worry, GitHub renders it but it's clearly internal)
