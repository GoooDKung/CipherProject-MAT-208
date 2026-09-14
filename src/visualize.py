#!/usr/bin/env python3
"""Comparison plots for the Hill cipher over Z_26^2 (CLAUDE.md sec 3.2 item 4).

Standardized 4-case evaluation suite:

  Case 1  Canonical invertible benchmark   K=[[3,3],[2,5]]   det=9,  gcd(det,26)=1
  Case 2  Strict singularity (det=0)       K=[[2,4],[1,2]]   det=0,  gcd(det,26)=26
  Case 3  Even zero-divisor (factor 2)     K=[[1,5],[6,2]]   det=24, gcd(det,26)=2
  Case 4  Odd zero-divisor (factor 13)     K=[[1,1],[1,14]]  det=13, gcd(det,26)=13

  (An alternate invertible key for Case 1 is K=[[1,5],[6,5]], det=1, gcd(1,26)=1 —
  swap it in via --invertible-key if you want a second bijective example.)

Case 1 renders as a side-by-side bijective scatter (676 in -> 676 unique out)
AND, for the report's comparative 2x2 panel, a 26x26 hit-count heatmap where
every cell reads exactly 1 (the |ker T|=1 baseline other cases collapse from).
Cases 2-4 render as a 26x26 hit-count heatmap: the map folds many-to-one, with
every populated cell receiving exactly |ker T| = gcd(det K, 26) input points
(verified numerically for all four cases below), consistent with the module
First Isomorphism Theorem Z_26^2 / ker(T) = Im(T).

Batch mode (default — runs all 4 cases into figures/):
    python3 src/visualize.py
    python3 src/visualize.py --batch

Single custom-key mode (bypasses the 4-case suite):
    python3 src/visualize.py --invertible-key 3 3 2 5 --singular-key 1 1 1 14 --out figures
"""

import argparse
import os
import textwrap

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from cipher_tools import MOD, find_nonzero_kernel_vector, matrix_det_mod

FIGURES_DIR = os.path.join(os.path.dirname(__file__), "..", "figures")
DPI = 300

DEFAULT_INVERTIBLE_KEY = np.array([[3, 3], [2, 5]])   # det = 9,  gcd(9, 26)  = 1
DEFAULT_SINGULAR_KEY = np.array([[1, 1], [1, 14]])    # det = 13, gcd(13, 26) = 13

CASES = [
    {
        "id": 1,
        "name": "Canonical Invertible Benchmark",
        "K": np.array([[3, 3], [2, 5]]),
        "scatter_file": "case1_invertible_scatter.png",
        "heatmap_file": "case1_invertible_heatmap.png",
        "heatmap_vmin": 0,
        "heatmap_vmax": 2,
    },
    {
        "id": 2,
        "name": "Strict Singularity (Linear Dependency)",
        "K": np.array([[2, 4], [1, 2]]),
        "heatmap_file": "case2_singular_det0.png",
    },
    {
        "id": 3,
        "name": "Even Non-Coprime Zero-Divisor (Factor 2)",
        "K": np.array([[1, 5], [6, 2]]),
        "heatmap_file": "case3_singular_factor2.png",
    },
    {
        "id": 4,
        "name": "Odd Non-Coprime Zero-Divisor (Factor 13)",
        "K": np.array([[1, 1], [1, 14]]),
        "heatmap_file": "case4_singular_factor13.png",
    },
]


def full_lattice() -> np.ndarray:
    """All 676 points of {0,...,25}^2 as an (676, 2) array."""
    p1, p2 = np.meshgrid(np.arange(MOD), np.arange(MOD), indexing="ij")
    return np.column_stack([p1.ravel(), p2.ravel()])


def apply_key(K: np.ndarray, points: np.ndarray) -> np.ndarray:
    """(K @ v) mod 26 for every row-vector v in points."""
    return (points @ K.T) % MOD


def kernel_vectors(K: np.ndarray) -> list[np.ndarray]:
    """All v in {0,...,25}^2 (including the zero vector) with K v = 0 (mod 26)."""
    lattice = full_lattice()
    images = apply_key(K, lattice)
    hits = np.all(images == 0, axis=1)
    return [v for v in lattice[hits]]


