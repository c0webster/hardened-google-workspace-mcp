# Adding `read_sheet_hyperlinks` to Google Workspace MCP

## Problem

The existing `read_sheet_values` tool uses the Google Sheets `spreadsheets.values.get()` API, which only returns plain cell text. If a cell has an embedded hyperlink (e.g., a grant name that links to a Google Doc), the URL is lost — you only get the display text.

This matters when spreadsheets are used as indexes (e.g., a grant pipeline where Column C links grant names to their investigation or approval documents).

## Solution

A new `read_sheet_hyperlinks` tool that uses `spreadsheets.get()` with `includeGridData=True` and a targeted fields mask to extract the `hyperlink` property from each cell.

## How it works

The Google Sheets API stores hyperlinks as cell metadata, separate from the cell value. The `spreadsheets.values` endpoint doesn't expose this metadata, but `spreadsheets.get` does when you request grid data.

**API call:**
```python
service.spreadsheets().get(
    spreadsheetId=spreadsheet_id,
    ranges=[range_name],
    includeGridData=True,
    fields="sheets(properties(title),data(startRow,startColumn,rowData(values(formattedValue,hyperlink))))"
).execute()
```

**Key fields:**
- `formattedValue`: The display text of the cell (e.g., "FCAP vs. cash transfer RCT")
- `hyperlink`: The URL embedded in the cell (e.g., `https://docs.google.com/document/d/...`)

The `hyperlink` field is only populated when a cell has a single hyperlink. For cells with multiple hyperlinks within the text, you'd need to parse `textFormatRuns`, but single-link cells cover the vast majority of use cases.

## Files changed

### `gsheets/sheets_helpers.py`

Added `_extract_hyperlinks_from_grid()` — parses the grid data response into a list of `{"cell": "Sheet1!A3", "text": "...", "url": "..."}` dicts. Follows the same pattern as `_extract_cell_errors_from_grid`.

### `gsheets/sheets_tools.py`

Added `read_sheet_hyperlinks()` tool function with the same decorator stack and parameter signature as `read_sheet_values`:

```python
@server.tool()
@handle_http_errors("read_sheet_hyperlinks", is_read_only=True, service_type="sheets")
@require_google_service("sheets", "sheets_read")
async def read_sheet_hyperlinks(
    service,
    user_google_email: str,
    spreadsheet_id: str,
    range_name: str = "A1:Z1000",
) -> str:
```

### `gsheets/__init__.py`

Added to imports and `__all__`.

### `core/tool_tiers.yaml`

Added to `sheets: core:` tier (same as `read_sheet_values`).

## Output format

```
Found 5 hyperlinks in range 'Grants!A13:C22' for user@example.com:
Grants!C13: "FCAP vs. cash transfer RCT" -> https://docs.google.com/document/d/1P_SlFJe0D04BXwiViIMVZz4KWSOMnZWo-zX3Zpi5TVM/edit?tab=t.0
Grants!C14: "Scoping grant for an impact evaluation of FIka" -> https://docs.google.com/document/d/1fXezezjY9ky31uAjyXOEDBQHvDin7iE54Nw0UuW7QNA/edit?tab=t.jt812henn1n9
...
```

## How to apply this to your MCP server

If you're running your own instance of the Google Workspace MCP server (either taylorwilsdon/google_workspace_mcp or c0webster/hardened-google-workspace-mcp):

1. Copy the `_extract_hyperlinks_from_grid` function into your `gsheets/sheets_helpers.py`
2. Copy the `read_sheet_hyperlinks` function into your `gsheets/sheets_tools.py` (right after `read_sheet_values`)
3. Add the import and export in `gsheets/__init__.py`
4. If your server uses tool tiers, add `read_sheet_hyperlinks` to the appropriate tier
5. Restart the MCP server

No new dependencies or API scopes are required — it uses the same `sheets_read` scope as `read_sheet_values`.
