# Color utils

Needs [uv](https://docs.astral.sh/uv/). Accepts `#rrggbb`, `#rgb`, or bare hex.

# hsl_diff

Diff two hex colors in HSL and OKLab. Optionally replay that shift onto a third color.

## Diff

```bash
uv run hsl_diff.py '#3a3a3a' '#5c5c5c'
```

```
HSL
  #3a3a3a   H=   0.0°  S=  0.0%  L= 22.7%
  #5c5c5c   H=   0.0°  S=  0.0%  L= 36.1%
  Δ         H=   +0.0°  S=  +0.0%  L= +13.3%
OKLab
  #3a3a3a   L=0.3485  a=+0.0000  b=+0.0000
  #5c5c5c   L=0.4748  a=+0.0000  b=+0.0000
  Δ         L=+0.1263  a=+0.0000  b=+0.0000  ΔE=0.1263
```

**HSL** — hue / saturation / lightness of each color, then signed deltas (from → to). Hue is the shortest wrap (−180°…+180°).

**OKLab** — perceptual L (lightness), a (green–red), b (blue–yellow). ΔE is Euclidean distance in that space.

## Apply

Pass a third color to add those deltas onto it. Each space produces its own hex (they will usually differ).

```bash
uv run hsl_diff.py '#3a3a3a' '#5c5c5c' '#8b0000'
```

```
apply HSL
  #8b0000   H=   0.0°  S=100.0%  L= 27.3%
  #cf0000   H=   0.0°  S=100.0%  L= 40.6%
apply OKLab
  #8b0000   L=0.3999  a=+0.1432  b=+0.0801
  #b6382c   L=0.5252  a=+0.1435  b=+0.0802
```

First line is the source, second is the result. `clipped` / `clipped to sRGB` means the result was outside the gamut and got clamped (HSL: S/L to 0–100; OKLab: RGB to 0–255).

# closest_token

Nearest RAYNET palette token for one hex. Overall winner per space, then nearest on each axis. Hue is skipped when the input is near gray. Palette: `palette.json` (`khaki40` / `olive40` / `khaki10` stored as hyphenated names).

```bash
uv run closest_token.py '#e9802f'
```

```
#e9802f
exact  orange       #e9802f
overall
  RGB    orange       #e9802f  Δ=0.0
  HSL    orange       #e9802f  Δ=0.000
  OKLab  orange       #e9802f  Δ=0.0000
axes
  RGB   R  orange       #e9802f  ΔR=+0
  HSL   H  orange       #e9802f  ΔH=+0.0°
  OKLCH L  orange       #e9802f  ΔL=+0.0000
  ...
```

**overall** — RGB Euclidean; cylindrical HSL; OKLab ΔE (perceptual stand-in for OKLCH).

**axes** — closest token by that one channel only. Signed Δ is token − input. A single-channel match can be a different hue (e.g. `#ff0000` R matches `white`).

# hueless

Gray with the same OKLab lightness (L kept, a=b=0). Same perceived brightness; not the same HSL L, and not WCAG contrast.

```bash
uv run hueless.py '#e9802f'
```

```
#e9802f   #e9802f  L=0.7038  C=0.1572
gray      #9f9f9f  L=0.7025  C=0.0000
```