def draw_bijective_scatter(fig, K: np.ndarray, title: str) -> dict:
    """Draw the side-by-side bijective scatter onto an existing Figure (used by both
    the CLI's savefig path and the GUI's embedded FigureCanvas). Returns stats."""
    det = matrix_det_mod(K)
    inputs = full_lattice()
    outputs = apply_key(K, inputs)

    # Color by distance from the origin (Euclidean, in the 26x26 lattice) so the
    # same color pattern should reappear, permuted, in the output scatter.
    colors = np.linalg.norm(inputs, axis=1)

    n_unique = len(np.unique(outputs, axis=0))

    # Both axes use aspect="equal", so they render as small squares regardless
    # of how wide the containing figure/canvas is (matters when embedded live
    # in a resizable Qt panel, not just the fixed-aspect saved PNG). Extra
    # wspace and short titles keep the two square titles from colliding in
    # the middle when the figure is much wider than it is tall.
    axes = fig.subplots(1, 2, gridspec_kw={"wspace": 0.6})

    sc = axes[0].scatter(inputs[:, 0], inputs[:, 1], c=colors, cmap="viridis", s=14)
    axes[0].set_xlabel(r"$p_1$")
    axes[0].set_ylabel(r"$p_2$")
    axes[0].set_title("Plaintext Space", fontsize=10)

    axes[1].scatter(outputs[:, 0], outputs[:, 1], c=colors, cmap="viridis", s=14)
    axes[1].set_xlabel(r"$c_1$")
    axes[1].set_ylabel(r"$c_2$")
    axes[1].set_title(r"Ciphertext Space ($Kv$ mod 26)", fontsize=10)

    for ax in axes:
        ax.set_xlim(-1, MOD)
        ax.set_ylim(-1, MOD)
        ax.set_aspect("equal")
    fig.colorbar(sc, ax=axes, label="distance from origin", shrink=0.8)

    fig.suptitle(
        f"{title}\nK={K.tolist()}, det(K) mod 26 = {det} (gcd({det}, 26) = 1)\n"
        f"each of 676 points maps to a unique point — bijective "
        f"({n_unique}/676 distinct outputs)",
        fontsize=11,
    )
    return {"n_unique": n_unique, "bijective": n_unique == MOD * MOD}


def plot_bijective_scatter(K: np.ndarray, out_path: str, title: str) -> None:
    fig = plt.figure(figsize=(11, 5.5))
    stats = draw_bijective_scatter(fig, K, title)
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path} ({stats['n_unique']}/676 distinct output points; bijective = {stats['bijective']})")


def draw_heatmap(fig, K: np.ndarray, title: str, vmin: float = None, vmax: float = None) -> dict:
    """26x26 hit-count heatmap of T(v) = Kv mod 26, drawn onto an existing Figure.
    Handles both the bijective case (|ker T| = 1, every cell reads exactly 1) and
    singular keys (|ker T| > 1, annotated with a concrete collision v1, v1+v0),
    so it covers all 4 cases. Returns stats."""
    det = matrix_det_mod(K)
    g = int(np.gcd(det, MOD))
    inputs = full_lattice()
    outputs = apply_key(K, inputs)

    heatmap = np.zeros((MOD, MOD), dtype=int)
    for c1, c2 in outputs:
        heatmap[c1, c2] += 1

    kernel = kernel_vectors(K)
    kernel_order = len(kernel)
    image_size = MOD * MOD // kernel_order

    ax = fig.subplots(1, 1)
    im = ax.imshow(heatmap.T, origin="lower", cmap="magma", vmin=vmin, vmax=vmax)
    fig.colorbar(im, ax=ax, label="number of input points mapping here")
    ax.set_xlabel(r"$c_1$")
    ax.set_ylabel(r"$c_2$")
    ax.set_xlim(-0.5, MOD - 0.5)
    ax.set_ylim(-0.5, MOD - 0.5)

    if kernel_order > 1:
        v0 = find_nonzero_kernel_vector(K)
        v1 = np.array([4, 9])
        v2 = (v1 + v0) % MOD
        w1 = (K @ v1) % MOD
        w2 = (K @ v2) % MOD
        assert np.array_equal(w1, w2), "sanity check: v1 and v1+v0 must collide"

        ax.plot(w1[0], w1[1], marker="*", color="cyan", markersize=16, markeredgecolor="black")
        # Fixed text-box position (top-left) so the annotation never runs off the
        # canvas regardless of where the collision point w1 happens to land.
        ax.annotate(
            f"v1={v1.tolist()}, v1+v0={v2.tolist()}\nboth -> {w1.tolist()}",
            xy=(w1[0], w1[1]), xytext=(0.03, 0.97), textcoords="axes fraction",
            va="top", color="white", fontsize=9,
            bbox=dict(boxstyle="round", fc="black", alpha=0.6, ec="cyan"),
            arrowprops=dict(arrowstyle="->", color="cyan"),
        )
        kernel_note = f"(kernel vector v0 = {v0.tolist()}); every populated cell receives exactly "
        cell_scope = "populated cell"
    else:
        v0 = np.array([0, 0])
        kernel_note = "every cell receives exactly "
        cell_scope = "cell"

    bijective_suffix = " (bijective)" if kernel_order == 1 else ""
    stats_line = (
        f"|ker T| = {kernel_order}, |Im T| = 676/{kernel_order} = {image_size}; "
        f"{kernel_note}{kernel_order} input point{'s' if kernel_order != 1 else ''}"
        f"{bijective_suffix}"
    )
    # This line is long and its exact length varies by case (kernel vector,
    # counts); wrap it so it never overflows the figure width, whether saved
    # to file or embedded live in a resizable Qt canvas.
    stats_line = "\n".join(textwrap.wrap(stats_line, width=62))
    fig.suptitle(
        f"{title}\nK={K.tolist()}, det(K) mod 26 = {det} (gcd({det}, 26) = {g})\n{stats_line}",
        fontsize=10.5,
    )
    # Wrapping can push the suptitle to 3-4 lines depending on the case; give
    # it a bit more headroom than the scatter plot's fixed 3-line title.
    fig.subplots_adjust(top=0.82)
    max_count = int(heatmap.max())
    return {
        "kernel_order": kernel_order, "image_size": image_size,
        "max_count": max_count, "v0": v0, "cell_scope": cell_scope,
    }


