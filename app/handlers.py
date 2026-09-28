import csv
import io

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from .config import (
    MAX_CELL_LENGTH,
    MAX_COLUMNS,
    MAX_ROWS,
    MAX_COLUMN_NAME_LENGTH,
)
from .csv_service import make_csv, make_xlsx, validate_columns
from .state import SessionStore

store = SessionStore()

BULK_DELIMITERS = ("\t", ",")


def parse_bulk_text(text: str, expected_columns: int):
    """Try tab first (safe with commas inside values), then comma
    (needs quotes around any value that itself contains a comma).
    Returns (parsed_rows, delimiter_used). If neither delimiter makes
    every row match expected_columns, returns the tab-parsed result
    so the normal per-row mismatch error still fires downstream."""
    cleaned = text.replace("\r", "")
    fallback = None
    for delim in BULK_DELIMITERS:
        reader = csv.reader(io.StringIO(cleaned), delimiter=delim)
        parsed = list(reader)
        if parsed and all(len(row) == expected_columns for row in parsed):
            return parsed, delim
        if fallback is None:
            fallback = parsed
    return fallback, BULK_DELIMITERS[0]


def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ New CSV", callback_data="new")],
        [InlineKeyboardButton("➕ Add Row", callback_data="row"),
         InlineKeyboardButton("📋 Paste Rows", callback_data="bulk")],
        [InlineKeyboardButton("📄 CSV", callback_data="csv"),
         InlineKeyboardButton("📊 Excel", callback_data="xlsx")],
        [InlineKeyboardButton("📦 Both", callback_data="both")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store.reset(update.effective_user.id)
    await update.message.reply_text(
        "CSV/Excel Bot\n\nCreate your columns, enter rows, then download CSV, Excel, or both.",
        reply_markup=menu(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/new - start a new project\n"
        "/cancel - cancel current project\n"
        "/skip - skip the current guided field\n"
        "/help - show this help\n\n"
        "Columns are completely user-defined."
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store.reset(update.effective_user.id)
    await update.message.reply_text("Current project cancelled.", reply_markup=menu())


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    project = store.get(user_id)
    action = query.data

    if action == "new":
        project = store.reset(user_id)
        project.mode = "columns"
        await query.edit_message_text(
            "Enter the column names separated by commas.\n\n"
            "Example:\nName, Phone, Email, City, Amount"
        )
    elif action == "row":
        if not project.columns:
            await query.edit_message_text("Create columns first with New CSV.")
            return
        if len(project.rows) >= MAX_ROWS:
            await query.edit_message_text("The row limit has been reached.")
            return
        project.mode = "guided"
        project.current_row = []
        project.column_index = 0
        await query.edit_message_text(f"{project.columns[0]}?")
    elif action == "bulk":
        if not project.columns:
            await query.edit_message_text("Create columns first with New CSV.")
            return
        project.mode = "bulk"
        await query.edit_message_text(
            f"Send rows separated by newlines.\n"
            f"Use TAB between values.\n\n"
            f"Expected {len(project.columns)} values per row."
        )
    elif action in {"csv", "xlsx", "both"}:
        if not project.columns or not project.rows:
            await query.edit_message_text("Add at least one row first.")
            return
        await send_files(update, action, project)
        store.reset(user_id)
    elif action == "cancel":
        store.reset(user_id)
        await query.edit_message_text("Project cancelled.", reply_markup=menu())


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    project = store.get(user_id)
    text = update.message.text.strip()

    if project.mode == "columns":
        columns = [x.strip() for x in text.split(",") if x.strip()]
        if len(columns) > MAX_COLUMNS or any(len(x) > MAX_COLUMN_NAME_LENGTH for x in columns):
            await update.message.reply_text("Invalid column list. Check the number or length of column names.")
            return
        try:
            validate_columns(columns)
        except ValueError as exc:
            await update.message.reply_text(str(exc))
            return

        project.columns = columns
        project.mode = None
        await update.message.reply_text(
            "Columns saved:\n\n" + " | ".join(columns) +
            "\n\nUse Add Row for guided entry or Paste Rows for bulk entry.",
            reply_markup=menu(),
        )
        return

    if project.mode == "guided":
        value = text
        if len(value) > MAX_CELL_LENGTH:
            await update.message.reply_text("That value is too long.")
            return

        project.current_row.append(value)
        project.column_index += 1

        if project.column_index < len(project.columns):
            await update.message.reply_text(f"{project.columns[project.column_index]}?")
            return

        project.rows.append(project.current_row)
        project.current_row = []
        project.column_index = 0
        project.mode = None
        await update.message.reply_text(
            f"✅ Row {len(project.rows)} added.",
            reply_markup=menu(),
        )
        return

    if project.mode == "bulk":
        parsed, delim_used = parse_bulk_text(text, len(project.columns))
        if not parsed:
            await update.message.reply_text("No rows received.")
            return

        if len(project.rows) + len(parsed) > MAX_ROWS:
            await update.message.reply_text(f"Maximum rows: {MAX_ROWS}.")
            return

        # Validate the whole batch first — commit nothing until every row passes.
        cleaned_rows = []
        for i, row in enumerate(parsed, start=1):
            if len(row) != len(project.columns):
                await update.message.reply_text(
                    f"Row {i} has {len(row)} value(s), expected {len(project.columns)} "
                    f"(tried tab and comma as separators — used comma). "
                    "If a value itself contains a comma, wrap it in quotes. "
                    "Nothing was added — fix and resend the whole batch."
                    if delim_used == ","
                    else
                    f"Row {i} has {len(row)} value(s), expected {len(project.columns)}. "
                    "Nothing was added — fix and resend the whole batch."
                )
                return
            cleaned = [v.strip() if v.strip() else project.missing_value for v in row]
            if any(len(v) > MAX_CELL_LENGTH for v in cleaned):
                await update.message.reply_text(
                    f"Row {i} has a value that's too long. Nothing was added — fix and resend."
                )
                return
            cleaned_rows.append(cleaned)

        project.rows.extend(cleaned_rows)
        project.mode = None
        await update.message.reply_text(
            f"✅ Added {len(cleaned_rows)} row(s). Total: {len(project.rows)}.",
            reply_markup=menu(),
        )
        return

    await update.message.reply_text("Choose an action from the menu.", reply_markup=menu())


async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    project = store.get(user_id)
    if project.mode != "guided":
        await update.message.reply_text("Skip is only available during guided row entry.")
        return

    project.current_row.append(project.missing_value)
    project.column_index += 1

    if project.column_index < len(project.columns):
        await update.message.reply_text(f"{project.columns[project.column_index]}?")
    else:
        project.rows.append(project.current_row)
        project.current_row = []
        project.column_index = 0
        project.mode = None
        await update.message.reply_text(
            f"✅ Row {len(project.rows)} added.",
            reply_markup=menu(),
        )


async def send_files(update: Update, action: str, project):
    target = update.callback_query.message

    if action in {"csv", "both"}:
        data = make_csv(project.columns, project.rows)
        data.seek(0)
        await target.reply_document(document=data, filename="data.csv")

    if action in {"xlsx", "both"}:
        data = make_xlsx(project.columns, project.rows)
        data.seek(0)
        await target.reply_document(document=data, filename="data.xlsx")

    await target.reply_text("Files generated. The temporary project has been cleared.", reply_markup=menu())
