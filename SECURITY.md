# Hardened Google Workspace MCP - Security Documentation

This is a **security-hardened fork** of the google_workspace_mcp server, designed for use with Claude Code.

## ⚠️ Important Security Notice

**This server reduces but does NOT eliminate data exfiltration risk.**

While we've removed dangerous Google Workspace operations, Claude Code has access to many other tools that could be used for data exfiltration:
- **Web requests** - Claude can make HTTP requests to external servers
- **File operations** - Claude can write files that may sync to cloud storage (Dropbox, iCloud, etc.)
- **Other MCP servers** - Other installed MCP tools may have exfiltration capabilities
- **Code execution** - Claude can write and execute code that calls external APIs

**You must remain vigilant:**
- Always review Claude's tool calls before approving them
- Never run Claude Code with `--dangerously-skip-permissions`
- Be suspicious of unexpected file writes, web requests, or code execution
- Treat all content from external sources as potentially malicious (prompt injection risk)

This hardening **only** secures the Google Workspace integration. Your overall security depends on the full set of tools Claude has access to.

## Security Model

This server is designed with the assumption that **prompt injection attacks are possible**. An attacker could potentially inject malicious instructions into documents, emails, or other content that Claude processes. To mitigate data exfiltration risks, we have removed all tools that could be used to send data outside your account.

### Blocked Operations

The following tools have been **removed** from this fork:

#### Gmail - Blocked
| Tool | Reason |
|------|--------|
| `send_gmail_message` | Primary exfiltration vector - could send sensitive data to external addresses |
| `create_gmail_filter` | Could create auto-forwarding rules to exfiltrate incoming emails |
| `delete_gmail_filter` | Could remove security monitoring filters |

#### Google Drive - Blocked
| Tool | Reason |
|------|--------|
| `share_drive_file` | Could share sensitive files with external users |
| `batch_share_drive_file` | Same risk as above, at scale |
| `update_drive_permission` | Could escalate permissions or expose files externally |
| `remove_drive_permission` | Could remove security restrictions |
| `transfer_drive_ownership` | Could transfer ownership of sensitive files outside org |

#### Services - Removed Entirely
| Service | Reason |
|---------|--------|
| Google Chat | Not needed, reduces attack surface |
| Google Tasks | Not needed, reduces attack surface |
| Google Search | Not needed, reduces attack surface |

### Allowed Operations

#### Gmail - Allowed
- `list_gmail_messages` - Search/list emails
- `get_gmail_message` - Read specific email
- `list_gmail_drafts` - List drafts
- `get_gmail_draft` - Read draft content
- `draft_gmail_message` - Create new draft (**user must manually send**)
- `update_gmail_draft` - Edit existing draft
- `delete_gmail_draft` - Delete draft
- `list_gmail_labels` - List labels
- `list_gmail_filters` - Read-only view of existing filters

#### Google Drive - Allowed
- `search_drive_files` - Search/list files
- `list_drive_items` - List folder contents
- `get_drive_file_content` - Read file content
- `get_drive_file_download_url` - Get download URL
- `create_drive_file` - Create new file
- `update_drive_file` - Update file metadata
- `get_drive_file_permissions` - Read-only view of permissions
- `get_drive_shareable_link` - Get shareable link (read-only)
- `check_drive_file_public_access` - Check if file is public

#### Google Docs - Allowed (all operations)
- Read and edit documents

#### Google Sheets - Allowed (all operations)
- Read and write spreadsheet data

#### Google Calendar - Allowed (limited)
- List, read, create, update, delete calendar events
- **Cannot add attendees** - Event attendees trigger automatic email invitations from Google, creating an exfiltration vector. Users must add attendees manually in Calendar UI.

#### Google Forms - Allowed (all operations)
- Read form structure and responses
- Create and edit forms

#### Google Slides - Allowed (all operations)
- Read and edit presentations

## Remaining Risks

While this fork removes the most obvious exfiltration vectors, **data leakage is still possible** through the following mechanisms:

### 1. Creating Documents in Shared Folders
If Claude creates a document in a folder that is already shared with an external party (including an attacker), that party will immediately gain access to the new document. The server cannot prevent this because:
- Claude can create documents in any folder the user has access to
- The server has no visibility into which folders are shared externally
- Google Drive's permission model automatically grants folder permissions to new files

**Mitigation**: Users should carefully review any prompts that involve creating documents, especially if the destination folder is not explicitly verified.

### 2. Editing Attacker-Controlled Documents
If an attacker shares a Google Doc with the user (or tricks the user into opening one), Claude could write sensitive information directly into that document, which the attacker can immediately see. This attack vector cannot be blocked because:
- The server cannot distinguish between "user's own document" and "shared document from attacker"
- Normal legitimate use cases involve editing shared documents
- Revoking write access to all shared documents would break core functionality

**Mitigation**: Users should be suspicious if Claude attempts to edit documents they don't recognize, especially if those documents were recently shared with them from external sources.

