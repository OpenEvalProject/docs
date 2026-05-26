#!/usr/bin/env python3
"""Generate the OpenEval 36 in x 48 in vector-text poster PDF."""

from __future__ import annotations

import argparse
import importlib.util
import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


PROJECT = Path(__file__).resolve().parent


def find_workspace_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / "tmp_final.bib").exists() and (
            path / "poster_reference_backdrop" / "make_reference_backdrop.py"
        ).exists():
            return path
    raise RuntimeError(
        "Could not find tmp_final.bib and poster_reference_backdrop/ above "
        f"{start}"
    )


ROOT = find_workspace_root(PROJECT)
DEFAULT_BIB = ROOT / "tmp_final.bib"
DEFAULT_OUT = PROJECT / "out"
REFERENCE_SCRIPT = ROOT / "poster_reference_backdrop" / "make_reference_backdrop.py"
DEFAULT_QR_IMAGE = PROJECT / "assets" / "chatgpt_share_qr.pdf"
DEFAULT_POSTER_PDF_QR_IMAGE = PROJECT / "assets" / "openeval_poster_pdf_qr.pdf"


@dataclass(frozen=True)
class PosterStats:
    total_manuscripts: int
    post_publication_ai_reviews: int
    comparison_manuscripts: int


def format_percent(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0%"
    pct = 100.0 * numerator / denominator
    if abs(pct - round(pct)) < 0.05:
        return f"{round(pct):.0f}%"
    return f"{pct:.1f}%"


def load_reference_tools():
    spec = importlib.util.spec_from_file_location("reference_backdrop", REFERENCE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {REFERENCE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tex_path(path: Path) -> str:
    return r"\detokenize{" + str(path) + "}"


def write_background_references(
    lines: list[str],
    citations: list[str],
    tools,
    *,
    width_pt: float,
    height_pt: float,
    columns: int,
    margin_in: float,
    gap_in: float,
) -> None:
    margin_pt = margin_in * 72.0
    gap_pt = gap_in * 72.0
    usable_w_pt = width_pt - 2 * margin_pt - (columns - 1) * gap_pt
    usable_h_pt = height_pt - 2 * margin_pt
    col_w_pt = usable_w_pt / columns
    rows = math.ceil(len(citations) / columns)
    line_h_pt = usable_h_pt / rows
    font_size_pt = 1.95
    approx_char_pt = font_size_pt * 0.57
    max_chars = max(12, int(col_w_pt / approx_char_pt))

    lines.append(r"\begingroup")
    lines.append(r"\color{referencegray}\ttfamily\fontsize{1.95pt}{2.43pt}\selectfont")
    for idx, citation in enumerate(citations):
        col = idx // rows
        row = idx % rows
        x = margin_pt + col * (col_w_pt + gap_pt)
        y = height_pt - margin_pt - font_size_pt - row * line_h_pt
        visible = tools.tex_escape_visible(tools.truncate_to_column(citation, max_chars))
        lines.append(rf"\put({x:.2f},{y:.2f}){{\makebox[0pt][l]{{\strut {visible}}}}}")
    lines.append(r"\endgroup")


def write_foreground(
    lines: list[str],
    *,
    width_pt: float,
    height_pt: float,
    qr_size_in: float,
    qr_image: Path | None,
    poster_pdf_qr_size_in: float,
    poster_pdf_qr_image: Path | None,
    stats: PosterStats,
) -> None:
    qr_size_pt = qr_size_in * 72.0
    qr_x = (width_pt - qr_size_pt) / 2.0
    qr_y = 18.6 * 72.0
    title_y = height_pt - 3.15 * 72.0
    author_y = height_pt - 4.38 * 72.0
    affiliation_one_y = height_pt - 5.22 * 72.0
    affiliation_two_y = height_pt - 5.58 * 72.0
    affiliation_three_y = height_pt - 5.94 * 72.0
    cta_y = qr_y - 1.2 * 72.0

    lines.extend(
        [
            r"\begingroup",
            r"\color{black}\sffamily",
            rf"\put(0,{title_y:.2f}){{\makebox({width_pt:.2f},0)[c]{{\bfseries\fontsize{{82pt}}{{90pt}}\selectfont Science should be machine-readable}}}}",
            rf"\put(0,{author_y:.2f}){{\makebox({width_pt:.2f},0)[c]{{\fontsize{{43pt}}{{50pt}}\selectfont \underline{{A. Sina Booeshaghi}}\textsuperscript{{1}}, Laura Luebbert\textsuperscript{{2}}, Lior Pachter\textsuperscript{{3}}}}}}",
            rf"\put(0,{affiliation_one_y:.2f}){{\makebox({width_pt:.2f},0)[c]{{\fontsize{{19pt}}{{24pt}}\selectfont \textsuperscript{{1}}University of California Berkeley, Berkeley, CA USA}}}}",
            rf"\put(0,{affiliation_two_y:.2f}){{\makebox({width_pt:.2f},0)[c]{{\fontsize{{19pt}}{{24pt}}\selectfont \textsuperscript{{2}}Broad Institute of MIT and Harvard, Cambridge, MA, USA}}}}",
            rf"\put(0,{affiliation_three_y:.2f}){{\makebox({width_pt:.2f},0)[c]{{\fontsize{{19pt}}{{24pt}}\selectfont \textsuperscript{{3}}California Institute of Technology, Pasadena, CA USA}}}}",
            r"\endgroup",
            callout_tikz(width_pt, height_pt, stats),
            r"\begingroup",
            rf"\put({qr_x:.2f},{qr_y:.2f}){{\color{{white}}\rule{{{qr_size_pt:.2f}pt}}{{{qr_size_pt:.2f}pt}}}}",
        ]
    )

    if qr_image is not None:
        lines.append(
            rf"\put({qr_x:.2f},{qr_y:.2f}){{\includegraphics[width={qr_size_pt:.2f}pt,height={qr_size_pt:.2f}pt,keepaspectratio]{{{tex_path(qr_image)}}}}}"
        )
    else:
        lines.extend(
            [
                r"\linethickness{2.5pt}",
                rf"\put({qr_x:.2f},{qr_y:.2f}){{\color{{black}}\framebox({qr_size_pt:.2f},{qr_size_pt:.2f}){{\sffamily\bfseries\fontsize{{58pt}}{{68pt}}\selectfont QR code}}}}",
            ]
        )

    lines.extend(
        [
            r"\endgroup",
            r"\begingroup",
            r"\color{black}\sffamily",
            rf"\put(0,{cta_y:.2f}){{\makebox({width_pt:.2f},0)[c]{{\bfseries\fontsize{{47pt}}{{56pt}}\selectfont Chat with this poster. Scan the QR code with your camera.}}}}",
            r"\endgroup",
        ]
    )
    write_poster_pdf_qr(
        lines,
        qr_size_in=poster_pdf_qr_size_in,
        qr_image=poster_pdf_qr_image,
    )


def write_poster_pdf_qr(
    lines: list[str],
    *,
    qr_size_in: float,
    qr_image: Path | None,
) -> None:
    if qr_image is None:
        return

    qr_size_pt = qr_size_in * 72.0
    box_x = 0.55 * 72.0
    box_y = 0.55 * 72.0
    pad_pt = 14.0
    box_w = qr_size_pt + 252.0
    box_h = qr_size_pt + 2 * pad_pt
    qr_x = box_x + pad_pt
    qr_y = box_y + pad_pt
    text_x = qr_x + qr_size_pt + 20.0
    title_y = box_y + box_h - 62.0
    body_y = title_y - 26.0

    lines.extend(
        [
            r"\begingroup",
            rf"\put({box_x:.2f},{box_y:.2f}){{\color{{white}}\rule{{{box_w:.2f}pt}}{{{box_h:.2f}pt}}}}",
            r"\linethickness{1.2pt}",
            rf"\put({box_x:.2f},{box_y:.2f}){{\color{{black}}\framebox({box_w:.2f},{box_h:.2f}){{}}}}",
            rf"\put({qr_x:.2f},{qr_y:.2f}){{\includegraphics[width={qr_size_pt:.2f}pt,height={qr_size_pt:.2f}pt,keepaspectratio]{{{tex_path(qr_image)}}}}}",
            r"\color{black}\sffamily",
            rf"\put({text_x:.2f},{title_y:.2f}){{\makebox[0pt][l]{{\bfseries\fontsize{{18pt}}{{22pt}}\selectfont View poster PDF}}}}",
            rf"\put({text_x:.2f},{body_y:.2f}){{\makebox[0pt][l]{{\fontsize{{12pt}}{{15pt}}\selectfont Zoom in on references}}}}",
            r"\endgroup",
        ]
    )


def callout_tikz(width_pt: float, height_pt: float, stats: PosterStats) -> str:
    ai_pct = format_percent(stats.post_publication_ai_reviews, stats.total_manuscripts)
    comparison_pct = format_percent(stats.comparison_manuscripts, stats.total_manuscripts)
    ai_pct_tex = ai_pct.replace("%", r"\%")
    comparison_pct_tex = comparison_pct.replace("%", r"\%")
    box_x = width_pt - 930.0
    box_y = height_pt - 635.0
    reference_columns = 12
    reference_margin_pt = 0.03 * 72.0
    reference_gap_pt = 0.05 * 72.0
    reference_col_w = (
        width_pt - 2 * reference_margin_pt - (reference_columns - 1) * reference_gap_pt
    ) / reference_columns
    target_left = reference_margin_pt + 10 * (reference_col_w + reference_gap_pt)
    target_right = target_left + reference_col_w
    target_bottom = height_pt - 1090.0
    target_top = height_pt - 850.0
    target_y = (target_bottom + target_top) / 2.0
    return "\n".join(
        [
            r"\put(0,0){%",
            r"\begin{tikzpicture}[x=1pt,y=1pt,overlay]",
            rf"\draw[referencecallout, rounded corners=4pt, line width=2.2pt] ({target_left:.2f},{target_bottom:.2f}) rectangle ({target_right:.2f},{target_top:.2f});",
            rf"\node[name=calloutbox, anchor=north west, text width=565pt, align=left, rounded corners=10pt, inner sep=16pt, fill=calloutfill, draw=black, line width=2pt] at ({box_x:.2f},{box_y:.2f}) {{\sffamily\fontsize{{25pt}}{{32pt}}\selectfont \textbf{{Look closely:}}\\[4pt]\textbf{{{stats.total_manuscripts:,}}} total eLife manuscripts\\\textbf{{{stats.post_publication_ai_reviews:,}}} ({ai_pct_tex}) post-publication AI reviews\\\textbf{{{stats.comparison_manuscripts:,}}} ({comparison_pct_tex}) AI-peer review comparisons}};",
            rf"\draw[-{{Stealth[length=16pt,width=12pt]}}, line width=3.2pt, calloutarrow, shorten <=2pt] (calloutbox.south) .. controls +({0:.2f},-150.00) and ({target_left - 155:.2f},{target_y + 105:.2f}) .. ({target_left:.2f},{target_y:.2f});",
            r"\end{tikzpicture}%",
            r"}",
        ]
    )


def write_tex(
    citations: list[str],
    tools,
    output: Path,
    *,
    width_in: float,
    height_in: float,
    columns: int,
    margin_in: float,
    gap_in: float,
    reference_gray: float,
    qr_size_in: float,
    qr_image: Path | None,
    poster_pdf_qr_size_in: float,
    poster_pdf_qr_image: Path | None,
    stats: PosterStats,
) -> None:
    width_pt = width_in * 72.0
    height_pt = height_in * 72.0
    reference_gray = min(1.0, max(0.0, reference_gray))

    lines = [
        r"\documentclass{article}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage{lmodern}",
        r"\usepackage{graphicx}",
        r"\usepackage{xcolor}",
        r"\usepackage{tikz}",
        r"\usetikzlibrary{arrows.meta}",
        rf"\usepackage[papersize={{{width_in}in,{height_in}in}},margin=0in]{{geometry}}",
        r"\pagestyle{empty}",
        r"\setlength{\parindent}{0pt}",
        r"\setlength{\unitlength}{1pt}",
        rf"\definecolor{{referencegray}}{{gray}}{{{reference_gray:.3f}}}",
        r"\definecolor{calloutfill}{HTML}{FFF3B0}",
        r"\definecolor{calloutarrow}{HTML}{D1495B}",
        r"\definecolor{referencecallout}{HTML}{D1495B}",
        r"\begin{document}",
        rf"\begin{{picture}}({width_pt:.2f},{height_pt:.2f})",
    ]

    write_background_references(
        lines,
        citations,
        tools,
        width_pt=width_pt,
        height_pt=height_pt,
        columns=columns,
        margin_in=margin_in,
        gap_in=gap_in,
    )
    write_foreground(
        lines,
        width_pt=width_pt,
        height_pt=height_pt,
        qr_size_in=qr_size_in,
        qr_image=qr_image,
        poster_pdf_qr_size_in=poster_pdf_qr_size_in,
        poster_pdf_qr_image=poster_pdf_qr_image,
        stats=stats,
    )

    lines.extend([r"\end{picture}", r"\end{document}"])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compile_tex(tex_file: Path, out_dir: Path) -> Path:
    engine = shutil.which("lualatex")
    if engine is None:
        raise RuntimeError("lualatex not found")

    cmd = [
        engine,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-output-directory",
        str(out_dir),
        str(tex_file),
    ]
    subprocess.run(cmd, check=True, cwd=PROJECT)
    return out_dir / f"{tex_file.stem}.pdf"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bib", type=Path, default=DEFAULT_BIB)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--width-in", type=float, default=36.0)
    parser.add_argument("--height-in", type=float, default=48.0)
    parser.add_argument("--columns", type=int, default=12)
    parser.add_argument("--margin-in", type=float, default=0.03)
    parser.add_argument("--gap-in", type=float, default=0.05)
    parser.add_argument("--reference-gray", type=float, default=0.62)
    parser.add_argument("--qr-size-in", type=float, default=15.0)
    parser.add_argument("--qr-image", type=Path, default=DEFAULT_QR_IMAGE)
    parser.add_argument("--poster-pdf-qr-size-in", type=float, default=2.25)
    parser.add_argument(
        "--poster-pdf-qr-image", type=Path, default=DEFAULT_POSTER_PDF_QR_IMAGE
    )
    parser.add_argument("--total-manuscripts", type=int, default=16087)
    parser.add_argument("--post-publication-ai-reviews", type=int, default=13600)
    parser.add_argument("--comparison-manuscripts", type=int, default=2487)
    parser.add_argument("--no-compile", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    tools = load_reference_tools()

    qr_image = args.qr_image.resolve() if args.qr_image else None
    if qr_image is not None and not qr_image.exists():
        raise SystemExit(f"QR image not found: {qr_image}")
    poster_pdf_qr_image = (
        args.poster_pdf_qr_image.resolve() if args.poster_pdf_qr_image else None
    )
    if poster_pdf_qr_image is not None and not poster_pdf_qr_image.exists():
        raise SystemExit(f"Poster PDF QR image not found: {poster_pdf_qr_image}")

    stats = PosterStats(
        total_manuscripts=args.total_manuscripts,
        post_publication_ai_reviews=args.post_publication_ai_reviews,
        comparison_manuscripts=args.comparison_manuscripts,
    )
    citations = tools.load_citations(args.bib)
    if not citations:
        raise SystemExit(f"No BibTeX entries found in {args.bib}")

    tex_file = args.out_dir / "openeval_poster.tex"
    write_tex(
        citations,
        tools,
        tex_file,
        width_in=args.width_in,
        height_in=args.height_in,
        columns=args.columns,
        margin_in=args.margin_in,
        gap_in=args.gap_in,
        reference_gray=args.reference_gray,
        qr_size_in=args.qr_size_in,
        qr_image=qr_image,
        poster_pdf_qr_size_in=args.poster_pdf_qr_size_in,
        poster_pdf_qr_image=poster_pdf_qr_image,
        stats=stats,
    )

    print(f"Loaded {len(citations):,} references from {args.bib}")
    print(
        "Stats: "
        f"{stats.total_manuscripts:,} total manuscripts; "
        f"{stats.post_publication_ai_reviews:,} post-publication AI reviews; "
        f"{stats.comparison_manuscripts:,} AI-peer review comparison manuscripts"
    )
    print(f"Wrote {tex_file}")
    if not args.no_compile:
        pdf = compile_tex(tex_file, args.out_dir)
        print(f"Wrote {pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
