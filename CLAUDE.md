# CLAUDE.md — Secret Code with Linear Transformations

**MAT-208: Vector Spaces | Competency MAT-208:00020 (Determining Basic Matrices of Linear Transformations)**
**Project #2 of 10 — Secret Code with Linear Transformations**

> This file is the single source of truth for the repository. Every team member — and Claude Code, when reevaluating the project — should read it before writing code or report sections. If scope, team size, or requirements change, update this file first.

---

## 0. Project Registration Info

| Field | Value |
| --- | --- |
| Course | MAT-208: Vector Spaces |
| Project | #2 — Secret Code with Linear Transformations |
| Team size | 5 (scales cleanly to 6 if a member joins — see §5 for the 6-person variant; 7 requires instructor pre-approval per course policy) |
| Timeline | 7 days |
| Instructor | Dr. Pitikhate |
| Deliverables | (1) Written report, 5–8 pages, (2) Demonstration/output (interactive Python tool), (3) Group presentation, 10–15 min |
| Rubric total | 100 points — Math Understanding 30, Creativity & Application 20, Demonstration & Visualization 20, Collaboration 10, Report Quality 10, Presentation 10 |

**Academic integrity note**: External tools (including AI assistance) may be used, but all methods and sources must be acknowledged per course policy. Include a brief "Tools & Acknowledgments" note in the report.

---

## 1. File Manifest (for Claude Code re-evaluation)

Fill in the actual path as each file is created. Claude Code should read this table first and re-check the listed files against the specs in this document before making further changes — treat a blank "Path" cell as "not yet created."

| Artifact | Description | Path |
| --- | --- | --- |
| Core cipher module | Encode/decode functions, modular inverse logic (§4.2) | `src/cipher_tools.py` (renamed from `cipher-tools.py` — a hyphen is not valid in a Python `import` statement) |
| CLI / interactive key tester | Interactive testing loop (§4.2), also scriptable via `--message`/`--key` flags | `src/terminal_tools.py` |
| Visualization script | Standardized 4-case evaluation suite (§4.2, `--batch` / default): `figures/case1_invertible_scatter.png` (det=9, bijective scatter) + `figures/case1_invertible_heatmap.png` (same key, \|ker\|=1 heatmap baseline), `figures/case2_singular_det0.png` (det=0, \|ker\|=26), `figures/case3_singular_factor2.png` (det=24, gcd=2, \|ker\|=2), `figures/case4_singular_factor13.png` (det=13, gcd=13, \|ker\|=13). All numerically verified against \|ker T\|=gcd(det K,26) and \|Im T\|=676/\|ker T\|. Single-key mode (`--invertible-key`/`--singular-key`/`--out`) still available for ad hoc keys | `src/visualize.py` |
| Test / verification script | Unit tests (unittest, 15 cases) checking §2–3 worked examples: modular inverse, K·K⁻¹=I, encode/decode round trip, linearity axiom, singular-key collision, known-plaintext attack recovery | `src/test_verify.py` (renamed from `test-verify.py` — same hyphen-import issue) |
| Live-demo GUI | PySide6 desktop app for the presentation: message + key-matrix entry, the 4 preset evaluation cases, a "Run Transformation" button (plots render on demand, not per-keystroke), a text report pane, and the same scatter/heatmap plots embedded live via `FigureCanvasQTAgg`. Shares `cipher_tools.evaluate_key` and `visualize.draw_bijective_scatter`/`draw_heatmap` — no logic duplicated across CLI, batch script, and GUI | `src/gui_app.py` |
| Written report (source) | Markdown/LaTeX/Word source for the 5–8 page report | N/A |
| Written report (final PDF) | Final exported report for submission | N/A |
| Presentation slides | Slide deck source/export | N/A |
| Demo recording (backup) | Recorded fallback for the live demo | N/A |
| Sample encoded/decoded output | Example run output used in the report's Results section | N/A |

