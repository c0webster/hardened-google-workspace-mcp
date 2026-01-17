# Setup Guide: Hardened Google Workspace MCP for Claude Code

This guide will help you connect Claude Code to your Google Workspace (Gmail, Drive, Docs, etc.).

**Time required:** About 15-20 minutes

---

## Before You Start

Make sure you have:
- [ ] Claude Code installed and working
- [ ] A Google Workspace account (or personal Google account)
- [ ] Access to Google Cloud Console to create OAuth credentials

---

## Step 1: Create Google OAuth Credentials

Follow the instructions in **[OAUTH_SETUP.md](./OAUTH_SETUP.md)** to create your own OAuth credentials.

You'll need:
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`

Keep these values handy for Step 4.

---

## Step 2: Install Python (if you don't have it)

Open **Terminal** (press `Cmd + Space`, type "Terminal", hit Enter).

Check if Python is installed:
```bash
python3 --version
```

If you see a version number (like `Python 3.11.4`), skip to Step 3.

If you get "command not found", install Python:
```bash
# Install Homebrew first (if you don't have it)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Then install Python
brew install python
```

---

## Step 3: Install uv (Python package manager)

In Terminal, run:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then close and reopen Terminal (or run `source ~/.zshrc`).

---

## Step 4: Set Up the Workspace Server

**4a.** Move the `hardened-google-workspace-mcp` folder somewhere permanent.

We recommend putting it in your home folder:
```bash
mv ~/Downloads/hardened-google-workspace-mcp ~/hardened-google-workspace-mcp
```

**4b.** Install the dependencies:
```bash
cd ~/hardened-google-workspace-mcp
uv sync
```

You should see it download and install packages. This takes a minute or two.

---

## Step 5: Configure Claude Code

Choose **one** of these options:

### Option A: Using `claude mcp add` (recommended)

This is the easiest method. Run this command in Terminal:

```bash
claude mcp add hardened-workspace \
  --scope user \
  -e GOOGLE_OAUTH_CLIENT_ID="YOUR_CLIENT_ID" \
  -e GOOGLE_OAUTH_CLIENT_SECRET="YOUR_CLIENT_SECRET" \
  -- uv run --directory ~/hardened-google-workspace-mcp python -m main --single-user
```

Replace `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` with the values from Step 1.

The `--scope user` flag makes this available in all your projects.

> **Note:** If you put the folder somewhere other than `~/hardened-google-workspace-mcp`, replace that path in the command above.

### Option B: Manual config file

**5a.** Create the Claude config folder (if it doesn't exist):
```bash
mkdir -p ~/.claude
```

**5b.** Create the config file:
```bash
open -e ~/.claude/mcp_config.json
```

**5c.** Paste this content (replace `YOUR_USERNAME` with your macOS username - run `whoami` in Terminal to find it):

```json
{
  "mcpServers": {
    "hardened-workspace": {
      "command": "uv",
      "args": ["run", "--directory", "/Users/YOUR_USERNAME/hardened-google-workspace-mcp", "python", "-m", "main", "--single-user"],
      "env": {
        "GOOGLE_OAUTH_CLIENT_ID": "YOUR_CLIENT_ID",
        "GOOGLE_OAUTH_CLIENT_SECRET": "YOUR_CLIENT_SECRET"
      }
    }
  }
}
```

Replace `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` with the values from Step 1.

**5d.** Save and close the file (`Cmd + S`, then `Cmd + W`).

---

## Step 6: Restart Claude Code

Completely quit Claude Code (`Cmd + Q`) and reopen it.

---

## Step 7: Authorize with Google

The first time you use a Google feature, Claude will open your browser.

1. Sign in with your **Google account**
2. Click **"Continue"** on the security warning (it's expected for apps in testing mode)
3. Click **"Allow"** to grant permissions
4. Close the browser tab and return to Claude Code

---

## Step 8: Add Safety Instructions (Recommended)

Add these instructions to your `CLAUDE.md` file so Claude is more careful with your Google data.

**If you don't have a CLAUDE.md yet:**
```bash
cp ~/hardened-google-workspace-mcp/CLAUDE_TEMPLATE.md ~/CLAUDE.md
```

**If you already have a CLAUDE.md**, add these lines to it:
```markdown
## Google Workspace Safety

When using Google Workspace tools (Gmail, Drive, Docs, Calendar, etc.):
- Always tell me exactly what you're about to do before doing it
- For any action that creates, modifies, or deletes data, ask for my confirmation first
- Show me the specific details (recipient, document name, calendar event, etc.)
```

> **Why?** This makes Claude pause and explain before taking actions on your Google account, giving you a chance to catch mistakes.

---

## You're Done!

Try asking Claude:
- "Show me my recent emails"
- "What's on my calendar this week?"
- "Find the document called [something] in my Drive"

---

## Troubleshooting

### "MCP server not found" or similar errors
- Make sure you restarted Claude Code after Step 6
- Check that the path in `mcp_config.json` is correct (no typos!)

### Browser doesn't open for Google login
- Look in Claude Code's output for a URL you can copy/paste manually

### "Permission denied" after previously working
```bash
rm -rf ~/.credentials/workspace-mcp/
```
Then restart Claude Code and re-authorize.

### Need help?
File an issue on the [GitHub repository](https://github.com/c0webster/hardened-google-workspace-mcp/issues).

---

## What Claude Can (and Can't) Do

**Claude CAN:**
- Read your emails and create drafts
- Read and edit Google Docs, Sheets, and Slides
- View and create calendar events
- Search and read files in your Drive

**Claude CANNOT:**
- Send emails (you must open Gmail and click Send yourself)
- Share files with external users
- Delete your files or emails permanently

This is intentional for security. See SECURITY.md for details.
