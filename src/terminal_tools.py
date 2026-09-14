#!/usr/bin/env python3
"""Interactive key-testing CLI (CLAUDE.md sec 3.2 item 3).

Interactive mode (run with no arguments, works in any Mac/Linux terminal):
    python3 src/terminal_tools.py

Non-interactive / scriptable mode (for quick iteration, CI, or piping):
    python3 src/terminal_tools.py --message "ATTACKATDAWN" --key 3 3 2 5

Type 'quit' or 'exit' at the message prompt to leave the interactive loop.
"""

import argparse
import sys

import numpy as np

from cipher_tools import MOD, evaluate_key

QUIT_WORDS = {"quit", "exit", "q"}


def report_key(message: str, K: np.ndarray) -> None:
    """Print the full report for one (message, K) pair: det, gcd, invertibility, encode, decode/failure."""
    result = evaluate_key(message, K)

    print(f"\nKey matrix K =\n{K}")
    print(f"det(K) mod {MOD} = {result['det']}")
    print(f"gcd(det(K), {MOD}) = {result['gcd']}")
    print(f"Invertible mod {MOD}: {result['invertible']}")

    print(f"\nMessage:    {message.upper()}")
    print(f"Ciphertext: {result['ciphertext']}")

    if result["invertible"]:
        print(f"K^-1 mod {MOD} =\n{result['K_inv']}")
        print(f"Decoded:    {result['decoded']}")
    else:
        print(f"\nDecoding cannot proceed: (det K)^-1 mod {MOD} does not exist "
              f"because gcd(det(K), {MOD}) = {result['gcd']} != 1.")
        v0 = result["kernel_vector"]
        if v0 is not None:
            print(f"Nonzero kernel vector v0 (K v0 = 0 mod {MOD}): {v0.tolist()}")
            print("This means any plaintext digraph v collides with v + v0 "
                  "under this key (sec 2.4) — decoding is many-to-one, not just hard.")
        else:
            print("No nonzero kernel vector found (unexpected for a non-invertible key).")


def prompt_int(label: str) -> int:
    while True:
        raw = input(f"  {label} (0-25): ").strip()
        try:
            val = int(raw)
        except ValueError:
            print("  Please enter an integer.")
            continue
        if 0 <= val <= 25:
            return val
        print("  Value must be in {0, ..., 25}.")


def run_interactive() -> None:
    print("Hill-cipher key tester (Z_26^2). Type 'quit' to exit.\n")
    while True:
        message = input("Message to encode: ").strip()
        if message.lower() in QUIT_WORDS:
            print("Goodbye.")
            return
        if not message:
            print("Message cannot be empty.\n")
            continue

        print("Enter key matrix K = [[a, b], [c, d]]:")
        a = prompt_int("a")
        b = prompt_int("b")
        c = prompt_int("c")
        d = prompt_int("d")
        K = np.array([[a, b], [c, d]])

        report_key(message, K)
        print()


def run_noninteractive(message: str, key: list[int]) -> None:
    a, b, c, d = key
    K = np.array([[a, b], [c, d]])
    report_key(message, K)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="terminal_tools.py",
        description=(
            "Hill-cipher key tester over Z_26^2 (CLAUDE.md sec 3.2 item 3).\n\n"
            "Reports det(K) mod 26, gcd(det(K), 26), and whether K is invertible mod 26.\n"
            "  - If invertible: encodes the message and decodes it back (full round trip).\n"
            "  - If not invertible: still encodes the message, then explains why decoding\n"
            "    is impossible and prints a concrete nonzero kernel vector v0 with\n"
            "    K*v0 = 0 (mod 26)."
        ),
        epilog=(
            "examples:\n"
            "  Interactive mode (prompts for message, then a, b, c, d one at a time):\n"
            "    python3 terminal_tools.py\n\n"
            "  Scriptable mode, invertible key (worked example from CLAUDE.md, det=9):\n"
            "    python3 terminal_tools.py --message \"ATTACKATDAWN\" --key 3 3 2 5\n\n"
            "  Scriptable mode, singular key (det=13, shows the collision instead of decoding):\n"
            "    python3 terminal_tools.py --message \"HELLOO\" --key 1 1 1 14\n\n"
            "  In the interactive loop, type 'quit', 'exit', or 'q' at the message prompt to leave.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--message", type=str, metavar="TEXT",
        help="Message to encode. Non-letters are dropped; odd-length messages are padded with 'X'. "
             "Must be given together with --key, or omit both for interactive mode.",
    )
    parser.add_argument(
        "--key", type=int, nargs=4, metavar=("a", "b", "c", "d"),
        help="The four entries of key matrix K = [[a, b], [c, d]], each an integer in 0-25. "
             "Must be given together with --message, or omit both for interactive mode.",
    )
    args = parser.parse_args()

    if args.message is not None and args.key is not None:
        run_noninteractive(args.message, args.key)
    elif args.message is None and args.key is None:
        run_interactive()
    else:
        parser.error("--message and --key must be given together, or both omitted for interactive mode.")


if __name__ == "__main__":
    sys.exit(main())
