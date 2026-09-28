import csv
import io

from openpyxl import Workbook
from openpyxl.styles import Font

from .config import MAX_CELL_LENGTH, MAX_COLUMNS, MAX_ROWS


def validate_columns(columns: list[str]) -> None:
    if not 1 <= len(columns) <= MAX_COLUMNS:
        raise ValueError(f"Column count must be between 1 and {MAX_COLUMNS}.")
    seen = set()
    for column in columns:
        name = column.strip()
        if not name:
            raise ValueError("Column names cannot be empty.")
        if len(name) > 100:
            raise ValueError("A column name is too long.")
        key = name.casefold()
        if key in seen:
            raise ValueError(f"Duplicate column name: {name}")
        seen.add(key)


def validate_rows(columns: list[str], rows: list[list[str]]) -> None:
    if len(rows) > MAX_ROWS:
        raise ValueError(f"Maximum rows: {MAX_ROWS}.")
    for row in rows:
        if len(row) != len(columns):
            raise ValueError("A row does not contain the correct number of values.")
        if any(len(str(value)) > MAX_CELL_LENGTH for value in row):
            raise ValueError("A cell value is too long.")


def make_csv(columns: list[str], rows: list[list[str]]) -> io.BytesIO:
    validate_columns(columns)
    validate_rows(columns, rows)

    text = io.StringIO(newline="")
    writer = csv.writer(text, lineterminator="\n")
    writer.writerow(columns)
    writer.writerows(rows)

    data = io.BytesIO(text.getvalue().encode("utf-8-sig"))
    data.name = "data.csv"
    return data


def make_xlsx(columns: list[str], rows: list[list[str]]) -> io.BytesIO:
    validate_columns(columns)
    validate_rows(columns, rows)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Data"
    sheet.append(columns)

    for cell in sheet[1]:
        cell.font = Font(bold=True)

    for row in rows:
        sheet.append(row)

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    for column_cells in sheet.columns:
        values = [str(cell.value or "") for cell in column_cells]
        width = min(max(max(map(len, values), default=10) + 2, 10), 50)
        sheet.column_dimensions[column_cells[0].column_letter].width = width

    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    output.name = "data.xlsx"
    return output
