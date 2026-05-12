# Setup

Two pieces to install: the **BlueAlpha MCP** connector (so Claude can read your Google Ads data and your Meridian MMM) and the **BlueAlpha Marketing Plugin** (the twenty skills that use it). Total time: about a minute.

## Step 1 — Install the BlueAlpha MCP connector

1. Open **Settings** in the Claude desktop app
2. Go to **Connectors → Add custom connector**
3. Name it: `BlueAlpha MCP`
4. URL: `https://mcp.bluealpha.ai/mcp`
5. Click **Connect** and sign in with your BlueAlpha account

That single sign-in wires Claude up to your Meridian models (and your Google Ads accounts, if you have them). No keys, no IDs, no config files.

Don't have a BlueAlpha account yet? Visit [bluealpha.ai](https://bluealpha.ai) to get one.

## Step 2 — Install the plugin

Pick the path that matches the Claude product you're using.

### Option A — Cowork (drag-and-drop)

1. Go to [github.com/bluealpha-labs/bluealpha-plugins](https://github.com/bluealpha-labs/bluealpha-plugins)
2. Click **Releases** on the right rail and open the latest release (currently v0.3.0)
3. Expand **Assets** and click `bluealpha-marketing-plugin.plugin` to download
4. Drag the downloaded file into an open Cowork session and click **Install** when prompted

That's it. No CLI, no settings menu — one drag.

### Option B — Claude Code (slash commands)

Inside Claude Code, run these two commands:

```
/plugin marketplace add https://github.com/bluealpha-labs/bluealpha-plugins.git
/plugin install bluealpha-marketing-plugin
```

The first registers the GitHub repo as a marketplace; the second installs the plugin from it. The same plugin contains both the Google Ads skills and the MMM skills — you install once, the right skill triggers based on what you ask.

## Step 3 — Try it

Ask Claude something like:

> *"Audit my Google Ads account and tell me what to fix first."*

…or, if you have an MMM connected:

> *"Which of my channels are saturated and which still have headroom?"*

Claude routes that to the right skill, pulls your live data, and walks you through what it finds. From there, just keep talking.

That's the whole setup.

---

**Need help?** Email support@bluealpha.ai or message your BlueAlpha account manager.
