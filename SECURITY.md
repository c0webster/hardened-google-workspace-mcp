# Hardened Google Workspace MCP - Security Documentation

This is a **security-hardened fork** of the google_workspace_mcp server, designed for use with Claude Code.

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

#### Google Calendar - Allowed (all operations)
- List, read, create, update, delete calendar events

#### Google Forms - Allowed (all operations)
- Read form structure and responses
- Create and edit forms

#### Google Slides - Allowed (all operations)
- Read and edit presentations

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
2. **Review tool calls** - Pay attention when Claude asks to use Google Workspace tools
3. **Be suspicious of unexpected requests** - If Claude suddenly wants to read many files or create drafts, review the context
4. **Report strange behavior** - If Claude acts unexpectedly, investigate immediately
5. **Don't paste untrusted content** - Content from external sources could contain prompt injections

## Reporting Security Issues

For security issues with this project, please [file an issue](https://github.com/c0webster/hardened-google-workspace-mcp/issues) on GitHub.

For issues with the upstream google_workspace_mcp project, see the [upstream repository](https://github.com/taylorwilsdon/google_workspace_mcp).
