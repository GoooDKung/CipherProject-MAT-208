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
    text_to_vectors,
    vectors_to_text,
)
from visualize import CASES, draw_bijective_scatter, draw_heatmap, kernel_vectors

PRESET_SHORT_NAMES = {
    1: "Canonical Invertible",
    2: "Strict Singularity",
    3: "Even Factor 2",
    4: "Odd Factor 13",
}

st.set_page_config(
    page_title="Secret Code Explorer",
    page_icon="🔐",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #d7dee6;
        border-radius: 8px;
        padding: 12px 16px;
    }
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
        det = matrix_det_mod(case["K"])
        g = int(np.gcd(det, MOD))
        label = f"Preset {case['id']}: {PRESET_SHORT_NAMES[case['id']]} (det={det}, gcd={g})"
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

# ---- Recovery -----------------------------------------------------------

st.subheader("Recovery")

if invertible:
    K_inv = matrix_inverse_mod(K)
    decoded = decode(ciphertext, K)
    st.success(f"Decryption succeeded — recovered plaintext: **{decoded}**")
    st.write("K⁻¹ mod 26 =")
    st.write(K_inv)
else:
    st.error("**SingularKeyError:** Inversion Impossible (gcd(det(K), 26) ≠ 1)")

    v0 = find_nonzero_kernel_vector(K)
    kernel_size = len(kernel_vectors(K))
    st.write(f"**Kernel size** |ker(T)| = {kernel_size}")
    st.write(f"**Null vector** v0 (K·v0 ≡ 0 mod 26): {v0.tolist()}")

    v1 = plain_vectors[0]
    v2 = (v1 + v0) % MOD
    w1 = (K @ v1) % MOD
    w2 = (K @ v2) % MOD
    assert np.array_equal(w1, w2), "sanity check: v1 and v1+v0 must collide"

    d1, d2, c = vectors_to_text([v1]), vectors_to_text([v2]), vectors_to_text([w1])
    st.warning(
        f"**Collision demo:** Digraph 1 (\"{d1}\") and Digraph 2 (\"{d2}\") "
        f"both map to Ciphertext (\"{c}\") — decoding is many-to-one, not just hard."
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
