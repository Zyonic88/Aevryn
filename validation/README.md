# SceneSmith Validation Corpus

The validation corpus stores regression case definitions for local story chapters.

It does not store copyrighted chapter text.

## Purpose

The validation suite exists to prove that SceneSmith remains stable across genres as
the V1 engines are hardened.

Each case checks:

* Chapter file count
* Ordered source file manifest
* Story Import structure
* Chapter count
* Scene count
* Paragraph count
* Sentence count
* Evidence anchor count
* Deterministic repeated import structure
* Imported structure digest

Future V1 checks can add Canon, Timeline, Character, World, Scene, Prompt,
Presentation, and Export expectations without copying source chapters into the repo.

Each case also checks extraction readiness:

* Scene input count
* Evidence anchor count
* Evidence-bounded extraction input digest
* Evidence-bounded extraction prompt digest

The extraction input digest is built from scene IDs, hashed scene text, evidence
anchor IDs, and hashed evidence quotes. It proves that Story Import can feed the
Entity Extraction boundary deterministically without storing chapter text.

The extraction prompt digest is built from the actual evidence-bounded prompt
text that would be sent to an AI extraction client. It catches prompt-builder
drift without storing prompts or chapter text.

## Source Chapters

By default, the CLI looks for local chapters at:

```text
~/Desktop/SceneSmith test chapters
```

Override the source root with either:

```powershell
$env:SCENESMITH_VALIDATION_ROOT = "C:\path\to\chapters"
```

or:

```powershell
scenesmith validate --source-root "C:\path\to\chapters"
```

`--source-root` takes priority over `SCENESMITH_VALIDATION_ROOT`.

`SCENESMITH_VALIDATION_ROOT` must not be blank.

## Running

```powershell
scenesmith validate
```

or from a source checkout:

```powershell
python -m scenesmith.cli validate
```

The command prints one result per case plus suite-level totals and a suite digest:

```text
Validation Totals
cases=7 passed=7 failed=0 files=70 chapters=70 scenes=70 paragraphs=1971 sentences=7578 anchors=7578 extraction_inputs=70 extraction_anchors=7578

Validation Digest
816f6226832fe56ccdddc4064630807d31dd3646d4ec4573fde1450d0c2a3aad
```

For quick repeat checks, suppress per-case output:

```powershell
scenesmith validate --summary-only
```

## Writing Snapshots

Save deterministic validation metadata for future comparison:

```powershell
scenesmith validate --summary-only --snapshot-dir snapshots/validation_v1_rc1
```

Snapshot directories must be empty or absent. SceneSmith refuses to overwrite a
non-empty snapshot directory.

Validation snapshots contain metrics, digests, and result metadata. They do not
store chapter text or extraction prompt bodies.

`validation_result.json` uses the same deterministic JSON as
`scenesmith validate --format json`.

Snapshots are only valid for actual validation runs. `--snapshot-dir` cannot be
combined with `--list-cases`.

The snapshot path must be a directory path, not a file path.

## Listing Cases

List available case IDs without importing chapter files:

```powershell
scenesmith validate --list-cases
```

Machine-readable case listing:

```powershell
scenesmith validate --list-cases --format json
```

## Focused Runs

Run one case:

```powershell
scenesmith validate --case-id adventure_starfleet
```

Run multiple selected cases:

```powershell
scenesmith validate --case-id adventure_starfleet --case-id mystery_super_dimensional_wizard
```

Unknown case IDs fail loudly.

## JSON Output

Validation can emit machine-readable results:

```powershell
scenesmith validate --format json
```

If validation fails, JSON is still printed to stdout and the command exits with a
nonzero status.

## Case File Rules

Each case file must follow these rules:

* The filename must match `case_id`.
* The JSON root must be an object.
* Duplicate JSON object keys are rejected.
* `chapter_glob` must be filename-only, such as `*.txt`.
* Case JSON rejects unsupported top-level fields.
* `expected_import` rejects unsupported metric fields.
* `expected_extraction` rejects unsupported metric fields.
* `expected_import` and `expected_extraction` must be JSON objects.
* Count metrics must be integers, not booleans or strings.
* Paths must remain relative to the configured validation source root.
* Case paths must be JSON files.
* Source paths must be directories.
* Matched chapter paths must be files.
* Matched chapter files must not be blank.
* Checked-in case JSON must use canonical two-space formatting.
* Checked-in V1 cases use `*.txt` and 10 chapter files per genre.
* Case IDs, genres, and source directories must be unique.

Example:

```text
validation/cases/adventure_starfleet.json
```

must contain:

```json
{
  "case_id": "adventure_starfleet"
}
```

## Rule

Validation cases may store metadata and expected metrics.

Validation cases must not store raw chapter text, republished chapters, generated
chapter dumps, or copyrighted source content.

The `source_manifest_digest` is a SHA-256 digest built from ordered source file
names and file content hashes. It lets the validation suite detect wrong,
renamed, reordered, or changed local chapter files without storing the source
text itself.

The `import_digest` is a SHA-256 digest built from stable imported IDs and
hashes of sentence/anchor text. It lets the validation suite detect parsing drift
without storing the source text itself.

The `extraction_input_digest` is a SHA-256 digest built from extraction-ready
scene inputs and evidence anchors. It lets the validation suite detect drift
between Story Import and Entity Extraction without storing source text.

The `extraction_prompt_digest` is a SHA-256 digest built from generated
evidence-bounded extraction prompts. It lets the validation suite detect prompt
format drift without storing source text or prompts.
