"""
report_scores.py  —  Export PFS results to CSV and generate a clean Persona Radar Chart.

Usage (from epps_workspace/):
    python -m src.eval.report_scores
    python -m src.eval.report_scores --paths data/file1.json data/file2.json --csv results.csv --radar chart.png
"""

import argparse
import json
import os
import csv
from collections import defaultdict
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np

# ── palette ──────────────────────────────────────────────────────────────────

METHOD_COLORS = {
    "ZeroShot":    "#ef5350",   # red
    "RagHistory":  "#ff9800",   # amber
    "NaiveSummary":"#42a5f5",   # blue
    "EPPS":        "#66bb6a",   # green
}

# ── helpers ───────────────────────────────────────────────────────────────────

def load_results(paths: List[str]) -> dict:
    """Load and merge results, appending the model size to prevent key collisions."""
    merged_results = defaultdict(list)
    for path in paths:
        if not os.path.exists(path):
            print(f"Warning: Results file not found and skipped: {path}")
            continue
            
        filename = os.path.basename(path)
        if "4B" in filename:
            model_tag = "4B"
        elif "30B" in filename:
            model_tag = "30B"
        elif "235B" in filename:
            model_tag = "235B"
        else:
            model_tag = ""

        with open(path, "r") as f:
            data = json.load(f)
            for method, entries in data.items():
                unique_method_name = f"{model_tag} {method}".strip()
                merged_results[unique_method_name].extend(entries)
    
    if not merged_results:
        raise ValueError("No valid data loaded from the provided paths.")
        
    return dict(merged_results)

def aggregate(results: dict) -> Dict[str, Dict[str, List[float]]]:
    scores: Dict[str, Dict[str, List[float]]] = {}
    for method, entries in results.items():
        scores[method] = defaultdict(list)
        for entry in entries:
            scores[method][entry["persona"]].append(float(entry["pfs"]))
    return scores

def method_color(method: str, idx: int) -> str:
    """Assign color based on base method name."""
    for base_method, color in METHOD_COLORS.items():
        if base_method in method:
            return color
    colors = plt.cm.tab20.colors
    return colors[idx % len(colors)]

def mean(vals: List[float]) -> float:
    return sum(vals) / len(vals) if vals else float("nan")

# ── CSV Export ────────────────────────────────────────────────────────────────

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

    footer = ["Mean"]
    all_grand: List[float] = []
    for persona in personas:
        combined = [s for m in methods for s in scores[m].get(persona, [])]
        all_grand.extend(combined)
        footer.append(f"{mean(combined):.1f}%")
    footer.append(f"{mean(all_grand):.1f}%")

    return rows, footer, col_labels

def export_to_csv(scores: dict, personas: List[str], methods: List[str], filepath: str):
    """Exports the summary table structure to a CSV file."""
    rows, footer, col_labels = build_summary_table(scores, personas, methods)
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
    
    with open(filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(col_labels)
        writer.writerows(rows)
        writer.writerow(footer)
    print(f"Saved CSV summary to {filepath}")

# ── Radar Chart ───────────────────────────────────────────────────────────────

def build_radar_chart(scores: dict, personas: List[str], methods: List[str], filepath: str):
    """Generates a Spider/Radar chart to visualize Persona Balance."""
    
    # FILTERING LOGIC: To prevent a messy web of 12 lines, we only plot the 235B model.
    # We also exclude ZeroShot since it's typically 0% and just crowds the center.
    radar_methods = [m for m in methods if "235B" in m and "ZeroShot" not in m]
    if not radar_methods:
        radar_methods = methods # Fallback if 235B isn't present
        
    N = len(personas)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1] 

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    
    plt.xticks(angles[:-1], personas, color='#1a1a2e', size=11, fontweight='bold')
    
    ax.set_rlabel_position(0)
    plt.yticks([20, 40, 60, 80], ["20", "40", "60", "80"], color="grey", size=9)
    plt.ylim(0, 100)

    for idx, method in enumerate(radar_methods):
        values = [mean(scores[method].get(p, [])) for p in personas]
        values = [v if not np.isnan(v) else 0 for v in values] 
        values += values[:1] 
        
        color = method_color(method, idx)
        ax.plot(angles, values, linewidth=2.5, linestyle='solid', label=method.replace("235B ", ""), color=color)
        ax.fill(angles, values, color=color, alpha=0.1)

    plt.title('Persona Generalization (235B Models)', size=15, fontweight='bold', y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1), fontsize=10)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
    fig.savefig(filepath, dpi=300, bbox_inches="tight")
    print(f"Saved radar chart to {filepath}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Export PFS results to CSV and plot radar chart.")
    parser.add_argument("--paths", nargs='+', default=[
        "data/eval_results_Qwen3-4B-Instruct-2507_reevaluated.json", 
        "data/eval_results_Qwen3-30B-A3B-Instruct-2507_reevaluated.json", 
        "data/eval_results_Qwen3-235B-A22B-Instruct-2507_reevaluated.json"
    ], help="List of paths to JSON result files to process and merge.")
    parser.add_argument("--csv", default="data/size_all_personas_summary.csv",
                        help="Export the summarized table to a CSV file.")
    parser.add_argument("--radar", default="data/radar_chart.png",
                        help="Path to save the radar chart image.")
    args = parser.parse_args()

    results = load_results(args.paths)
    scores  = aggregate(results)
    methods  = list(results.keys())
    personas = sorted({e["persona"] for entries in results.values() for e in entries})

    # Export to CSV
    if args.csv:
        export_to_csv(scores, personas, methods, args.csv)
        
    # Export Radar Chart
    if args.radar:
        build_radar_chart(scores, personas, methods, args.radar)

if __name__ == "__main__":
    main()