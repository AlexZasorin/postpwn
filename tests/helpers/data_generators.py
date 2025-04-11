import random

from faker import Faker


def generate_id() -> str:
    fake = Faker()
    return fake.uuid4()


def generate_int(min_val: int = 1, max_val: int = 100) -> int:
    return random.randint(min_val, max_val)


def generate_text(words: int = 10, ext_word_list: list[str] | None = None) -> str:
    fake = Faker()

    generated_words = fake.words(words, ext_word_list=ext_word_list)

    return " ".join(generated_words)


def generate_datetime(before_now: bool = True, after_now: bool = False) -> str:
    fake = Faker()
    return str(fake.date_time_this_month(before_now=before_now, after_now=after_now))


def generate_date() -> str:
    fake = Faker()
    return str(fake.date_this_month(before_today=False, after_today=True))


def generate_timezone() -> str:
    fake = Faker()
    return fake.timezone()


def generate_url() -> str:
    fake = Faker()
    return fake.url()
