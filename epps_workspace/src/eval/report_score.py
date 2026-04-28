"""
report_scores.py  —  Visualise PFS results as a matplotlib table + line charts.

Usage (from epps_workspace/):
    python -m src.eval.report_scores
    python -m src.eval.report_scores --turns
    python -m src.eval.report_scores --path data/eval_results.json --save report.png
"""

import argparse
import json
import os
from collections import defaultdict
from typing import Dict, List, Tuple

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np

# ── palette ──────────────────────────────────────────────────────────────────

HEADER_BG   = "#1a1a2e"   # deep navy  – column/row headers
HEADER_FG   = "#ffffff"
SUBHEAD_BG  = "#16213e"   # slightly lighter – row-label column
ROW_EVEN    = "#f0f4ff"   # soft periwinkle
ROW_ODD     = "#ffffff"
FOOTER_BG   = "#e8eaf6"   # lavender – mean row
BORDER      = "#c5cae9"

METHOD_COLORS = {
    "ZeroShot":    "#ef5350",   # red
    "RagHistory":  "#ff9800",   # amber
    "NaiveSummary":"#42a5f5",   # blue
    "EPPS":        "#66bb6a",   # green
}
FALLBACK_COLORS = ["#7e57c2", "#26c6da", "#d4e157", "#ec407a"]


# ── helpers ───────────────────────────────────────────────────────────────────

