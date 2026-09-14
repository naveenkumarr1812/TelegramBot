# Anime World

Anime World is a Telegram + Supabase + Streamlit system for distributing links to content you are authorized to distribute.

## Architecture

- **Telegram bot:** Aiogram 3.x
- **Admin panel:** Streamlit
- **Database:** Supabase / PostgreSQL
- **File hosting:** Google Drive
- **Local file storage:** None
- **Docker:** Not required
- **Redis:** Not required

The bot does not download or store anime files. It checks Telegram channel membership and, when verification succeeds, presents the Google Drive URL stored for the resource.

## Project structure

```text
AnimeWorld/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── admin/
│   ├── app.py
│   ├── database.py
│   ├── .streamlit/
│   │   └── secrets.toml.example
│   └── pages/
│       ├── 2_Resources.py
│       └── 3_Channels.py
└── bot/
    ├── config.py
    ├── database.py
    ├── get_chat_id.py
    ├── keyboards.py
    ├── main.py
    ├── services.py
    ├── test_database.py
    ├── users.py
    └── verification.py
```

## 1. Install

Windows PowerShell:

```powershell
cd "D:\Code Playground\AnimeWorld"
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If PowerShell blocks `Activate.ps1`, activation is not required. The commands below can use `.venv\Scripts\python.exe` directly.

## 2. Configure environment

Copy `.env.example` to `.env` and fill in:

```env
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=YOUR_SUPABASE_KEY
BOT_USERNAME=YourBotUsername
```

`BOT_USERNAME` should be the bot username without `@`.

For Streamlit, copy:

```text
admin/.streamlit/secrets.toml.example
```

to:

```text
admin/.streamlit/secrets.toml
```

and fill in the same Supabase URL/key.

**Never commit `.env` or `admin/.streamlit/secrets.toml`.**

## 3. Supabase schema

The application expects these tables and columns.

### `users`

Required columns:

```text
id            bigint/int primary key
telegram_id   bigint not null unique
username      text nullable
first_name    text nullable
last_name     text nullable
created_at    timestamp/timestamptz
updated_at    timestamp/timestamptz
```

Your existing database already has a `telegram_id` column. The bot deliberately uses `telegram_id`, not `telegram_user_id`.

### `telegram_channels`

```text
id            bigint/int primary key
name          text not null
chat_id       bigint not null unique
username      text nullable
invite_link   text nullable
is_active     boolean default true
created_at    timestamp/timestamptz
```

### `resources`

```text
id            bigint/int primary key
name          text not null
drive_url     text not null
is_active     boolean default true
created_at    timestamp/timestamptz
```

### `resource_required_channels`

```text
resource_id   foreign key -> resources.id
channel_id    foreign key -> telegram_channels.id
```

Use a unique constraint on `(resource_id, channel_id)`.

The bot only requires these four core tables. Older experimental tables such as `verification_logs`, `pending_downloads`, and `channel_join_requests` are not required by the current implementation.

## 4. Telegram bot permissions

For every private channel that is used as a requirement:

1. Add the bot to the channel.
2. Promote it to administrator.
3. Give it enough permission to inspect members.
4. The bot must be able to access `getChatMember` for the channel.
5. For automatically generated join-request invite links, the bot also needs the appropriate invite/admin permission.

The Channels page can generate a Telegram invite link with join requests enabled. If you already have a suitable invite link, you can enter it manually.

## 5. Get a channel Chat ID

For a public channel, after adding/configuring the bot, run:

```powershell
cd "D:\Code Playground\AnimeWorld\bot"
..\ .venv\Scripts\python.exe get_chat_id.py @YourChannel
```

The command is normally:

```powershell
..\.venv\Scripts\python.exe get_chat_id.py @YourChannel
```

It prints the Telegram channel ID.

## 6. Start the bot

From the project root:

```powershell
.venv\Scripts\python.exe bot\main.py
```

You should see a log similar to:

```text
Starting @YourBot ...
```

Keep this terminal running.

## 7. Start the admin panel

Open another terminal:

```powershell
cd "D:\Code Playground\AnimeWorld"
.venv\Scripts\python.exe -m streamlit run admin\app.py
```

Streamlit will open the admin panel in your browser.

## 8. Admin workflow

### Add a channel

Open **Channels**:

1. Enter channel name.
2. Enter Telegram Chat ID.
3. Optionally enter the public username.
4. Leave Invite Link empty if you want the panel to generate a join-request link.
5. Click **Add Channel**.

The bot must be an administrator in the channel for automatic invite-link creation.

### Create a resource

Open **Resources**:

1. Enter the resource/anime name.
2. Enter the Google Drive URL.
3. Select all required channels.
4. Keep the resource active.
5. Create the resource.

The panel generates:

```text
https://t.me/YourBotUsername?start=resource_123
```

Copy that deep link into your authorized Telegram release/update post.

## 9. User flow

```text
Anime World channel
        │
        │ Download button
        ▼
Telegram bot
        │
        │ /start resource_<id>
        ▼
Load resource from Supabase
        │
        ▼
Load required channels
        │
        ▼
Check Telegram membership
        │
        ├── Missing channels
        │       │
        │       ▼
        │   Show Join Channel buttons
        │       │
        │       ▼
        │   User joins
        │       │
        │       ▼
        │   Verify Again
        │
        └── All required memberships valid
                │
                ▼
        Show Google Drive button
```

## Important verification detail

The current implementation verifies **actual Telegram membership** using `getChatMember`.

A submitted join request is not treated as membership. For a channel configured with join requests, the user may remain pending until the request is approved. If your channel requires manual approval, approve the request before expecting membership verification to pass.

This is intentional: it avoids granting a download link merely because a request was submitted.

## Troubleshooting

### `telegram_id` NOT NULL error

The bot expects:

```text
users.telegram_id
```

not:

```text
users.telegram_user_id
```

If your database has a different schema, update the schema or adapt `bot/database.py`.

### Bot says every channel is missing

Check:

- Bot is an administrator in the channel.
- `chat_id` is correct.
- The channel is active in the admin panel.
- The user has actually joined/been approved.
- The bot is using the same Telegram account/token you configured.
- The required-channel relationship exists in `resource_required_channels`.

### Invite-link generation fails

The bot needs sufficient administrator/invite rights in the channel. Alternatively, paste an existing valid invite link into the Channels page.

### Streamlit secrets error

Make sure `admin/.streamlit/secrets.toml` is valid TOML:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_KEY"
```

Do not paste Python syntax into this file.

## Security

Do not put Telegram bot tokens or Supabase service-role keys in GitHub or in a shared ZIP.

If a bot token or service-role key has ever been exposed, rotate/revoke it and replace it in your local `.env`/Streamlit secrets.

## Current implementation notes

- Google Drive links are stored in Supabase as resource metadata; the files themselves are not uploaded to Supabase.
- The bot does not require Redis.
- The project does not require Docker.
- The current implementation has one active pending concept: the resource ID is carried in the Telegram deep link and verification callback.
- The implementation intentionally keeps the database layer synchronous because the Supabase Python client is synchronous; Telegram handlers remain asynchronous.

## Production hardening to consider later

- Admin authentication for Streamlit.
- Audit logs for resource/channel changes.
- Pagination for large resource/channel lists.
- Rate limiting and abuse protection.
- More granular role-based access.
- Automatic handling/approval of join requests if that is desired for your channel policy.
- Expiring or rotating resource links.
