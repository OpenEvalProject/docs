# OpenEval Poster: CSHL AI in Biology 2026

LaTeX source for a 36 in x 48 in portrait poster.

The reference field is generated as TeX text, not as a raster image. The QR code
is generated with `qrencode` and included as a vector PDF. The callout counts use
the manuscript-level values from the paper: 16,087 total manuscripts, 13,600
OpenEval-only post-publication AI reviews, and 2,487 manuscripts with AI-peer
review comparisons.

This folder is named for the intended documentation archive convention:

`YYYYMMDD-AuthorInitials-ShortName`

The checked-in PDF is the canonical poster artifact. The generator is included
for editing, but a full rebuild currently expects the original local
`claim-validation` workspace because the reference background is generated from
`tmp_final.bib` and `poster_reference_backdrop/make_reference_backdrop.py`.

## Generate

```bash
python3 make_openeval_poster.py
```

Outputs:

- `out/openeval_poster.tex`
- `out/openeval_poster.pdf`

## With a QR Code

```bash
python3 make_openeval_poster.py --qr-image /path/to/qr-code.png
```

Useful controls:

```bash
# Darker reference background
python3 make_openeval_poster.py --reference-gray 0.58

# Larger QR square
python3 make_openeval_poster.py --qr-size-in 17

# Wider or tighter reference columns
python3 make_openeval_poster.py --columns 12 --gap-in 0.04

# Override callout counts
python3 make_openeval_poster.py --total-manuscripts 16087 --post-publication-ai-reviews 13600 --comparison-manuscripts 2487
```