**Environment note**: the system default `python3` on at least one dev machine is a 3.15 beta with no matplotlib/PySide6 wheels yet (build from source fails, e.g. matplotlib's `freetype` download). `visualize.py` and `gui_app.py` need matplotlib (and `gui_app.py` also needs PySide6), so run both from a stable-Python venv, e.g.:

```bash
python3.12 -m venv .venv && source .venv/bin/activate && pip install numpy matplotlib PySide6
```

`cipher_tools.py`, `terminal_tools.py`, and `test_verify.py` only need numpy and are unaffected. Launch the GUI with `python3 src/gui_app.py` (from inside the venv).
| Lecture note | Lecture note for MAT-208 | `Week 4-5 Linear Transformation.pdf` & `Week 2-3 Basic Vector and Matrix Operations.pdf` |

**Instructions for updating this table**: whenever a team member creates or moves a file that this project depends on, add/update its row here in the same commit or session. This keeps Claude Code (or any collaborator) able to locate and re-validate the current state of the repo without guessing paths.

---

## 2. Mathematical Framework & Modulo 26 Specification

**Scope confirmation — this supersedes any earlier real-valued (ℝ²) framing. The cipher operates over ℤ₂₆, not ℝ².** Ciphertext characters are recoverable letters (mod 26), not arbitrary real numbers — this is what makes the "actual encoded and decoded messages" deliverable possible.

### 2.1 Algebraic Structure & Mapping

- **Block size**: n = 2 (pairs of letters / digraphs).
- **Character encoding**: standard 0-indexed mapping:
  $$A = 0,\; B = 1,\; C = 2,\; \dots,\; Z = 25$$
- **Vector representation**: a plaintext pair $P_1P_2$ maps to a column vector $v \in \mathbb{Z}_{26}^2$:
  $$v = \begin{bmatrix} p_1 \\ p_2 \end{bmatrix}, \quad p_1, p_2 \in \{0, 1, \dots, 25\}$$
- **Algebraic foundation (report rigor note)**:
  - Because 26 = 2 × 13 is composite, $\mathbb{Z}_{26}$ is a commutative **ring**, not a field — it has zero-divisors (e.g. $2 \times 13 \equiv 0 \pmod{26}$).
  - $\mathbb{Z}_{26}^2$ is technically a **free module** over the ring $\mathbb{Z}_{26}$, not a vector space in the strict sense. Consequently, standard field-style invertibility (det(K) ≠ 0) is **insufficient**: invertibility strictly requires $\gcd(\det(K), 26) = 1$.
  - **Linearity still holds**: the map $T(v) = Kv \pmod{26}$ still satisfies $T(au + bv) = aT(u) + bT(v)$ for scalars $a, b \in \mathbb{Z}_{26}$ — this axiom transfers from the vector-space case cleanly and should still be demonstrated concretely in the report with your chosen key. What changes is only the invertibility criterion.
  - **Rank-Nullity caveat**: the classical Rank-Nullity Theorem is stated for vector spaces over a field. Over the ring $\mathbb{Z}_{26}$, the module-theoretic analogue holds informally (a non-injective map has a non-trivial kernel), which is exactly what §2.4 needs — but note in the report that this is an analogous, not identical, statement, since $\mathbb{Z}_{26}$ is not a field.

### 2.2 Forward Transformation (Encryption)

Given a 2×2 key matrix $K = \begin{bmatrix} a & b \\ c & d \end{bmatrix}$ with $a, b, c, d \in \mathbb{Z}_{26}$:

$$w = Kv \pmod{26} = \begin{bmatrix} (a \cdot p_1 + b \cdot p_2) \bmod 26 \\ (c \cdot p_1 + d \cdot p_2) \bmod 26 \end{bmatrix}$$

The resulting coordinate vector $w = \begin{bmatrix} c_1 \\ c_2 \end{bmatrix}$ maps back to the ciphertext character pair $C_1C_2$.

### 2.3 Backward Transformation (Decryption)

Decryption applies the modular inverse matrix $K^{-1} \pmod{26}$:

$$v = K^{-1}w \pmod{26}$$

Computed via the modular adjugate formula:

$$K^{-1} \equiv (\det K)^{-1} \cdot \operatorname{adj}(K) \pmod{26}$$

$$\operatorname{adj}(K) = \begin{bmatrix} d & -b \\ -c & a \end{bmatrix} \equiv \begin{bmatrix} d & 26-b \\ 26-c & a \end{bmatrix} \pmod{26}$$

- **Determinant**: $\det(K) = (ad - bc) \bmod 26$.
- **Modular multiplicative inverse**: $(\det K)^{-1}$ is the unique integer $x \in \{1, 3, 5, \dots, 25\}$ satisfying $\det(K) \cdot x \equiv 1 \pmod{26}$, computed via the Extended Euclidean Algorithm.

**Worked example to include in the report**: pick a specific invertible key (e.g. $K = \begin{bmatrix} 3 & 3 \\ 2 & 5 \end{bmatrix}$, $\det K = 9$, $\gcd(9,26)=1$), hand-compute $(\det K)^{-1} \bmod 26$ via the Extended Euclidean Algorithm, build $K^{-1} \bmod 26$, and verify $K K^{-1} \equiv I \pmod{26}$ numerically.

### 2.4 Failure Analysis: Singular and Non-Coprime Keys

A key matrix $K$ fails and causes unrecoverable decoding if either:

1. **Zero determinant**: $\det(K) \equiv 0 \pmod{26}$, or
2. **Shared factors**: $\gcd(\det(K), 26) \in \{2, 13, 26\}$.

**Mathematical justification (rubric focus):**

- In either failure condition, $(\det K)^{-1} \pmod{26}$ does not exist.
- **Loss of injectivity / non-trivial kernel**: the map has a non-trivial null space — there exists a nonzero vector $v_0 \in \mathbb{Z}_{26}^2 \setminus \{\mathbf{0}\}$ such that
  $$Kv_0 \equiv \begin{bmatrix} 0 \\ 0 \end{bmatrix} \pmod{26}$$
- Consequently, distinct plaintext vectors $v_1$ and $v_2 = v_1 + v_0$ map to the **exact same ciphertext**:
  $$Kv_2 = K(v_1 + v_0) \equiv Kv_1 + Kv_0 \equiv Kv_1 \pmod{26}$$
- Decoding is mathematically impossible because the transformation is many-to-one — information is destroyed, not just "hard to reverse."

**Worked example to include**: pick a specific key with $\gcd(\det K, 26) \neq 1$ (e.g. $\det K \equiv 13 \pmod{26}$), find a nonzero $v_0$ with $Kv_0 \equiv 0$, and show two distinct plaintext digraphs colliding to the identical ciphertext under this key. A concrete numeric collision is worth more rubric credit than the abstract argument alone.

### 2.5 Cryptanalysis: Known-Plaintext Attack

The cipher is vulnerable to elementary linear algebra. An eavesdropper who intercepts two distinct plaintext/ciphertext vector pairs $(v_1, w_1)$ and $(v_2, w_2)$ forms:

$$W \equiv K \cdot P \pmod{26}, \quad P = [v_1 \mid v_2],\ \ W = [w_1 \mid w_2]$$

If $P$ is invertible mod 26 (i.e. $\gcd(\det P, 26) = 1$), the secret key is recovered directly:

$$K \equiv W \cdot P^{-1} \pmod{26}$$

**Report framing**: present this as a real vulnerability of any cipher whose encoding function is linear — no brute force is needed, just two known plaintext/ciphertext pairs and modular linear algebra. Briefly contrast with why modern ciphers use nonlinear components (S-boxes, etc.) specifically to resist this style of attack. Two or three sentences of this framing meaningfully strengthens the Creativity & Application score.

---

## 3. Deliverables & Technical Specs

### 3.1 Written Report Outline (5–8 pages)

| Section | Content | Approx. length |
| --- | --- | --- |
| Title page | Group name, all member names + student IDs, project title (per course formatting requirement) | — |
| 1. Introduction | The problem: how do you send a message so only someone with the right key can read it? Frame via linear transformations. State scope: $\mathbb{Z}_{26}^2$, block size 2, mod-26 arithmetic. | 0.5–1 page |
| 2. Mathematical Background | §2.1–2.3 content: ring vs. field distinction, linearity, modular invertibility criterion, adjugate/modular-inverse formula, worked with your actual key matrix | 1.5–2 pages |
| 3. Methodology | Letter↔$\mathbb{Z}_{26}$ encoding scheme, choice of key matrix K, encode/decode pipeline (text → digraph vectors → Kv mod 26 → ciphertext letters → transmission → K⁻¹w mod 26 → text), tools used (Python/NumPy/Matplotlib) | 1–1.5 pages |
| 4. Results | Worked encode/decode example with a real message and real letter output; the two comparison plots (§3.2); the singular-key collision example from §2.4; known-plaintext attack demo from §2.5 | 1.5–2 pages |
| 5. Conclusion & Reflection | What the non-trivial kernel geometrically/algebraically means for this application; real-world cryptographic weaknesses of linear ciphers; what the team learned; individual reflections (optional, 1–2 sentences each, supports Collaboration score) | 0.5–1 page |

Figures/diagrams must be numbered and labeled per course formatting requirements. Include a brief "Tools & Acknowledgments" line noting AI or software assistance used, per academic integrity policy.

### 3.2 Visualization Tool Spec (Python: NumPy + Matplotlib)

Standalone script, suggested filename `cipher_tool.py` (record its actual path in §1 once created). Required capabilities:

1. **Encoding function** `encode(message: str, K: np.ndarray) -> str`
   - Converts message to digraph vectors per the fixed 0-indexed letter mapping (§2.1). Pad odd-length messages with a filler character (document the choice, e.g. `'X'`).
   - Applies `(K @ v) % 26` to each vector, maps results back to letters, returns the ciphertext string.
2. **Decoding function** `decode(ciphertext: str, K: np.ndarray) -> str`
   - Computes $\det(K) \bmod 26$ and checks $\gcd(\det K, 26) = 1$ before attempting inversion.
   - If coprime: compute the modular inverse of the determinant via the Extended Euclidean Algorithm (implement directly — do not rely on floating-point `np.linalg.inv`, which is real-valued and wrong here), build $K^{-1} \bmod 26$ via the modular adjugate formula, apply to each ciphertext vector, map back to letters.
   - If not coprime: raise a clear, custom exception (e.g. `SingularKeyError`) rather than silently producing garbage — this exception is your live proof of §2.4.
3. **Interactive key testing**
   - CLI or input-prompt loop: user enters a message and 4 matrix entries (a, b, c, d); script reports $\det(K) \bmod 26$, $\gcd(\det K, 26)$, whether K is invertible mod 26, and runs a full encode→decode round-trip if invertible.
   - If not invertible, the script should still perform encoding and show the ciphertext, then explicitly report *why* decoding cannot proceed: print $\gcd(\det K, 26)$ and a computed nonzero null vector $v_0$ (search $\{0,\dots,25\}^2$ directly — the space is small enough to brute-force $Kv_0 \equiv 0 \pmod{26}$).
4. **Automated comparison plots** (generate both every run, save as PNG). Because the cipher is discrete (mod 26), these are scatter plots over the lattice $\{0,\dots,25\}^2$, not continuous grid deformations:
   - **(a) Invertible key — bijective scatter**: plot all 676 points of $\{0,\dots,25\}^2$ (or a representative subsample if 676 is too dense to read, e.g. every 2nd point) as inputs; plot their images under $Kv \bmod 26$ as outputs, side by side. For an invertible K, every output point should be **hit exactly once** — annotate this (e.g. title: "each of 676 points maps to a unique point — bijective"). A useful supplementary check: color each point by its distance from the origin in the input plot, and confirm the same color pattern appears as a permuted scatter in the output plot.
   - **(b) Singular/non-coprime key — collision heatmap**: same input lattice, mapped through a singular or non-coprime K. Because the map is many-to-one, multiple input points collapse onto the same output point. Visualize this as a **hit-count heatmap** over the 26×26 output grid (color intensity = number of input points mapping to that output cell) — cells with count > 1 should be visually obvious. Annotate the specific collision from §2.4's worked example (e.g. mark $v_1$ and $v_1+v_0$ both landing on the same output cell).
   - **Optional supplementary visual (not the primary demo)**: a continuous, real-valued (non-modular) unit-square deformation plot can still be included as a *geometric intuition aid* alongside the mod-26 plots — clearly labeled as an illustrative analogy, not the actual cipher behavior, since the real cipher never leaves $\mathbb{Z}_{26}$.

**Stretch goal (if time allows)**: wrap the interactive key-testing loop in a minimal GUI (e.g. `matplotlib` widgets/sliders for the four integer matrix entries, clamped to $\{0,\dots,25\}$, with a live-updating output scatter/heatmap) — this converts a script into a genuinely interactive demo and is the single highest-leverage addition for the Demonstration & Visualization score.

### 3.3 Team Workflow — 5-Person, 7-Day Breakdown

**Roles:**

- **Person A — Math Lead**: owns §2 theoretical write-up, worked examples (invertible key, singular-key collision, known-plaintext attack), verification of all hand computations.
- **Person B — Implementation Lead**: owns `encode`/`decode`, the Extended Euclidean modular-inverse logic, and the interactive key-testing loop.
- **Person C — Visualization Lead**: owns the bijective-scatter and collision-heatmap plots and (if pursued) the GUI stretch goal.
- **Person D — Report & Editing Lead**: owns document structure, formatting, figure labeling, integration of all sections.
- **Person E — Presentation & Demo Lead**: owns slides, speaker script, rehearsal coordination, and a recorded demo backup.

Everyone contributes math content and reviews the final report regardless of role — this protects the Collaboration score.

| Day | Focus | Whole-team task |
| --- | --- | --- |
| 1 (Mon) | Confirm message + key matrices (one invertible mod 26, one with $\gcd(\det K,26)\neq 1$); assign roles; outline report | Read §2 of this file together |
| 2 (Tue) | B starts `encode`/`decode` + modular inverse logic; A drafts theory section with worked examples; C researches the scatter/heatmap plotting approach | Agree on the specific singular-key collision example from §2.4 |
| 3 (Wed) | B finishes core functions incl. `SingularKeyError` handling; C builds the bijective-scatter plot | D sets up shared report document with section headers from §3.1 |
| 4 (Thu) | C finishes the collision heatmap; A finishes math writeup; D drafts Introduction/Methodology | Full team dry-run of the script together |
| 5 (Fri) | D integrates all sections into full draft; E starts slides + script | Everyone proofreads their own section; a second person independently re-derives all math |
| 6 (Sat) | E finalizes slides and speaker assignments; first full rehearsal | Full team rehearsal + feedback round |
| 7 (Sun) | Final polish: report formatting, demo backup recording, final rehearsal, submission | Submit report + presentation file |

**6-person variant** (if a member joins): split Implementation into "Encode/Decode + Modular Inverse Logic" and "Interactive Key Testing / GUI stretch goal" as two roles, or add a dedicated "QA/Verification" role that independently re-derives every hand computation in §2 before submission — this directly strengthens the Math Understanding score.

### 3.4 Presentation Narrative (10–15 min, 5 speakers)

| Speaker | Time | Content | Verbal transition in |
| --- | --- | --- | --- |
| 1 | 2 min | Hook: "How do you send a message so only the right person can read it?" Real-world framing (historical + modern ciphers, note this is a Hill-cipher-style construction). Introduce linear transformations as the encoding mechanism. State scope: $\mathbb{Z}_{26}^2$, block size 2, modular arithmetic. | "To understand how this works mathematically, [Speaker 2] will walk through the linear algebra behind it." |
| 2 | 2–3 min | Math foundation: $T(v) = Kv \bmod 26$, why $\mathbb{Z}_{26}$ is a ring not a field, why invertibility needs $\gcd(\det K, 26)=1$ (not just $\det K \neq 0$), the modular adjugate formula. | "Now that we know what makes a key invertible mod 26, let's see the actual cipher in action — [Speaker 3]." |
| 3 | 3 min | Live demo: run `cipher_tool.py`, encode a real message with the invertible key, show the bijective-scatter plot, decode back to the original message letters. (Have the recorded backup cued in case of live failure.) | "That's what happens when the key is invertible mod 26. [Speaker 4] will show you what happens when it isn't." |
| 4 | 2–3 min | The singular/non-coprime failure case: same message, a key with $\gcd(\det K,26)\neq 1$. Show the ciphertext still gets produced, but decode raises `SingularKeyError`. Show the collision heatmap and connect it to the non-trivial kernel argument from §2.4. | "This isn't just a coding error — it's a real vulnerability, and [Speaker 5] will close by talking about what that means for cryptography." |
| 5 | 2 min | Known-plaintext attack (§2.5) as the "so what": linear ciphers are breakable with just two plaintext/ciphertext pairs. Reflection on what the team learned. Close by tying back to the opening hook. | (closing) |

Practice explicit handoffs (as scripted above) — visible, verbal transitions between speakers are an easy way to raise the Presentation score's "engages the audience" and balanced-participation criteria.

---

## 4. Open Items / Change Log

- **[Resolved]** Course instructions specify groups of 6–7; team has confirmed 5–6 is acceptable, with 7 requiring pre-approval from Dr. Pitikhate.
- **[Resolved — supersedes earlier version]** Original draft used a real-valued $\mathbb{R}^2$ framework with no modular arithmetic. This has been replaced throughout with the $\mathbb{Z}_{26}^2$ modular (Hill-cipher-style) framework so that encoded/decoded output is actual recoverable text, per the team's clarified requirement. All math (§2), the tool spec (§3.2), and the presentation script (§3.4) now reflect mod 26 exclusively; the old $\mathbb{R}^2$ grid-deformation visual is retained only as an optional, clearly-labeled supplementary intuition aid, not the primary demo.
- If the chosen key matrices, message, or scope change again, update §2–3 of this file *before* continuing implementation or report writing, so the math, code, visualizations, and presentation script stay in sync. Also update §1's File Manifest whenever files are created or moved.
