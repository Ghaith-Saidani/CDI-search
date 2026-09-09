# CDI Application Assistant

Small, local, dependency-free evaluator for French Data/AI CDI job offers. It produces a transparent JSON report using only evidence present in the candidate profile.

## Run

From the repository root, install the local package once:

```powershell
python -m pip install -e .
python -m cdi_assistant.cli --input examples/request.json
cdi-evaluate --input examples/request.json
```

For normal use, keep your verified profile in `data/candidate_profile.json` and provide only the offer:

```powershell
python -m cdi_assistant.cli --job examples/job_offer.json
```

PowerShell note: use `cdi_assistant.cli` exactly as written. Do not add a backslash before the underscore. The `examples/request.json` path is relative to the repository root, so run these commands from `CDI-search`, not `src`.

## Tests

Tests use only Python's standard library:

```powershell
python -m unittest discover -s tests -v
```

## Input

The CLI accepts one JSON object with `candidate` and `job` properties. Start from `examples/candidate.template.json`; populate only facts you can support. `confirmed_skills`, `partial_skills`, years of experience, degree, and languages are all optional, but omitted facts are reported as unknown rather than credited.

`job.technical_requirements` entries have `name` and an optional `importance` (`mandatory`, `preferred`, or `nice_to_have`). `job.languages` maps language names to a requested level such as `B2`, `C1`, or `fluent`.

## Design

The application intentionally has no database, web scraping, or LLM dependency. Its request and response are stable JSON boundaries for a later Excel tracker or LLM enrichment layer. The scoring rules are in one readable module and can be adjusted without changing the CLI or data models.

## Scoring

| Dimension | Maximum |
| --- | ---: |
| Data/AI relevance | 25 |
| Technical match | 25 |
| Experience match | 15 |
| Seniority match | 10 |
| Education match | 10 |
| Location/mobility | 5 |
| Languages/other | 10 |

Data/AI relevance below 15 triggers the hard gate and the final decision is `DO NOT APPLY`, irrespective of the total. Priorities: A (80–100), B (65–79), C (50–64), otherwise SKIP.
