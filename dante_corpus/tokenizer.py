from pathlib import Path

convert_dict: dict[str, str] = {}


def split_on_apostrophes(text: str) -> list[str]:
    if not text:
        return []

    parts: list[str] = []
    current = ""
    prev_is_alpha = False
    for ch in text:
        if ch == "'":
            if prev_is_alpha:
                parts.append(current + ch)
                current = ""
            else:
                if current:
                    parts.append(current)
                current = ch
        else:
            current += ch
        prev_is_alpha = ch.isalpha()

    if current:
        parts.append(current)
    return parts


def tokenize_part(text: str) -> list[str]:
    tokens: list[str] = []
    current = ""
    prev_is_alpha = False
    for ch in text:
        if ch.isalpha() or ch == "'":
            if not prev_is_alpha and current:
                tokens.append(current)
                current = ""
            current += ch
            prev_is_alpha = True
        else:
            if current:
                tokens.append(current)
            current = ch
            prev_is_alpha = False

    if current:
        tokens.append(current)
    return tokens


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for part in split_on_apostrophes(text):
        tokens.extend(tokenize_part(part))
    return tokens


def _load_conversion_dict() -> None:
    if convert_dict:
        return

    script_dir = Path(__file__).resolve().parent
    quote_cases = (script_dir / "quote_cases.txt").read_text(encoding="utf-8").splitlines()
    quote_cases_converted = (
        script_dir / "quote_cases_converted.txt"
    ).read_text(encoding="utf-8").splitlines()

    for original, converted in zip(quote_cases, quote_cases_converted, strict=True):
        mapped = []
        for before, after in zip(original, converted, strict=True):
            mapped.append(before if after == '"' else after)
        convert_dict[original] = "".join(mapped)


def convert_apostrophe(text: str) -> str:
    _load_conversion_dict()
    return convert_dict.get(text, text.replace("\u2019", "'"))


def has_alpha(text: str) -> bool:
    return any(ch.isalpha() for ch in text)

