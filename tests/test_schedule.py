from datetime import datetime

def test_week_type():
    now = datetime(2026, 6, 22)
    week_number = now.isocalendar().week
    week_type = "ЧЁТНАЯ" if week_number % 2 == 0 else "НЕЧЁТНАЯ"
    assert week_type == "ЧЁТНАЯ"

def test_day_mapping():
    days = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
    now = datetime(2026, 6, 22)
    today = days[now.weekday()]
    assert today == "ПН"
