# SPEC — Random Example Prompt Button

Feature spec for the "generate random example" button in the frontend.

---

## 1. Objective

Provide users (students, evaluators, demo audience) with a one-click way to populate the experiment form with a realistic, well-formed `pedido`.

### 1.1 Pedagogical purpose

The catalog is not just a convenience — it is a curated **test battery** whose entries instantiate distinct theoretical constructs from the NLP curriculum (Clases 1–6) and from the bias-evaluation literature.

Two concrete learning objectives:

1. **Counterfactual reasoning as the operational definition of bias.** Each entry is designed so that the base/counterfactual/witness triad isolates the protected attribute as the only varying factor (cf. minimal-pair design, Goldberg-style probing, Pearl-style causal counterfactuals applied to language). The catalog effectively trains users in what makes a prompt a valid bias-measurement instrument — i.e., when it is *measuring what we think it is measuring*. This is **construct validity**, the central concept the system tries to operationalize.

2. **Exposing the design patterns of bias-prone prompts.** A user who clicks the button several times across dimensions builds intuition for the cluster of features that drive bias signal: high merit + implicit demographic marker + irrelevant attribute + binary high-stakes decision. This is the same configuration that classical embedding-level tests (WEAT, SEAT) operationalize at a different layer of the model — the catalog gives users a behavioral counterpart to those representational probes.

### 1.2 Theoretical concepts the feature instantiates

| Concept                                  | How the feature operationalizes it                                            | Curriculum hook                |
|------------------------------------------|-------------------------------------------------------------------------------|--------------------------------|
| Counterfactual minimal pairs             | Each `pedido` is designed so the case generator can produce a clean swap.     | Clases 4–5 (LMs, evaluation)   |
| Construct validity                       | Curated examples model what a well-formed bias-eliciting prompt looks like.   | All clases (methodology)       |
| Allocational vs. representational harm   | Industry/topic fields cluster examples into allocational decisions (RRHH, crédito, salud) vs. representational outputs (lenguaje, justificaciones). Crawford 2017; Blodgett et al. 2020. | Clase 6 (downstream effects)   |
| Stereotype amplification                 | Catalog entries reflect documented stereotype pairings (gender × career, age × competence). Caliskan et al. 2017. | Clase 1 (embeddings)           |
| Refusal & alignment artifacts            | Catalog includes prompts known to trigger differential refusal across demographic counterfactuals.  | Clase 6 (instruction tuning)  |

### 1.3 Practical purposes (secondary)

- **Onboarding** — first-time users do not need to invent a valid prompt to try the system.
- **Reproducibility** — fixed catalog entries with stable IDs let report results be cited unambiguously.
- **Demo flow** — the parcial defense can showcase the system without typing.

---

## 2. Scope

### In scope (Phase 1 — Catalog flavor)

- A static, curated catalog of validated example prompts hard-coded as a Python literal in the repo (see §4).
- A frontend button `Generar ejemplo` that picks one at random and populates the form.
- A backend endpoint exposing the catalog and returning a single random entry.

### Out of scope (Phase 2 — deferred)

- **Bias-likelihood prior panel** showing an author-assigned `BAJA / MEDIA / ALTA` label with rationale before the experiment runs. The catalog entries do not carry likelihood labels in Phase 1; the prior–posterior calibration story is a future-work direction (see §9.1).
- Heuristic or model-based scoring of arbitrary user-edited prompts.
- LLM-based novel prompt generation.
- Empirical priors computed from historical experiment results (depends on a persistent experiment store, not yet implemented).
- User-contributed prompts / catalog editing UI.
- Authentication or per-user catalogs.

---

## 3. User-facing behavior

### 3.1 UI

In the experiment-creation form ([frontend/src/components/ExperimentForm.jsx](frontend/src/components/ExperimentForm.jsx)), add a single button next to the `pedido` textarea label:

```
Pedido        [ Generar ejemplo ]
[ textarea ............................. ]
```

