from datetime import date


def calculate_age(born: date) -> int:
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def resolve_gender(gender: int) -> str | None:
    return {0: "Man", 1: "Woman"}.get(gender)
