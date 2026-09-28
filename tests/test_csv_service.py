from app.csv_service import make_csv, make_xlsx


def test_csv_generation():
    data = make_csv(["Name", "City"], [["Rahul", "Pune"], ["Amit", "Mumbai"]])
    assert b"Name,City" in data.getvalue()
    assert b"Rahul,Pune" in data.getvalue()


def test_xlsx_generation():
    data = make_xlsx(["Name", "City"], [["Rahul", "Pune"]])
    assert data.getvalue().startswith(b"PK")
