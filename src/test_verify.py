#!/usr/bin/env python3
"""Automated verification against CLAUDE.md sec 2-3 worked examples.

Run directly for a quick loop while iterating on cipher_tools.py:
    python3 src/test_verify.py

Or with pytest, if installed:
    pytest src/test_verify.py -v
"""

import math
import unittest

import numpy as np

from cipher_tools import (
    MOD,
    SingularKeyError,
    decode,
    encode,
    extended_gcd,
    find_nonzero_kernel_vector,
    matrix_det_mod,
    matrix_inverse_mod,
    mod_inverse,
    recover_key,
    text_to_vectors,
)

# The report's worked invertible key (CLAUDE.md sec 2.3): det = 9, gcd(9, 26) = 1.
INVERTIBLE_KEY = np.array([[3, 3], [2, 5]])

# The report's worked singular key family (CLAUDE.md sec 2.4): det = 13.
SINGULAR_KEY = np.array([[1, 1], [1, 14]])


class TestModularArithmetic(unittest.TestCase):
    def test_det_of_worked_invertible_key(self):
        self.assertEqual(matrix_det_mod(INVERTIBLE_KEY), 9)

    def test_det_of_worked_singular_key(self):
        self.assertEqual(matrix_det_mod(SINGULAR_KEY), 13)

    def test_mod_inverse_matches_extended_euclid(self):
        # 9 * 3 = 27 = 1 (mod 26)
        self.assertEqual(mod_inverse(9), 3)
        g, x, y = extended_gcd(9, 26)
        self.assertEqual(g, 1)
        self.assertEqual((9 * x + 26 * y) % 26, 1)

    def test_mod_inverse_raises_on_non_coprime(self):
        with self.assertRaises(SingularKeyError):
            mod_inverse(13)


class TestInvertibleKeyRoundTrip(unittest.TestCase):
    def test_k_times_kinv_is_identity_mod_26(self):
        K_inv = matrix_inverse_mod(INVERTIBLE_KEY)
        product = (INVERTIBLE_KEY @ K_inv) % MOD
        np.testing.assert_array_equal(product, np.eye(2, dtype=int))

    def test_encode_decode_round_trip(self):
        message = "ATTACKATDAWN"
        ciphertext = encode(message, INVERTIBLE_KEY)
        self.assertEqual(decode(ciphertext, INVERTIBLE_KEY), message)

    def test_odd_length_message_is_padded(self):
        message = "HELLO"  # odd length -> padded with filler
        ciphertext = encode(message, INVERTIBLE_KEY)
        decoded = decode(ciphertext, INVERTIBLE_KEY)
        self.assertEqual(decoded, "HELLOX")

    def test_linearity_axiom_holds(self):
        # T(au + bv) = aT(u) + bT(v) mod 26, for scalars a, b and vectors u, v (sec 2.1).
        u = np.array([3, 7])
        v = np.array([11, 2])
        a, b = 4, 5
        lhs = (INVERTIBLE_KEY @ ((a * u + b * v) % MOD)) % MOD
        rhs = (a * (INVERTIBLE_KEY @ u) + b * (INVERTIBLE_KEY @ v)) % MOD
        np.testing.assert_array_equal(lhs, rhs)


class TestSingularKeyFailure(unittest.TestCase):
    def test_gcd_is_shared_factor(self):
        det = matrix_det_mod(SINGULAR_KEY)
        self.assertIn(math.gcd(det, MOD), {2, 13, 26})

    def test_decode_raises_singular_key_error(self):
        ciphertext = encode("HELLOO", SINGULAR_KEY)
        with self.assertRaises(SingularKeyError):
            decode(ciphertext, SINGULAR_KEY)

    def test_encode_still_succeeds_on_singular_key(self):
        # Encoding never needs the inverse, so it must still work (sec 3.2 item 3).
        ciphertext = encode("HELLOO", SINGULAR_KEY)
        self.assertEqual(len(ciphertext), 6)

    def test_nonzero_kernel_vector_exists_and_is_correct(self):
        v0 = find_nonzero_kernel_vector(SINGULAR_KEY)
        self.assertIsNotNone(v0)
        self.assertFalse(np.array_equal(v0, np.zeros(2)))
        product = (SINGULAR_KEY @ v0) % MOD
        np.testing.assert_array_equal(product, np.array([0, 0]))

    def test_collision_from_kernel_vector(self):
        # v1 and v1 + v0 must encode to the exact same ciphertext (sec 2.4).
        v0 = find_nonzero_kernel_vector(SINGULAR_KEY)
        v1 = np.array([4, 9])
        v2 = (v1 + v0) % MOD
        self.assertFalse(np.array_equal(v1, v2))
        w1 = (SINGULAR_KEY @ v1) % MOD
        w2 = (SINGULAR_KEY @ v2) % MOD
        np.testing.assert_array_equal(w1, w2)


class TestKnownPlaintextAttack(unittest.TestCase):
    def test_recovers_exact_key_from_two_pairs(self):
        v1, v2 = text_to_vectors("ATTACKATDAWN")[:2]
        w1 = (INVERTIBLE_KEY @ v1) % MOD
        w2 = (INVERTIBLE_KEY @ v2) % MOD
        recovered = recover_key(v1, w1, v2, w2)
        np.testing.assert_array_equal(recovered, INVERTIBLE_KEY % MOD)

    def test_raises_if_plaintext_pairs_are_not_independent(self):
        # P = [v1 | v2] must itself be invertible mod 26, else the attack can't solve for K.
        v1 = np.array([1, 1])
        v2 = np.array([2, 2])  # linearly dependent on v1 -> det(P) = 0
        w1 = (INVERTIBLE_KEY @ v1) % MOD
        w2 = (INVERTIBLE_KEY @ v2) % MOD
        with self.assertRaises(SingularKeyError):
            recover_key(v1, w1, v2, w2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
