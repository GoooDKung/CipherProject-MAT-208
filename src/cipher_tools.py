"""Core Hill-cipher-style module over Z_26^2 (CLAUDE.md sec 2, sec 3.2 items 1-2)."""

import numpy as np

MOD = 26
FILLER = "X"


class SingularKeyError(Exception):
    """Raised when a key matrix K has gcd(det(K), 26) != 1 and cannot be inverted mod 26."""


def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    """Return (g, x, y) such that a*x + b*y = g = gcd(a, b)."""
    if b == 0:
        return a, 1, 0
    g, x1, y1 = extended_gcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


def mod_inverse(a: int, m: int = MOD) -> int:
    """Modular multiplicative inverse of a mod m via the Extended Euclidean Algorithm."""
    a = a % m
    g, x, _ = extended_gcd(a, m)
    if g != 1:
        raise SingularKeyError(f"No modular inverse: gcd({a}, {m}) = {g} != 1")
    return x % m


def matrix_det_mod(K: np.ndarray, m: int = MOD) -> int:
    """det(K) mod m for a 2x2 integer matrix."""
    a, b, c, d = int(K[0, 0]), int(K[0, 1]), int(K[1, 0]), int(K[1, 1])
    return (a * d - b * c) % m


def matrix_inverse_mod(K: np.ndarray, m: int = MOD) -> np.ndarray:
    """K^-1 mod m via the modular adjugate formula (sec 2.3). Raises SingularKeyError if not invertible."""
    det = matrix_det_mod(K, m)
    det_inv = mod_inverse(det, m)  # raises SingularKeyError if gcd(det, m) != 1
    a, b, c, d = int(K[0, 0]), int(K[0, 1]), int(K[1, 0]), int(K[1, 1])
    adj = np.array([[d, -b], [-c, a]]) % m
    return (det_inv * adj) % m


def find_nonzero_kernel_vector(K: np.ndarray, m: int = MOD) -> np.ndarray | None:
    """Brute-force search {0,...,m-1}^2 for a nonzero v0 with K v0 = 0 (mod m). Sec 2.4 / 3.2 item 3."""
    for p1 in range(m):
        for p2 in range(m):
            if p1 == 0 and p2 == 0:
                continue
            v = np.array([p1, p2])
            if np.array_equal((K @ v) % m, np.array([0, 0])):
                return v
    return None


def char_to_num(c: str) -> int:
    return ord(c.upper()) - ord("A")


def num_to_char(n: int) -> str:
    return chr((n % MOD) + ord("A"))


def text_to_vectors(message: str) -> list[np.ndarray]:
    """Strip non-letters, pad to even length with FILLER, split into 2x1 vectors."""
    letters = [c for c in message.upper() if c.isalpha()]
    if len(letters) % 2 != 0:
        letters.append(FILLER)
    return [
        np.array([char_to_num(letters[i]), char_to_num(letters[i + 1])])
        for i in range(0, len(letters), 2)
    ]


def vectors_to_text(vectors: list[np.ndarray]) -> str:
    return "".join(num_to_char(int(n)) for v in vectors for n in v)


def encode(message: str, K: np.ndarray) -> str:
    """Encrypt message with key matrix K: w = K v mod 26 for each digraph vector (sec 2.2)."""
    vectors = text_to_vectors(message)
    encoded_vectors = [(K @ v) % MOD for v in vectors]
    return vectors_to_text(encoded_vectors)


def decode(ciphertext: str, K: np.ndarray) -> str:
    """Decrypt ciphertext with key matrix K: v = K^-1 w mod 26 (sec 2.3).

    Raises SingularKeyError if gcd(det(K), 26) != 1.
    """
    K_inv = matrix_inverse_mod(K)  # raises SingularKeyError if not invertible
    vectors = text_to_vectors(ciphertext)
    decoded_vectors = [(K_inv @ w) % MOD for w in vectors]
    return vectors_to_text(decoded_vectors)


def evaluate_key(message: str, K: np.ndarray) -> dict:
    """Full report for one (message, K) pair, shared by terminal_tools.py and gui_app.py.

    Always includes det/gcd/invertibility and the ciphertext. When K is invertible,
    also includes K_inv and the decoded round-trip. When it is not, also includes
    the nonzero kernel vector v0 explaining why decoding cannot proceed (sec 2.4).
    """
    det = matrix_det_mod(K)
    g = int(np.gcd(det, MOD))
    invertible = g == 1
    ciphertext = encode(message, K)

    result = {
        "det": det,
        "gcd": g,
        "invertible": invertible,
        "ciphertext": ciphertext,
    }
    if invertible:
        result["K_inv"] = matrix_inverse_mod(K)
        result["decoded"] = decode(ciphertext, K)
    else:
        result["kernel_vector"] = find_nonzero_kernel_vector(K)
    return result


def recover_key(v1: np.ndarray, w1: np.ndarray, v2: np.ndarray, w2: np.ndarray) -> np.ndarray:
    """Known-plaintext attack (sec 2.5): recover K from two plaintext/ciphertext pairs.

    K = W P^-1 mod 26, where P = [v1 | v2], W = [w1 | w2].
    """
    P = np.column_stack([v1, v2])
    W = np.column_stack([w1, w2])
    P_inv = matrix_inverse_mod(P)  # raises SingularKeyError if P is not invertible mod 26
    return (W @ P_inv) % MOD
