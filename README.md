# Telegram CSV / Excel Bot

A standalone Telegram bot for turning user-defined forms into ready-to-use CSV or Excel files.

## Core workflow

1. User starts a CSV project.
2. User defines any number of column names.
3. Bot asks for values one column at a time for each row.
4. A value can be skipped; the configured missing-value marker is written.
5. User can also paste multiple rows in bulk.
6. Bot generates CSV and/or XLSX and sends the file back in Telegram.
7. Session data is temporary by default and is removed after the project is finished/cancelled.

There are no hardcoded CSV columns and no website dependency.

## Stack

- Python 3.11+
- python-telegram-bot
- openpyxl for XLSX generation
- Python standard-library csv module
- In-memory session state by default

No database is required for the first version because the bot's purpose is temporary file generation.

## Security

- Put the Telegram bot token in `.env`.
- Never commit `.env`.
- The bot does not intentionally persist user records.
- Temporary generated files are removed after sending.
- Input size and column/row counts are limited in configuration.
- The bot does not log submitted row values.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
cp .env.example .env
```

Put the BotFather token in `.env`:

```env
TELEGRAM_BOT_TOKEN=your_token_here
```

Run:

```bash
python -m app
```

## Bot commands

- `/start` - start or reset the bot
- `/new` - create a new CSV project
- `/cancel` - cancel the current operation
- `/help` - show help

## Guided entry

After columns are created, choose `Add Row`. The bot asks:

```text
Name?
Phone?
City?
```

For a missing value, use `/skip` or the Skip button.

## Bulk entry

Choose `Paste Rows` and send rows separated by newlines.

Tabs are preferred when values may contain spaces:

```text
Rahul Sharma    9876543210    Pune    1500
Amit Shah       9123456789    Mumbai  800
```

The number of fields must match the number of configured columns.

## Output

The bot can generate:

- `.csv`
- `.xlsx`
- both

The Excel workbook contains a single sheet named `Data`, with a frozen header row and an autofilter.

## Limits

The defaults are deliberately conservative. Change them in `app/config.py` if required.

## Project layout

```text
telegram_csv_bot/
├── app/
│   ├── __main__.py
│   ├── bot.py
│   ├── config.py
│   ├── state.py
│   ├── csv_service.py
│   └── handlers.py
├── tests/
│   └── test_csv_service.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```
