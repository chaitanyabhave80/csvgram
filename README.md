# csvgram

A Telegram bot that builds CSV and Excel files from chat. Define your own columns, enter rows one by one or paste them in bulk, then download the result as CSV, XLSX, or both.

No database. No server-side storage. Session data lives in memory only and is cleared after export or cancel.

## How it works

1. Tap **New CSV** and send your column names, separated by commas.
2. Add rows with **Add Row** (guided, one value at a time) or **Paste Rows** (bulk).
3. Tap **CSV**, **Excel**, or **Both** to get the file back in the chat.
4. The session is cleared after export.

There are no hardcoded columns. Any schema works, up to the limits below.

## Stack

- Python 3.11+
- python-telegram-bot 22.x
- openpyxl (XLSX generation)
- Standard-library `csv`
- In-memory session state

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS/Termux
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

Create a `.env` file in the project root with the token from BotFather:

```env
TELEGRAM_BOT_TOKEN=your_token_here
```

Run from the project root:

```bash
python -m app
```

## Commands

- `/start` - start or reset
- `/new` - start a new project
- `/skip` - skip the current field during guided entry (writes `N/A`)
- `/cancel` - cancel and clear the current project
- `/help` - show help

## Guided entry

After columns are saved, tap **Add Row**. The bot asks for each column in turn:

```text
Name?
Phone?
City?
```

Send `/skip` for a missing value.

## Bulk entry

Tap **Paste Rows** and send one row per line. The bot auto-detects the separator: it tries **tab** first, then **comma**.

```text
Rahul Sharma,9876543210,Pune,1500
Amit Shah,9123456789,Mumbai,800
```

Rules:

- Every row must have exactly as many values as there are columns.
- If a value itself contains a comma, wrap it in quotes: `"Pune, Maharashtra"`.
- Empty values become `N/A`.
- The batch is all-or-nothing. If any row is invalid, nothing is added and the bot tells you which row failed.

### Telegram's message limit

Telegram caps a single message at about 4096 characters. Longer pastes get cut off by the Telegram client before the bot ever sees them, and the bot cannot detect that. If your data is large, split it into several chunks and tap **Paste Rows** before each one. Rows keep accumulating across pastes.

A rough guide: at about 370 characters per row (50 columns), that is roughly 10 rows per message.

## Output

- `data.csv` (UTF-8 with BOM, opens correctly in Excel)
- `data.xlsx` (single sheet named `Data`, bold frozen header row, autofilter, auto-sized columns)

Files are built in memory and sent directly. Nothing is written to disk.

## Limits

Set in `app/config.py`:

| Setting | Default |
| --- | --- |
| Max columns | 50 |
| Max rows | 5000 |
| Max column name length | 100 characters |
| Max cell length | 5000 characters |
| Missing-value marker | `N/A` |

## Privacy and security

- No database and no persistence. Data exists only in memory for the active session.
- Restarting the bot clears all in-progress sessions.
- Submitted values are never logged.
- Keep the bot token in `.env` and never commit it. `.env` is in `.gitignore`.

## Project layout

```text
csvgram/
├── app/
│   ├── __init__.py
│   ├── __main__.py
│   ├── bot.py
│   ├── config.py
│   ├── state.py
│   ├── csv_service.py
│   └── handlers.py
├── tests/
│   └── test_csv_service.py
├── .gitignore
├── LICENSE
├── requirements.txt
└── README.md
```

## License

MIT. See `LICENSE`.