def plot_heatmap(K: np.ndarray, out_path: str, title: str, vmin: float = None, vmax: float = None) -> None:
    fig = plt.figure(figsize=(8, 6.5))
    stats = draw_heatmap(fig, K, title, vmin=vmin, vmax=vmax)
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(
        f"Wrote {out_path} (|ker T|={stats['kernel_order']}, |Im T|={stats['image_size']}, "
        f"max hits/{stats['cell_scope'].split()[-1]}={stats['max_count']}, v0={stats['v0'].tolist()})"
    )


def run_case(case: dict, out_dir: str) -> None:
    base_title = f"Case {case['id']}: {case['name']}"
    has_both = "scatter_file" in case and "heatmap_file" in case

    if "scatter_file" in case:
        plot_bijective_scatter(case["K"], os.path.join(out_dir, case["scatter_file"]), base_title)

    if "heatmap_file" in case:
        heatmap_title = f"{base_title} (Hit-Count Heatmap)" if has_both else base_title
        plot_heatmap(
            case["K"], os.path.join(out_dir, case["heatmap_file"]), heatmap_title,
            vmin=case.get("heatmap_vmin"), vmax=case.get("heatmap_vmax"),
        )


def run_batch(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for case in CASES:
        run_case(case, out_dir)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the standardized 4-case matrix evaluation suite for the Hill cipher "
            "(CLAUDE.md sec 3.2 item 4): one bijective scatter plot and three collision "
            "heatmaps (det=0, and the two zero-divisor factors of 26)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  Batch mode — all 4 standardized cases (default, same as --batch):\n"
            "    python3 visualize.py\n\n"
            "  Single custom-key mode instead of the 4-case suite:\n"
            "    python3 visualize.py --invertible-key 3 3 2 5 --singular-key 1 1 1 14 --out figures\n"
        ),
    )
    parser.add_argument(
        "--batch", action="store_true",
        help="Run all 4 standardized cases (this is also the default when no key is given).",
    )
    parser.add_argument(
        "--invertible-key", type=int, nargs=4, metavar=("a", "b", "c", "d"),
        default=None, help="Entries of an invertible key matrix (must satisfy gcd(det K, 26)=1). "
                            "Switches to single custom-key mode.",
    )
    parser.add_argument(
        "--singular-key", type=int, nargs=4, metavar=("a", "b", "c", "d"),
        default=None, help="Entries of a singular/non-coprime key matrix (gcd(det K, 26) != 1). "
                            "Switches to single custom-key mode.",
    )
    parser.add_argument(
        "--out", type=str, default=FIGURES_DIR,
        help="Output directory for the PNGs (default: figures/ next to src/).",
    )
    args = parser.parse_args()

    custom_mode = args.invertible_key is not None or args.singular_key is not None

    if custom_mode:
        K_invertible = np.array(args.invertible_key).reshape(2, 2) if args.invertible_key else DEFAULT_INVERTIBLE_KEY
        K_singular = np.array(args.singular_key).reshape(2, 2) if args.singular_key else DEFAULT_SINGULAR_KEY

        if np.gcd(matrix_det_mod(K_invertible), MOD) != 1:
            parser.error(f"--invertible-key is not actually invertible mod 26 (det={matrix_det_mod(K_invertible)})")
        if np.gcd(matrix_det_mod(K_singular), MOD) == 1:
            parser.error(f"--singular-key is actually invertible mod 26 (det={matrix_det_mod(K_singular)}) — pick one with a shared factor")

        os.makedirs(args.out, exist_ok=True)
        plot_bijective_scatter(K_invertible, os.path.join(args.out, "bijective_scatter.png"), "Custom invertible key")
        plot_heatmap(K_singular, os.path.join(args.out, "collision_heatmap.png"), "Custom singular key")
    else:
        run_batch(args.out)


if __name__ == "__main__":
    main()
