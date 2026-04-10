from __future__ import annotations

import re
import unicodedata


CYRILLIC_MAP = {
    "А": "A",
    "Б": "B",
    "В": "V",
    "Г": "G",
    "Д": "D",
    "Е": "E",
    "Ё": "Yo",
    "Ж": "Zh",
    "З": "Z",
    "И": "I",
    "Й": "Y",
    "К": "K",
    "Л": "L",
    "М": "M",
    "Н": "N",
    "О": "O",
    "П": "P",
    "Р": "R",
    "С": "S",
    "Т": "T",
    "У": "U",
    "Ф": "F",
    "Х": "Kh",
    "Ц": "Ts",
    "Ч": "Ch",
    "Ш": "Sh",
    "Щ": "Shch",
    "Ъ": "",
    "Ы": "Y",
    "Ь": "",
    "Э": "E",
    "Ю": "Yu",
    "Я": "Ya",
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "yo",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}

HANGUL_CHO = ["g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "", "j", "jj", "ch", "k", "t", "p", "h"]
HANGUL_JUNG = ["a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa", "wae", "oe", "yo", "u", "wo", "we", "wi", "yu", "eu", "ui", "i"]
HANGUL_JONG = ["", "k", "k", "ks", "n", "nj", "nh", "t", "l", "lk", "lm", "lb", "ls", "lt", "lp", "lh", "m", "p", "ps", "t", "t", "ng", "t", "t", "k", "t", "p", "h"]

SPECIAL_REPLACEMENTS = {
    "\xa0": " ",
    "–": "-",
    "—": "-",
    "−": "-",
    "×": "x",
    "Ⅰ": "I",
    "Ⅱ": "II",
    "Ⅲ": "III",
    "Ⅳ": "IV",
    "Ⅴ": "V",
    "Ⅵ": "VI",
    "Ⅶ": "VII",
    "Ⅷ": "VIII",
    "Ⅸ": "IX",
    "Ⅹ": "X",
    "Ⅺ": "XI",
    "Ⅻ": "XII",
}

ROMAN_TOKENS = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"}
UPPER_TOKENS = {"AT", "MT", "CVT", "AWD", "RWD", "FWD", "GDI", "TDI", "TSI", "FSI", "CDI", "SUV", "GT", "GTS", "EV", "PHEV", "HEV", "LPG", "BMW"}

BRAND_ALIASES = {
    "audi": "Audi",
    "aston martin": "Aston Martin",
    "bmw": "BMW",
    "brabus": "Brabus",
    "cadillac": "Cadillac",
    "chevrolet": "Chevrolet",
    "daewoo": "Daewoo",
    "ford": "Ford",
    "geely": "Geely",
    "genesis": "Genesis",
    "gia": "Kia",
    "honda": "Honda",
    "hyundai": "Hyundai",
    "hyeondae": "Hyundai",
    "infiniti": "Infiniti",
    "jaguar": "Jaguar",
    "jeep": "Jeep",
    "jenesiseu": "Genesis",
    "kia": "Kia",
    "lada": "Lada",
    "lada vaz": "Lada",
    "land rover": "Land Rover",
    "lexus": "Lexus",
    "mazda": "Mazda",
    "mercedes": "Mercedes-Benz",
    "mercedes benz": "Mercedes-Benz",
    "mini": "Mini",
    "mitsubishi": "Mitsubishi",
    "nissan": "Nissan",
    "opel": "Opel",
    "peugeot": "Peugeot",
    "porsche": "Porsche",
    "renault": "Renault",
    "renault korea": "Renault Korea",
    "reunokoria samseong": "Renault Korea",
    "skoda": "Skoda",
    "ssangyong": "SsangYong",
    "subaru": "Subaru",
    "swebore gmdaeu": "Chevrolet",
    "suzuki": "Suzuki",
    "toyota": "Toyota",
    "volkswagen": "Volkswagen",
    "volvo": "Volvo",
    "vaz": "Lada",
    "xiaomi": "Xiaomi",
}

FUEL_ALIASES = {
    "benzin": "Gasoline",
    "dizel": "Diesel",
    "diesel": "Diesel",
    "dijel": "Diesel",
    "electric": "Electric",
    "electro": "Electric",
    "gasoline": "Gasoline",
    "gasolrin": "Gasoline",
    "gaz": "LPG",
    "haibeurideu": "Hybrid",
    "hybrid": "Hybrid",
    "jeongi": "Electric",
    "lpg": "LPG",
    "petrol": "Gasoline",
}

TRANSMISSION_ALIASES = {
    "akpp": "Automatic",
    "at": "Automatic",
    "automatic": "Automatic",
    "avtomat": "Automatic",
    "cvt": "CVT",
    "jadong": "Automatic",
    "manual": "Manual",
    "mekhanika": "Manual",
    "mkpp": "Manual",
    "mt": "Manual",
    "robot": "Robot",
    "sudong": "Manual",
    "variator": "CVT",
}


def normalize_spaces(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def apply_special_replacements(text: str) -> str:
    result = text
    for source, target in SPECIAL_REPLACEMENTS.items():
        result = result.replace(source, target)
    return result


def romanize_cyrillic(text: str) -> str:
    return "".join(CYRILLIC_MAP.get(char, char) for char in text)


def romanize_hangul(text: str) -> str:
    result: list[str] = []
    for char in text:
        code = ord(char)
        if 0xAC00 <= code <= 0xD7A3:
            offset = code - 0xAC00
            cho = offset // 588
            jung = (offset % 588) // 28
            jong = offset % 28
            result.append(HANGUL_CHO[cho] + HANGUL_JUNG[jung] + HANGUL_JONG[jong])
        else:
            result.append(char)
    return "".join(result)


def romanize_text(text: str | None) -> str:
    if text is None:
        return ""
    value = normalize_spaces(str(text))
    value = apply_special_replacements(value)
    value = romanize_hangul(value)
    value = romanize_cyrillic(value)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return normalize_spaces(value)


def canonical_key(text: str | None) -> str:
    value = romanize_text(text).lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return normalize_spaces(value)


def format_word(token: str) -> str:
    if not token:
        return token
    clean = token.strip()
    if clean.upper() in ROMAN_TOKENS or clean.upper() in UPPER_TOKENS:
        return clean.upper()
    if any(char.isdigit() for char in clean):
        return clean.upper()
    if len(clean) <= 2 and clean.isalpha():
        return clean.upper()
    return clean.capitalize()


def english_title(text: str | None) -> str:
    value = romanize_text(text)
    if not value:
        return ""

    chunks: list[str] = []
    for token in value.split():
        subtokens = [format_word(part) for part in token.split("-")]
        chunks.append("-".join(subtokens))
    return " ".join(chunks)


def normalize_brand(text: str | None) -> str:
    key = canonical_key(text)
    if key in BRAND_ALIASES:
        return BRAND_ALIASES[key]
    return english_title(text)


def normalize_fuel_type(text: str | None) -> str | None:
    key = canonical_key(text)
    if not key:
        return None
    for alias, normalized in FUEL_ALIASES.items():
        if alias in key:
            return normalized
    return english_title(text)


def normalize_transmission(text: str | None) -> str | None:
    key = canonical_key(text)
    if not key:
        return None
    for alias, normalized in TRANSMISSION_ALIASES.items():
        if alias in key:
            return normalized
    return english_title(text)


def build_clean_title(
    brand: str,
    model: str,
    year: int | None,
    fuel_type: str | None,
    transmission: str | None,
) -> str:
    parts = [part for part in [brand, model] if part]
    if year:
        parts.append(str(year))
    if fuel_type:
        parts.append(fuel_type)
    if transmission:
        parts.append(transmission)
    return " | ".join(parts)
