"""Streamlit web demo for the Hill cipher over Z_26^2 (MAT-208 Project #2).

Reuses cipher_tools.py (encode/decode/modular inverse, no numpy.linalg.inv or
floating point) and visualize.py (CASES, draw_bijective_scatter, draw_heatmap)
so the web app, the CLI tester, the batch figure generator, and the desktop
GUI all share one implementation of the actual math.

Run:
    source .venv/bin/activate   # needs numpy, matplotlib, streamlit
    streamlit run src/app.py
"""

import math

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from cipher_tools import (
    MOD,
    decode,
    encode,
    find_nonzero_kernel_vector,
    matrix_det_mod,
    matrix_inverse_mod,
    mod_inverse,
    text_to_vectors,
    vectors_to_text,
)
from visualize import CASES, draw_bijective_scatter, draw_heatmap, kernel_vectors

PRESET_LABELS = {
    1: "Invertible (det=9)",
    2: "Det=0 (Strict)",
    3: "Factor 2 (det=24)",
    4: "Factor 13 (det=13)",
}

st.set_page_config(
    page_title="Secret Code Explorer",
    page_icon="🔐",
    layout="wide",
)

# Theme-neutral tweaks only — no hardcoded background/text colors, so this
# reads correctly in both Streamlit's light and dark modes. Native widgets
# (st.metric, st.success/error/warning) already adapt to the active theme;
# this just trims the default top padding.
st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- Session state / key inputs -------------------------------------------

DEFAULT_KEY = CASES[0]["K"]
for label, default in zip("abcd", [int(DEFAULT_KEY[0, 0]), int(DEFAULT_KEY[0, 1]),
                                    int(DEFAULT_KEY[1, 0]), int(DEFAULT_KEY[1, 1])]):
    if label not in st.session_state:
        st.session_state[label] = default


def load_preset(case: dict) -> None:
    K = case["K"]
    st.session_state["a"] = int(K[0, 0])
    st.session_state["b"] = int(K[0, 1])
    st.session_state["c"] = int(K[1, 0])
    st.session_state["d"] = int(K[1, 1])


with st.sidebar:
    st.header("Inputs")
    message = st.text_input("Plaintext Message", value="ATTACKATDAWN")

    st.subheader("Key Matrix K")
    row1 = st.columns(2)
    row1[0].number_input("a", min_value=0, max_value=MOD - 1, key="a")
    row1[1].number_input("b", min_value=0, max_value=MOD - 1, key="b")
    row2 = st.columns(2)
    row2[0].number_input("c", min_value=0, max_value=MOD - 1, key="c")
    row2[1].number_input("d", min_value=0, max_value=MOD - 1, key="d")

    st.subheader("Preset Evaluation Cases")
    for case in CASES:
        label = f"Preset {case['id']}: {PRESET_LABELS[case['id']]}"
        st.button(label, on_click=load_preset, args=(case,), use_container_width=True)

K = np.array([
    [st.session_state["a"], st.session_state["b"]],
    [st.session_state["c"], st.session_state["d"]],
])

# ---- Header -----------------------------------------------------------

st.title("Secret Code Explorer: MAT-208 Vector Space Cryptosystem")
st.caption("Hill cipher over ℤ₂₆² — T(v) = Kv mod 26")

if not message.strip():
    st.warning("Enter a plaintext message in the sidebar to continue.")
    st.stop()

# ---- Metrics -----------------------------------------------------------

det = matrix_det_mod(K)
gcd = math.gcd(det, MOD)
invertible = gcd == 1

m1, m2, m3 = st.columns(3)
m1.metric("det(K) mod 26", det)
m2.metric("gcd(det(K), 26)", gcd)
m3.metric("Invertible mod 26", "✅ Yes" if invertible else "❌ No")

# ---- Encoding pipeline -----------------------------------------------

st.subheader("Encoding Pipeline")

plain_vectors = text_to_vectors(message)
cipher_vectors = [(K @ v) % MOD for v in plain_vectors]
ciphertext = encode(message, K)
padded_plaintext = vectors_to_text(plain_vectors)

st.write(f"**Padded plaintext:** `{padded_plaintext}`  (message → uppercase, non-letters stripped, "
         f"'X' appended if odd length)")