def load_results(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Results file not found: {path}")
    with open(path) as f:
        return json.load(f)


def aggregate(results: dict) -> Dict[str, Dict[str, List[float]]]:
    scores: Dict[str, Dict[str, List[float]]] = {}
    for method, entries in results.items():
        scores[method] = defaultdict(list)
        for entry in entries:
            scores[method][entry["persona"]].append(float(entry["pfs"]))
    return scores


def method_color(method: str, idx: int) -> str:
    return METHOD_COLORS.get(method, FALLBACK_COLORS[idx % len(FALLBACK_COLORS)])


def mean(vals: List[float]) -> float:
    return sum(vals) / len(vals) if vals else float("nan")


# ── summary table ─────────────────────────────────────────────────────────────

def build_summary_table(
    scores: dict, personas: List[str], methods: List[str]
) -> Tuple[List[List[str]], List[str], List[str]]:
    col_labels = ["Method"] + personas + ["Overall"]
    rows: List[List[str]] = []

    for method in methods:
        all_vals: List[float] = []
        row = [method]
        for persona in personas:
            ps = scores[method].get(persona, [])
            all_vals.extend(ps)
            row.append(f"{mean(ps):.1f}%")
        row.append(f"{mean(all_vals):.1f}%")
        rows.append(row)

    # Footer: grand mean per persona
    footer = ["Mean"]
    all_grand: List[float] = []
    for persona in personas:
        combined = [s for m in methods for s in scores[m].get(persona, [])]
        all_grand.extend(combined)
        footer.append(f"{mean(combined):.1f}%")
    footer.append(f"{mean(all_grand):.1f}%")

    return rows, footer, col_labels


def plot_summary_table(
    scores: dict, personas: List[str], methods: List[str], ax: plt.Axes
):
    rows, footer, col_labels = build_summary_table(scores, personas, methods)
    n_rows = len(rows) + 1   # +1 footer
    n_cols = len(col_labels)

    ax.set_xlim(0, n_cols)
    ax.set_ylim(0, n_rows + 1)   # +1 for header
    ax.axis("off")

    cell_h = 1.0
    col_w  = 1.0

    def draw_cell(row_i, col_i, text, bg, fg="#1a1a2e", bold=False, fontsize=10):
        x = col_i * col_w
        y = (n_rows - row_i) * cell_h
        rect = plt.Rectangle(
            (x, y), col_w, cell_h,
            facecolor=bg, edgecolor=BORDER, linewidth=0.6, transform=ax.transData
        )
        ax.add_patch(rect)
        weight = "bold" if bold else "normal"
        ax.text(
            x + col_w / 2, y + cell_h / 2, text,
            ha="center", va="center", fontsize=fontsize,
            color=fg, fontweight=weight, transform=ax.transData,
        )

    # Header row
    for c, label in enumerate(col_labels):
        bg = HEADER_BG
        draw_cell(0, c, label, bg=bg, fg=HEADER_FG, bold=True, fontsize=10)

    # Data rows
    for r, row in enumerate(rows):
        method = row[0]
        row_bg_even = ROW_EVEN if r % 2 == 0 else ROW_ODD
        for c, cell in enumerate(row):
            if c == 0:
                # Method label — color-coded left border strip
                color = method_color(method, r)
                bg = row_bg_even
                x = c * col_w
                y = (n_rows - (r + 1)) * cell_h
                rect = plt.Rectangle(
                    (x, y), col_w, cell_h,
                    facecolor=bg, edgecolor=BORDER, linewidth=0.6
                )
                ax.add_patch(rect)
                strip = plt.Rectangle(
                    (x, y), 0.06, cell_h, facecolor=color, linewidth=0
                )
                ax.add_patch(strip)
                ax.text(
                    x + col_w / 2 + 0.03, y + cell_h / 2, cell,
                    ha="center", va="center", fontsize=10,
                    color="#1a1a2e", fontweight="bold"
                )
            else:
                draw_cell(r + 1, c, cell, bg=row_bg_even, fontsize=10)

    # Footer row
    for c, cell in enumerate(footer):
        draw_cell(n_rows, c, cell, bg=FOOTER_BG, bold=True, fontsize=10)


# ── per-turn line charts ──────────────────────────────────────────────────────

def plot_per_turn_lines(
    scores: dict, personas: List[str], methods: List[str], axes
):
    for ax, persona in zip(axes, personas):
        max_turns = max(len(scores[m].get(persona, [])) for m in methods)
        turns = list(range(1, max_turns + 1))

        for idx, method in enumerate(methods):
            ps = scores[method].get(persona, [])
            color = method_color(method, idx)
            ax.plot(
                turns, ps,
                marker="o", linewidth=2.2, markersize=6,
                color=color, label=method,
            )
            # Annotate final value
            if ps:
                ax.annotate(
                    f"{ps[-1]:.0f}%",
                    xy=(turns[-1], ps[-1]),
                    xytext=(4, 0), textcoords="offset points",
                    fontsize=8, color=color, va="center",
                )

        ax.set_title(persona, fontsize=11, fontweight="bold", color="#1a1a2e", pad=8)
        ax.set_xlabel("Turn", fontsize=9, color="#444")
        ax.set_ylabel("PFS (%)", fontsize=9, color="#444")
        ax.set_xticks(turns)
        ax.set_ylim(-5, 105)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        ax.tick_params(labelsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.legend(fontsize=8, framealpha=0.7)


# ── figure assembly ───────────────────────────────────────────────────────────

def build_figure(
    scores: dict, personas: List[str], methods: List[str], show_turns: bool
) -> plt.Figure:
    matplotlib.rcParams["font.family"] = "DejaVu Sans"

    if show_turns:
        fig = plt.figure(figsize=(14, 10))
        gs  = fig.add_gridspec(2, len(personas), height_ratios=[1.4, 1], hspace=0.45, wspace=0.35)
        table_ax = fig.add_subplot(gs[0, :])
        line_axes = [fig.add_subplot(gs[1, i]) for i in range(len(personas))]
    else:
        fig = plt.figure(figsize=(12, 4.5))
        table_ax = fig.add_subplot(111)
        line_axes = []

    # ── summary table ──
    n_data_cols = len(personas) + 1   # personas + Overall
    n_cols_total = 1 + n_data_cols    # + Method label col

    plot_summary_table(scores, personas, methods, table_ax)

    # Title above table
    table_ax.set_title(
        "Mean Pragmatic Faithfulness Score (PFS) by Method & Persona",
        fontsize=13, fontweight="bold", color="#1a1a2e", pad=14,
    )

    # ── per-turn line charts ──
    if show_turns:
        plot_per_turn_lines(scores, personas, methods, line_axes)
        fig.text(
            0.5, 0.47, "Per-Turn PFS by Persona",
            ha="center", fontsize=12, fontweight="bold", color="#1a1a2e",
        )

    fig.patch.set_facecolor("#f8f9fe")
    return fig


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Visualise PFS evaluation results.")
    parser.add_argument("--path",  default="data/eval_results_recalculated.json")
    parser.add_argument("--turns", action="store_true",
                        help="Also show per-turn line charts")
    parser.add_argument("--save",  default=None,
                        help="Save figure to this path instead of displaying")
    args = parser.parse_args()

    results = load_results(args.path)
    scores  = aggregate(results)
    methods  = list(results.keys())
    personas = sorted({e["persona"] for entries in results.values() for e in entries})

    fig = build_figure(scores, personas, methods, show_turns=args.turns)

    if args.save:
        os.makedirs(os.path.dirname(args.save) if os.path.dirname(args.save) else ".", exist_ok=True)
        fig.savefig(args.save, dpi=150, bbox_inches="tight")
        print(f"Saved to {args.save}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
