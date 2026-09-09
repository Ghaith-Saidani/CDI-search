# CDI Application Assistant

Decision-support system for managing a France-wide Data/AI CDI search, from job discovery and normalization to candidate matching and application follow-up.

## Current capabilities

- Transparent 100-point job-offer evaluator.
- Candidate profile with evidence-aware technical matching.
- France-wide Data/AI search-query portfolio covering 11 target role families.
- Pluggable `JobSource` interface for job providers.
- France Travail Offers API adapter using OAuth2 client credentials.
- Normalized `JobDiscovery` records with source IDs, dates, descriptions, contract, remote, salary, experience and skills.
- SQLite persistence with deterministic upserts and source-level deduplication.
- Discovery orchestration across multiple providers.
- Direct conversion of discovered offers into the existing candidate-matching engine.
- Ranked shortlist output with score, priority, decision, role family, strengths, gaps, red flags and recommended CV.

The system is deliberately designed so providers can be added without changing the matching logic.

## Run the evaluator

From the repository root:

```powershell
python -m pip install -e .
python -m cdi_assistant.cli --input examples/request.json
cdi-evaluate --input examples/request.json
```

For normal use, keep your verified profile in `data/candidate_profile.json` and provide only the offer:

```powershell
python -m cdi_assistant.cli --job examples/job_offer.json
```

## Run job discovery

The first live provider is France Travail. API credentials are intentionally supplied through environment variables rather than committed to the repository:

```powershell
$env:FRANCE_TRAVAIL_CLIENT_ID = "your-client-id"
$env:FRANCE_TRAVAIL_CLIENT_SECRET = "your-client-secret"

python -m cdi_assistant.discovery_cli --source france-travail
```

The command generates the configured search portfolio, queries the provider, deduplicates the results and stores them in `data/jobs.db`.

For a small smoke run:

```powershell
python -m cdi_assistant.discovery_cli --source france-travail --max-queries 2
```

## Discover + match + rank

Use `--match` to send the newly discovered offers directly through the existing 100-point evaluator:

```powershell
python -m cdi_assistant.discovery_cli --source france-travail --match --top 20
```

The command uses `data/candidate_profile.json` by default. You can provide another verified profile with `--profile` and another database with `--db`.

The ranked output contains:

- match score and priority;
- final application decision;
- detected role family;
- strong matches and gaps;
- red flags;
- recommended CV variant;
- source ID and application URL.

The discovery-to-matching conversion is deliberately conservative: structured source skills become preferred technical requirements, while seniority, experience and education are inferred only from explicit wording in the normalized offer. The underlying evaluator remains responsible for the final score and hard gate.

Do not commit API credentials. The discovery CLI fails clearly when France Travail credentials are missing.

## Tests

```powershell
python -m unittest discover -s tests -v
```

The discovery matching tests cover normalization into `JobOffer` objects and deterministic ranking by the existing evaluator score.

## Architecture

```text
Search configuration
        |
        v
Query portfolio ---> JobSource adapters ---> JobDiscovery normalization
                                             |
                                             v
                                      deduplication
                                             |
                                             v
                                        SQLite store
                                             |
                                             v
                                  candidate matching
                                             |
                                             v
                                      ranked shortlist
                                             |
                                             v
                                  application workflow
```

### Planned provider strategy

1. France Travail API — first structured provider.
2. Search-engine/company-career discovery — broad complementary discovery.
3. Apec — later, subject to the appropriate partner/API access.
4. Optional LinkedIn / Indeed / Welcome to the Jungle adapters only where access and source terms permit.

The system should automate discovery, filtering, analysis and ranking; the user remains the final decision-maker for applications.

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
