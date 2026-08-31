#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Usage: uv run hueless.py '#e9802f'"""

import argparse
import math
import sys


def parse_hex(s: str) -> tuple[int, int, int]:
    s = s.removeprefix("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        raise SystemExit(f"not a hex color: {s!r}")
    try:
        return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    except ValueError:
        raise SystemExit(f"not a hex color: {s!r}") from None


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def rgb_to_oklab(r: int, g: int, b: int) -> tuple[float, float, float]:
    r, g, b = (srgb_to_linear(x / 255) for x in (r, g, b))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = l ** (1 / 3), m ** (1 / 3), s ** (1 / 3)
    return (
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )


def oklab_to_rgb(ok_l: float, ok_a: float, ok_b: float) -> tuple[int, int, int]:
    l_ = ok_l + 0.3963377774 * ok_a + 0.2158037573 * ok_b
    m_ = ok_l - 0.1055613458 * ok_a - 0.0638541728 * ok_b
    s_ = ok_l - 0.0894841775 * ok_a - 1.2914855480 * ok_b
    l, m, s = l_**3, m_**3, s_**3
    r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    out = []
    for c in (r, g, b):
        srgb = linear_to_srgb(c)
        out.append(round(min(1.0, max(0.0, srgb)) * 255))
    return out[0], out[1], out[2]


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def main() -> None:
    p = argparse.ArgumentParser(description="Achromatic gray with the same OKLab lightness")
    p.add_argument("hex")
    args = p.parse_args()

    rgb = parse_hex(args.hex)
    L, a, b = rgb_to_oklab(*rgb)
    C = math.hypot(a, b)
    gray = oklab_to_rgb(L, 0.0, 0.0)
    Lg, ag, bg = rgb_to_oklab(*gray)

    print(f"{args.hex:8}  {rgb_to_hex(*rgb)}  L={L:.4f}  C={C:.4f}")
    print(f"{'gray':8}  {rgb_to_hex(*gray)}  L={Lg:.4f}  C={math.hypot(ag, bg):.4f}")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
