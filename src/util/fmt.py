from datetime import datetime
from typing import Any, Generator
import math

from src.constants import ANSI
from src.util.parse import Convention


def format_dict(
    data: dict[Any, Any], miss_keys: list[Any] = None, linesplit: bool = False
) -> str:
    if miss_keys is None:
        miss_keys = []
    lines: list[str] = []
    for k, v in data.items():
        v_str = f"{v}"
        if linesplit:
            lines.append(f"**{k}**:\n. . . {v_str}")
        else:
            lines.append(f"**{k}**: {v_str}")

    return "\n".join(lines)


def fmt_size(n_bytes: int, cvtn: Convention = Convention.BINARY):
    if cvtn == Convention.BINARY:
        size_factor = math.log(n_bytes, 2) // 10
    else:
        size_factor = math.log(n_bytes, 1000) // 1

    ext: str
    match round(size_factor):
        case 0:
            ext = "B"
        case 1:
            ext = "KiB"
        case 2:
            ext = "MiB"
        case 3:
            ext = "GiB"
        case 4:
            ext = "TiB"
        case 5:
            ext = "PiB"
        case 6:
            ext = "EiB"
        case 7:
            ext = "ZiB"
        case 8:
            ext = "YiB"
        case _:
            ext = "..."

    if cvtn == Convention.BINARY:
        n_bytes_factored = float(n_bytes) / (2 ** (10 * size_factor))
    else:
        n_bytes_factored = float(n_bytes) / (1000**size_factor)
        ext = ext.replace("i", "")
        ext = ext[:1].lower() + ext[1:]

    nb_fmt = round(n_bytes_factored, 3)
    if nb_fmt // 1 == nb_fmt:
        nb_fmt = int(nb_fmt)

    return f"{nb_fmt} {ext}"


def ctext(text: str, color: str):
    return f"{ANSI[color]}{text}{ANSI['reset']}"
    # start = f"\u001b[{fmt}"
    # if text_col:
    #     start += f";{text_col}"
    # if bg_col:
    #     start += f";{bg_col}"
    # return f"{start}m{text}"


def fbool(b: bool):
    if b:
        text = ctext("Yes", color="green")  # green for True
    else:
        text = ctext("No", color="red")  # Red for False
    text += "\u001b[0m"
    return text


def natural_join(l: list[str] | Generator[str, Any, Any]) -> str:
    if isinstance(l, Generator):
        l = list(l)
    n = len(l)
    match n:
        case 0:
            return ""
        case 1:
            return l[0]
        case 2:
            return f"{l[0]} and {l[1]}"
        case other:
            return f"{', '.join(l[:-1])}, and {l[-1]}"