### 3. Jailbroken Claude with Direct API Access
If Claude is successfully jailbroken through prompt injection, it could potentially write Python/JavaScript code that directly calls the Google Workspace APIs using the user's authenticated credentials. While the MCP server restricts which *tools* are available, Claude still has:
- The ability to write and potentially execute code (via other tools or mechanisms)
- Access to the same OAuth credentials the MCP server uses
- Knowledge of the Google Workspace API structure

**Mitigation**: This is the hardest risk to mitigate and relies on:
- Claude Code's permission system (never run with `--dangerously-skip-permissions`)
- Claude's base model training to resist jailbreaks
- User vigilance when reviewing tool calls that involve code execution
- Limiting Claude Code's access to code execution tools in high-risk contexts

### Defense-in-Depth Recommendations

Given these residual risks:

1. **Enable permission prompts** - Never disable Claude Code's permission system
2. **Review ALL tool usage, not just Google Workspace** - Watch for web requests, file writes, code execution, and other MCP tools
3. **Review document operations carefully** - Pay special attention when Claude creates or edits documents, especially in shared locations
4. **Audit shared folders** - Periodically review which folders have external sharing enabled
5. **Monitor recent activity** - Check Google Drive's "Recent" view and Gmail's "Sent" folder after Claude sessions
6. **Limit Claude's tool access** - Consider disabling other MCP servers or tools when working with sensitive data
7. **Use dedicated accounts for sensitive work** - Consider using separate Google accounts for highly sensitive data that Claude shouldn't access
8. **Treat all external content as untrusted** - Documents, emails, or websites from external sources could contain prompt injections
9. **Review Claude Code's logs** - Periodically check what tools Claude has been using and what data it accessed

## OAuth Scopes

This server requests only the minimum scopes needed:

```
openid
https://www.googleapis.com/auth/userinfo.email
https://www.googleapis.com/auth/userinfo.profile
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.compose      # For drafts only, NOT sending
https://www.googleapis.com/auth/gmail.modify
https://www.googleapis.com/auth/gmail.labels
https://www.googleapis.com/auth/drive
https://www.googleapis.com/auth/drive.readonly
https://www.googleapis.com/auth/drive.file
https://www.googleapis.com/auth/documents.readonly
https://www.googleapis.com/auth/documents
https://www.googleapis.com/auth/spreadsheets.readonly
https://www.googleapis.com/auth/spreadsheets
https://www.googleapis.com/auth/calendar
https://www.googleapis.com/auth/calendar.readonly
https://www.googleapis.com/auth/calendar.events
```

**Notably absent:**
- `gmail.send` - Cannot send emails
- `gmail.settings.basic` - Cannot modify Gmail settings/filters

## Token Storage (Stateless Mode)

This server runs in **stateless mode** by default (`WORKSPACE_MCP_STATELESS_MODE=true`). This means:

- OAuth tokens are stored **in memory only**, not written to disk
- No credential files are created in `~/.google_workspace_mcp/credentials/`
- Users must re-authenticate when Claude Desktop restarts

**Why this matters:** Without stateless mode, a refresh token would be stored in a plaintext JSON file. An attacker who compromises a user's machine could copy this file and use it from any other machine to access that user's Google Workspace data. Stateless mode eliminates this attack vector.

**Trade-off:** Users authenticate more frequently (on each Claude Desktop restart), but no persistent credential file exists to steal.

## Kill Switch

If you suspect a security incident, you can immediately revoke all access:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services > Credentials
3. Find the OAuth 2.0 Client ID for this integration
4. Click "Disable" or "Delete"

This will immediately invalidate all tokens and prevent any further access.

## User Security Guidelines

1. **Keep permission prompts ON** - Never run Claude Code with `--dangerously-skip-permissions`
2. **Review ALL tool calls, not just Google Workspace** - Watch for:
   - Unexpected web requests (WebFetch, curl, HTTP libraries)
   - File write operations that could sync to cloud storage
   - Code execution (especially Python/JavaScript that makes network calls)
   - Use of other MCP servers you have installed
3. **Be suspicious of unexpected requests** - If Claude suddenly wants to read many files, create drafts, or make web requests, review the context carefully
4. **Watch Claude's behavior with external content** - Be extra vigilant when Claude processes:
   - Emails from external senders
   - Documents shared by people outside your organization
   - Web pages or content from untrusted sources
5. **Report strange behavior** - If Claude acts unexpectedly, investigate immediately
6. **Don't paste untrusted content** - Content from external sources could contain prompt injections
7. **Review your other MCP servers** - Audit what other tools Claude has access to beyond Google Workspace

## Reporting Security Issues

For security issues with this project, please [file an issue](https://github.com/c0webster/hardened-google-workspace-mcp/issues) on GitHub.

For issues with the upstream google_workspace_mcp project, see the [upstream repository](https://github.com/taylorwilsdon/google_workspace_mcp).
