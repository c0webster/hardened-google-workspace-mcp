# Hardened Google Workspace MCP

A **security-hardened** Google Workspace integration for Claude Code.

> This is a fork of [taylorwilsdon/google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp) with dangerous operations removed to prevent data exfiltration via prompt injection attacks. See [SECURITY.md](./SECURITY.md) for details.

## What This Does

Enables Claude Code to interact with your Google Workspace:
- **Gmail**: Read emails, create drafts (cannot send)
- **Google Drive**: Read/create files (cannot share externally)
- **Google Docs**: Read and edit documents
- **Google Sheets**: Read and write spreadsheets
- **Google Calendar**: View and create events
- **Google Forms**: Read and create forms
- **Google Slides**: Read and edit presentations

## Why "Hardened"?

LLMs are vulnerable to prompt injection attacks—malicious instructions hidden in content the model processes. An attacker could embed instructions in an email or document that trick the AI into exfiltrating sensitive data.

This fork removes all tools that could send data outside your account:
- **No email sending** - Claude can draft emails, but you must manually send them from Gmail
- **No file sharing** - Claude cannot share files with external users
- **No filter creation** - Claude cannot create auto-forwarding rules

See [SECURITY.md](./SECURITY.md) for the complete security model.

## Prerequisites

- Claude Code installed on your machine
- A Google Workspace or personal Google account
- Python 3.11+ installed

## Quick Start

### Step 1: Create OAuth Credentials

Follow **[OAUTH_SETUP.md](./OAUTH_SETUP.md)** to create Google Cloud OAuth credentials.

### Step 2: Install Dependencies

```bash
cd ~/hardened-google-workspace-mcp  # or wherever you placed it
uv sync
```

> **Note:** If you don't have `uv` installed, run: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Step 3: Configure Claude Code

Add the MCP server using `claude mcp add`:

```bash
claude mcp add hardened-workspace \
  --scope user \
  -e GOOGLE_OAUTH_CLIENT_ID="YOUR_CLIENT_ID" \
  -e GOOGLE_OAUTH_CLIENT_SECRET="YOUR_CLIENT_SECRET" \
  -- uv run --directory ~/hardened-google-workspace-mcp python -m main --single-user
```

Replace `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` with your OAuth credentials.

**Or manually** add to `~/.claude/mcp_config.json`:

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

### Step 4: Authorize with Google

1. Start (or restart) Claude Code
2. The first time you use a Google Workspace tool, a browser window will open
3. Sign in with your Google account
4. Click "Allow" to grant permissions

For detailed instructions, see **[SETUP.md](./SETUP.md)**.

## Example Prompts

Once set up, try these prompts in Claude Code:

```
List my recent emails from the past week

Read the document "Q4 Planning" from my Google Drive

Create a draft email to john@example.com about the meeting tomorrow

Show me what's on my calendar for next Monday

Update cell A1 in my "Budget 2025" spreadsheet to "Updated"
```

## Troubleshooting

### "OAuth credentials not found"
Make sure you've set the `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` environment variables in your MCP config.

### "Permission denied" errors
1. Delete the credentials folder: `rm -rf ~/.credentials/workspace-mcp/`
2. Restart Claude Code
3. Re-authorize with your Google account

### "Tool not found" errors
Make sure the MCP server is running. Check Claude Code's MCP status panel.

### Browser doesn't open for authorization
If the browser doesn't open automatically, check the Claude Code output for a URL to copy/paste manually.

## Security Notes

- **Never disable permission prompts** - Always review what Claude is asking to do
- **Drafts require manual sending** - Claude can create email drafts, but you must open Gmail to send them
- **No external sharing** - Claude cannot share files outside your organization
- **Report issues** - If Claude behaves unexpectedly, file an issue

See [SECURITY.md](./SECURITY.md) for comprehensive security documentation.

## Support

For issues with this project, please [file an issue](https://github.com/YOUR_ORG/hardened-google-workspace-mcp/issues) on GitHub.

---

*Based on [google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp) by Taylor Wilsdon, licensed under MIT.*
