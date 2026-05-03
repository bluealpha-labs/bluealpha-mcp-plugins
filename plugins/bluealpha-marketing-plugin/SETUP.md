# Setup

Two pieces to install: the **BlueAlpha MCP** connector (so Claude can read your Google Ads data) and the **BlueAlpha Marketing Plugin** (the ten skills that use it). Total time: about a minute.

## Step 1 — Install the BlueAlpha MCP connector

1. Open **Settings** in the Claude desktop app
2. Go to **Connectors → Add custom connector**
3. Name: `BlueAlpha MCP`
4. URL: `https://consumer.mcp.bluealpha.ai/mcp`
5. Click **Connect** and sign in with your BlueAlpha account

That single sign-in wires Claude up to your Google Ads accounts (and your Meridian MMM, if you have one). No keys, no IDs, no config to copy.

Don't have a BlueAlpha account yet? Visit [bluealpha.ai](https://bluealpha.ai) to get one.

## Step 2 — Install the BlueAlpha Marketing Plugin

Pick one path.

**From the marketplace (recommended):** in Claude, type:

```
/plugin marketplace add bluealpha-labs/bluealpha-plugins
/plugin install bluealpha-marketing-plugin
```

**From a direct download:** grab the `.plugin` file from the [latest release](https://github.com/bluealpha-labs/bluealpha-plugins/releases/latest) and drag it into Claude. Click **Install** when prompted.

## Step 3 — Try it

Ask Claude something like:

> *"Audit my Google Ads account and tell me what to fix first."*

Claude routes that to the right skill, pulls your live data, and walks you through what it finds. From there, just keep talking.

That's the whole setup.

---

**Need help?** Email support@bluealpha.ai or message your BlueAlpha account manager.
