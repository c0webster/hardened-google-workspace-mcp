# Creating Google OAuth Credentials

This guide walks you through creating OAuth 2.0 credentials in Google Cloud Console. You'll need these credentials to authenticate the Secure Workspace MCP server with your Google account.

**Time required:** 10-15 minutes

---

## Step 1: Create or Select a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Click the project dropdown at the top of the page
4. Either:
   - Select an existing project, OR
   - Click **"New Project"**, give it a name (e.g., "Claude Workspace MCP"), and click **Create**

---

## Step 2: Enable Required APIs

1. Go to **APIs & Services > Library** (or use [this link](https://console.cloud.google.com/apis/library))
2. Search for and enable each of these APIs:

| API Name | Search Term |
|----------|-------------|
| Gmail API | `gmail` |
| Google Drive API | `drive` |
| Google Docs API | `docs` |
| Google Sheets API | `sheets` |
| Google Calendar API | `calendar` |
| Google Forms API | `forms` |
| Google Slides API | `slides` |

For each API:
1. Click on it in the search results
2. Click **Enable**
3. Wait for it to enable, then go back to the Library

> **Tip:** You only need to enable APIs for services you plan to use. Gmail, Drive, and Calendar are the most common.

---

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen** (or use [this link](https://console.cloud.google.com/apis/credentials/consent))
2. Select **User Type**:
   - Choose **Internal** if you have Google Workspace and want to limit to your organization
   - Choose **External** if using a personal Google account or want broader access
3. Click **Create**

### Fill in the consent screen details:

**App Information:**
- **App name:** `Claude Workspace Integration` (or any name you prefer)
- **User support email:** Your email address
- **App logo:** (optional, skip)

**App domain:** (optional, skip all)

**Developer contact information:**
- **Email addresses:** Your email address

4. Click **Save and Continue**

### Scopes:

1. Click **Add or Remove Scopes**
2. In the filter box, paste each scope below and check it:

```
openid
https://www.googleapis.com/auth/userinfo.email
https://www.googleapis.com/auth/userinfo.profile
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.compose
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
https://www.googleapis.com/auth/forms.body
https://www.googleapis.com/auth/forms.body.readonly
https://www.googleapis.com/auth/forms.responses.readonly
https://www.googleapis.com/auth/presentations
https://www.googleapis.com/auth/presentations.readonly
```

3. Click **Update** at the bottom
4. Click **Save and Continue**

### Test Users (External only):

If you chose "External" user type:
1. Click **Add Users**
2. Add your email address
3. Click **Save and Continue**

> **Note:** While your app is in "Testing" status, only test users you add can authorize it.

4. Click **Back to Dashboard**

---

## Step 4: Create OAuth Credentials

1. Go to **APIs & Services > Credentials** (or use [this link](https://console.cloud.google.com/apis/credentials))
2. Click **Create Credentials** at the top
3. Select **OAuth client ID**

### Configure the OAuth client:

- **Application type:** `Desktop app`
- **Name:** `Claude Code MCP` (or any name you prefer)

4. Click **Create**

### Copy Your Credentials

A dialog will appear with your credentials:

- **Client ID:** Looks like `123456789-abcdefg.apps.googleusercontent.com`
- **Client Secret:** Looks like `GOCSPX-xxxxxxxxx`

**Important:** Copy both values and store them securely. You'll need them when configuring Claude Code.

You can also click **Download JSON** to save a backup.

---

## Step 5: Use Your Credentials

Now that you have your credentials, go back to **[SETUP.md](./SETUP.md)** and continue from Step 2.

When you reach the configuration step, use:
- `GOOGLE_OAUTH_CLIENT_ID` = your Client ID
- `GOOGLE_OAUTH_CLIENT_SECRET` = your Client Secret

---

## Troubleshooting

### "Access blocked: This app's request is invalid"

This usually means the OAuth consent screen isn't fully configured. Make sure you:
1. Completed the OAuth consent screen setup
2. Added the required scopes
3. If using "External" type, added yourself as a test user

### "This app isn't verified"

This warning is expected for apps in testing mode. Click **Continue** to proceed. Google only verifies apps that are published for public use.

### "Access blocked: Authorization Error"

Check that:
1. You enabled all the required APIs (Step 2)
2. The OAuth client type is "Desktop app"
3. You're signing in with an account that has access (test user for External apps)

### Need to start over?

You can delete the OAuth client and create a new one. Go to **Credentials**, find your OAuth client, click the trash icon, and start Step 4 again.

---

## Security Notes

- **Keep your Client Secret confidential.** Never commit it to public repositories or share it publicly.
- **Rotate credentials** if you suspect they've been exposed. Delete the old OAuth client and create a new one.
- **Review authorized apps** periodically at [myaccount.google.com/permissions](https://myaccount.google.com/permissions)
