#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Usage: uv run closest_token.py '#e9802f'"""

import argparse
import colorsys
import json
import math
import sys
from pathlib import Path

PALETTE = Path(__file__).with_name("palette.json")
GRAY_S = 5.0
GRAY_C = 0.02


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


def rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return h * 360, s * 100, l * 100


def hue_delta(h1: float, h2: float) -> float:
    d = (h2 - h1) % 360
    return d - 360 if d > 180 else d


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


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


def oklab_to_oklch(L: float, a: float, b: float) -> tuple[float, float, float]:
    C = math.hypot(a, b)
    return L, C, math.degrees(math.atan2(b, a)) % 360


def load_tokens() -> list[dict]:
    data = json.loads(PALETTE.read_text())
    raw = data["tokens"] if isinstance(data, dict) and "tokens" in data else data
    tokens = []
    for name, hx in raw.items():
        rgb = parse_hex(hx)
        hsl = rgb_to_hsl(*rgb)
        oklab = rgb_to_oklab(*rgb)
        tokens.append(
            {
                "name": name,
                "hex": f"#{hx.removeprefix('#').lower()}",
                "rgb": rgb,
                "hsl": hsl,
                "oklab": oklab,
                "oklch": oklab_to_oklch(*oklab),
            }
        )
    return tokens


def nearest(tokens: list[dict], dist) -> tuple[dict, float]:
    best, best_d = tokens[0], dist(tokens[0])
    for t in tokens[1:]:
        d = dist(t)
        if d < best_d:
            best, best_d = t, d
    return best, best_d


def fmt_tok(t: dict) -> str:
    return f"{t['name']:<12} {t['hex']}"


def main() -> None:
    p = argparse.ArgumentParser(description="Closest palette token on HSL / OKLCH / RGB axes")
    p.add_argument("hex")
    args = p.parse_args()

    rgb = parse_hex(args.hex)
    hx = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    hsl = rgb_to_hsl(*rgb)
    oklab = rgb_to_oklab(*rgb)
    oklch = oklab_to_oklch(*oklab)
    tokens = load_tokens()

    print(hx)
    print(f"  HSL    H={hsl[0]:6.1f}°  S={hsl[1]:5.1f}%  L={hsl[2]:5.1f}%")
    print(f"  OKLCH  L={oklch[0]:.4f}  C={oklch[1]:.4f}  H={oklch[2]:6.1f}°")
    print(f"  RGB    R={rgb[0]:3d}  G={rgb[1]:3d}  B={rgb[2]:3d}")

    exact = [t for t in tokens if t["rgb"] == rgb]
    if exact:
        print(f"exact  {fmt_tok(exact[0])}")

    def rgb_d(t):
        return math.dist(rgb, t["rgb"])

    def hsl_d(t):
        dh = abs(hue_delta(hsl[0], t["hsl"][0])) / 180
        ds = abs(hsl[1] - t["hsl"][1]) / 100
        dl = abs(hsl[2] - t["hsl"][2]) / 100
        return math.hypot(dh, ds, dl)

    def ok_d(t):
        return math.dist(oklab, t["oklab"])

    print("overall")
    for label, fn, unit, digits in (
        ("RGB  ", rgb_d, "", 1),
        ("HSL  ", hsl_d, "", 3),
        ("OKLab", ok_d, "", 4),
    ):
        t, d = nearest(tokens, fn)
        print(f"  {label}  {fmt_tok(t)}  Δ={d:.{digits}f}{unit}")

    h, s, l = hsl
    L, C, H = oklch
    r, g, b = rgb
    chromatic = [t for t in tokens if t["oklch"][1] >= GRAY_C and t["hsl"][1] >= GRAY_S]
    hue_pool = chromatic if C >= GRAY_C and s >= GRAY_S else []

    print("axes")
    rows: list[tuple[str, list[dict], object, str]] = [
        ("RGB   R", tokens, lambda t: abs(t["rgb"][0] - r), lambda t: f"ΔR={t['rgb'][0] - r:+d}"),
        ("RGB   G", tokens, lambda t: abs(t["rgb"][1] - g), lambda t: f"ΔG={t['rgb'][1] - g:+d}"),
        ("RGB   B", tokens, lambda t: abs(t["rgb"][2] - b), lambda t: f"ΔB={t['rgb'][2] - b:+d}"),
        ("HSL   S", tokens, lambda t: abs(t["hsl"][1] - s), lambda t: f"ΔS={t['hsl'][1] - s:+.1f}%"),
        ("HSL   L", tokens, lambda t: abs(t["hsl"][2] - l), lambda t: f"ΔL={t['hsl'][2] - l:+.1f}%"),
        ("OKLCH L", tokens, lambda t: abs(t["oklch"][0] - L), lambda t: f"ΔL={t['oklch'][0] - L:+.4f}"),
        ("OKLCH C", tokens, lambda t: abs(t["oklch"][1] - C), lambda t: f"ΔC={t['oklch'][1] - C:+.4f}"),
    ]
    if hue_pool:
        rows.insert(3, ("HSL   H", hue_pool, lambda t: abs(hue_delta(h, t["hsl"][0])), lambda t: f"ΔH={hue_delta(h, t['hsl'][0]):+.1f}°"))
        rows.append(("OKLCH H", hue_pool, lambda t: abs(hue_delta(H, t["oklch"][2])), lambda t: f"ΔH={hue_delta(H, t['oklch'][2]):+.1f}°"))

    for label, pool, dist, delta in rows:
        t, _ = nearest(pool, dist)
        print(f"  {label}  {fmt_tok(t)}  {delta(t)}")
    if not hue_pool:
        print("  HSL   H   n/a (near gray)")
        print("  OKLCH H   n/a (near gray)")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