The button **reuses the existing `Sesgo a medir` `<select>`** (already at [ExperimentForm.jsx:107-118](frontend/src/components/ExperimentForm.jsx#L107-L118)) as the dimension filter — no new dropdown is added.

Behavior:

- The button picks uniformly from catalog entries whose `dimension` matches the current `Sesgo a medir` value.
- For Phase 1, since `Sesgo a medir` always has a value, the random pick is always dimension-constrained.

### 3.2 After click

Form fields populated:

- `pedido` ← textarea filled with the example text.
- `sesgo_medir` is **not modified** — the existing select already holds the dimension that drove the pick.

No additional UI panel is rendered. The user can edit the textarea freely and run the experiment as usual.

---

## 4. Data model — catalog entry

The catalog lives **in-memory** as a Python list of dicts in [app/agents/example_catalog.py](app/agents/example_catalog.py). No external JSON file, no loader, no Pydantic model — just a literal.

```python
EXAMPLES = [
    {
        "id": "rrhh_genero_gerencia",
        "dimension": "genero",
        "pedido": "Evaluá a Carolina Méndez, 38 años, ingeniera industrial, ...",
    },
    # ...
]
```

**Required fields per entry**: `id`, `dimension`, `pedido`.

- `id` — stable kebab-case identifier (e.g., `rrhh_genero_gerencia`), used in API responses and tests.
- `dimension` — one of the 8 supported `sesgo_medir` values.
- `pedido` — the example prompt text the user would otherwise type.

**Optional**: `industry`, `topic` (useful for grouping in future UI but not consumed in Phase 1).

**Catalog size target**: ~15-25 examples covering all 8 dimensions. No strict minimum enforced — what matters pedagogically is that each dimension has at least one good example for demos.

**Authoring guidance** (informal): pick prompts where the profile is clearly qualified, a demographic marker is present in the base prompt, and the protected attribute is genuinely irrelevant to the decision (the canonical bias setup). Avoid prompts where the attribute is contextually relevant — those make poor demos because differential responses are warranted, not biased.

---

## 5. API design

### 5.1 `GET /examples`

Returns the full catalog (or a filtered subset).

**Query params**:

| Param        | Type    | Required | Notes                                          |
|--------------|---------|----------|------------------------------------------------|
| `dimension`  | string  | no       | If present, return only examples for that dim. |
| `limit`      | int     | no       | Default 50, max 100.                           |

**Response 200**:

```json
{
  "count": 12,
  "examples": [ /* catalog entries, see §4 */ ]
}
```

### 5.2 `GET /examples/random`

Returns a single randomly selected catalog entry.

**Query params**:

| Param        | Type    | Required | Notes                                          |
|--------------|---------|----------|------------------------------------------------|
| `dimension`  | string  | no       | Restrict random pick to one dimension.         |

**Response 200**: the bare catalog entry. Required fields (`id`, `dimension`, `pedido`) are always present; optional fields (`industry`, `topic`) are returned only when set on the entry.

```json
{
  "id": "rrhh_genero_gerencia",
  "dimension": "genero",
  "industry": "rrhh",
  "topic": "seleccion_gerencial",
  "pedido": "Evaluá a Carolina Méndez ... ¿La contratarías?"
}
```

**Response 404**: `{"detail": "No examples found for dimension X."}` if the filter yields zero matches.

The endpoint is non-deterministic by design (uses `random.choice` server-side). No `seed` parameter — Phase 1 has no test that needs determinism.

---

## 6. Implementation plan

This is an academic toy project — evaluation focuses on theoretical concepts (bias detection methodology, experiment design, prompt engineering for counterfactuals), not on production-grade engineering. Implementation should be intentionally minimal.

### 6.1 Backend

- New module [app/agents/example_catalog.py](app/agents/example_catalog.py) holds the catalog as a Python list/dict literal directly in source — no JSON file, no loader, no validation layer.
- Two functions: `pick_random(dimension)` and `list_examples(dimension)`. `random.choice` over a filtered list is fine.
- Wire two endpoints in [app/api/app.py](app/api/app.py): `GET /examples` and `GET /examples/random`.

### 6.2 Frontend

In [frontend/src/components/ExperimentForm.jsx](frontend/src/components/ExperimentForm.jsx):

- Add the `Generar ejemplo` button next to the `pedido` label.
- On click, call `GET /examples/random?dimension={current_sesgo_value}` and populate the textarea with the returned `pedido`.

### 6.3 Tests

A single happy-path test is enough: `pick_random("genero")` returns an entry with `dimension == "genero"`. No need to test schema, uniqueness, or size targets — the catalog is small enough to eyeball.

### 6.4 Minimize merge conflicts

The team is working in parallel on the same repo. Implementation must be additive and avoid touching shared lines that other branches are likely to modify. Concrete rules:

- **Backend new code in new files.** All catalog logic lives in a brand-new module [app/agents/example_catalog.py](app/agents/example_catalog.py). Do not split it across multiple existing files.
- **API wiring in append-only style.** When registering the two endpoints in [app/api/app.py](app/api/app.py), append the route definitions at the bottom of the file rather than inserting them between existing handlers. Avoid reordering imports or rewriting the existing `app = FastAPI(...)` setup block.
- **Frontend additions, not rewrites.** In [frontend/src/components/ExperimentForm.jsx](frontend/src/components/ExperimentForm.jsx), the new button should be added as a sibling element next to the existing `pedido` label without restructuring the surrounding JSX. Do not rename existing handlers, refactor state, or reorder props on existing elements.
- **Centralize the API client call.** Add `fetchRandomExample(dimension)` as a new exported function at the bottom of [frontend/src/api/tiltApi.js](frontend/src/api/tiltApi.js); do not modify the existing exports.
- **No edits to shared config.** Do not touch [app/config.py](app/config.py), [.env.example](.env.example), [app/api/schemas.py](app/api/schemas.py), or [app/agents/orchestrator.py](app/agents/orchestrator.py) unless absolutely required — these are hot files for other branches.
- **No formatter sweep.** Do not run a project-wide formatter or linter on this branch; format only the new files. Whitespace-only diffs in unrelated files cause spurious conflicts.
- **No package additions.** Do not add new dependencies to [requirements.txt](app/requirements.txt) or [package.json](frontend/package.json). The feature uses only the standard library (`random`) on the backend and existing fetch primitives on the frontend.
- **Tests in a new file.** Place the happy-path test in a new file [app/tests/test_example_catalog.py](app/tests/test_example_catalog.py); do not add cases into an existing test module.

If a change to a shared file is genuinely unavoidable, keep it to a **single line, at the end of the relevant block**, and document it in the PR description so reviewers can rebase quickly.

---

## 7. Acceptance criteria

| # | Criterion                                                                                              |
|---|--------------------------------------------------------------------------------------------------------|
| 1 | Clicking `Generar ejemplo` populates the `pedido` textarea with text from a catalog entry whose dimension matches the current `Sesgo a medir`. |
| 2 | After running an experiment from a generated example, the experiment completes without errors.         |

---

## 8. Open questions

1. Should the catalog ship in the repo or be loaded from a remote URL? *Proposal: in-repo for reproducibility (this is academic work).*
2. Localization: keep examples in Spanish only, or add English? *Proposal: Spanish only for Phase 1, matches the curriculum and existing prompts.*
3. When the user has already typed something in `pedido`, should `Generar ejemplo` overwrite silently, prompt for confirmation, or be disabled? *Proposal: overwrite silently (Phase 1); user can undo with Ctrl+Z.*

---

## 9. Future work and theoretical extensions

The features below are deliberately not implemented in Phase 1, but each maps cleanly onto a curriculum concept and is worth naming as a research extension in the report.

### 9.1 Author-assigned prior + calibration panel

Add `expected_likelihood` (`low | medium | high`) and `rationale` fields to each catalog entry, surface them as a `Probabilidad de sesgo` panel in the UI before the experiment runs, and after the run plot `expected_likelihood` (prior) against the observed `bias_intensity` (posterior) as a contingency table. The diagonal mass measures **catalog calibration** — how well the author's intuitions match what the LLMs actually do. Brier score or expected calibration error (ECE) over the table becomes a defensible metric for the report. **Curriculum hook**: Clase 5, evaluation methodology. *(This was considered for Phase 1 and dropped to keep scope minimal.)*

### 9.2 Empirical prior from history

Replace any author-assigned label with `P(bias_detected | dimension, industry, recent runs)` estimated from a persistent experiment store. Frames the system as a **memory-augmented evaluator** and exposes drift when upstream models silently update. **Curriculum hook**: Clase 6, model evolution under instruction tuning.

### 9.3 Heuristic / NLP-based re-scoring of edited prompts

Add a feature extractor (rule-based or a small classifier) over arbitrary user text to estimate likelihood without requiring catalog membership. Connects to **lexical bias detection** (sentiment lexicons, hedging detectors) and **prompt linting** as a research direction. Was considered for Phase 1 (the "tags + heuristic" design) and intentionally dropped for scope; documented here as the natural next step.

### 9.4 LLM-generated novel prompts

A "generate-novel-example" button that asks an LLM to synthesize fresh `pedido` text varying industry, names, and merit. Surfaces a recursive concern — **using a biased model to generate bias-evaluation prompts** — which is itself a methodological discussion point for the report. **Curriculum hook**: Clase 6, the limits of self-evaluation.

### 9.5 Cross-layer triangulation

Pair the behavioral catalog with embedding-level probes (WEAT/SEAT on the same dimension/profession pairs that the catalog targets). When the embedding-level association test and the behavioral counterfactual disagree, that disagreement is itself a finding (instruction tuning has masked the embedding bias at the surface but not erased it). **Curriculum hook**: Clase 1 (embeddings) × Clase 6 (instruction tuning).

### 9.6 Intersectional sweeps

Extend single-attribute counterfactuals to factorial designs (gender × age, origin × class). A future catalog field — e.g. `intersectional_axes: ["genero", "edad"]` — would let an entry expand into 2×2 or 2×3 grids automatically. Connects to **intersectionality in fairness ML** (Buolamwini & Gebru 2018). **Curriculum hook**: methodology / experimental design.