rows = [
    {
        "Digraph #": i + 1,
        "Plaintext": vectors_to_text([pv]),
        "v = [p1, p2]": pv.tolist(),
        "Kv mod 26": cv.tolist(),
        "Ciphertext": vectors_to_text([cv]),
    }
    for i, (pv, cv) in enumerate(zip(plain_vectors, cipher_vectors))
]
st.dataframe(rows, hide_index=True, use_container_width=True)

st.write(f"**Ciphertext (transmitted):** `{ciphertext}`")

# ---- Recovery / Diagnostics --------------------------------------------

st.subheader("Recovery")

original_letter_count = sum(c.isalpha() for c in message)
was_padded = original_letter_count % 2 != 0

if invertible:
    st.success("🔓 Key Invertible over ℤ₂₆² — decryption is well-defined.")

    det_inv = mod_inverse(det)
    K_inv = matrix_inverse_mod(K)
    st.write(f"**det⁻¹ mod 26** = {det_inv}  (verify: {det} × {det_inv} mod 26 = {(det * det_inv) % MOD})")
    st.write("**K⁻¹ mod 26** =")
    st.write(K_inv)

    st.markdown("**Decoded Pipeline**")
    decode_rows = [
        {
            "Digraph #": i + 1,
            "Ciphertext w": vectors_to_text([cv]),
            "K⁻¹·w mod 26": ((K_inv @ cv) % MOD).tolist(),
            "Recovered Plaintext": vectors_to_text([(K_inv @ cv) % MOD]),
        }
        for i, cv in enumerate(cipher_vectors)
    ]
    st.dataframe(decode_rows, hide_index=True, use_container_width=True)

    decoded = decode(ciphertext, K)
    if was_padded:
        st.write(f"**Recovered Plaintext:** `{decoded[:-1]}`**`{decoded[-1]}`** "
                  f"(trailing **{decoded[-1]}** is the padding character added at encode time, "
                  f"not part of the original message)")
    else:
        st.write(f"**Recovered Plaintext:** `{decoded}`")
else:
    st.error(f"**SingularKeyError:** Non-invertible Transformation (gcd(det, 26) = {gcd} ≠ 1)")
    st.markdown(
        "Scalar modular inverse does not exist. Decryption is mathematically impossible "
        "due to loss of injectivity."
    )

    st.markdown("**Diagnostic Engine**")
    v0 = find_nonzero_kernel_vector(K)
    kernel_size = len(kernel_vectors(K))
    image_size = MOD * MOD // kernel_size
    st.write(f"**Null vector** v0 = {v0.tolist()}ᵀ, where (K·v0) mod 26 = [0, 0]ᵀ")
    st.write(f"**Kernel cardinality** |ker(T)| = {kernel_size}")
    st.write(f"**Image contraction** |Im(T)| = 676 / {kernel_size} = {image_size}")

    v1 = plain_vectors[0]
    v2 = (v1 + v0) % MOD
    w1 = (K @ v1) % MOD
    w2 = (K @ v2) % MOD
    assert np.array_equal(w1, w2), "sanity check: v1 and v1+v0 must collide"

    d1, d2 = vectors_to_text([v1]), vectors_to_text([v2])
    c1, c2 = vectors_to_text([w1]), vectors_to_text([w2])
    st.warning(
        f"**Explicit Collision Proof**\n\n"
        f"- Digraph 1: v1 = {v1.tolist()}ᵀ (\"{d1}\") → (K·v1) mod 26 = {w1.tolist()}ᵀ (\"{c1}\")\n"
        f"- Digraph 2: v2 = (v1 + v0) mod 26 = {v2.tolist()}ᵀ (\"{d2}\") → (K·v2) mod 26 = {w2.tolist()}ᵀ (\"{c2}\")\n\n"
        f"Two distinct plaintexts collapse to the identical ciphertext coordinate. "
        f"Information is destroyed."
    )

# ---- Visualization -----------------------------------------------------

st.subheader("Visualization")

heatmap_vmin, heatmap_vmax = None, None
for case in CASES:
    if np.array_equal(case["K"], K):
        heatmap_vmin = case.get("heatmap_vmin")
        heatmap_vmax = case.get("heatmap_vmax")
        break

fig = plt.figure(figsize=(10, 5) if invertible else (7, 6.5))
if invertible:
    draw_bijective_scatter(fig, K, "Live Key")
else:
    draw_heatmap(fig, K, "Live Key", vmin=heatmap_vmin, vmax=heatmap_vmax)
st.pyplot(fig)
plt.close(fig)
