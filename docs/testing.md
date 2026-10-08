# Testing methodology

Run from an activated Python 3.11+ environment:

```bash
python -m pytest -ra
```

## Deterministic test scope

| Area | What is verified |
|---|---|
| Polygon containment | Interior, exterior, edges, and vertices |
| Zone transitions | Single entry, duplicate suppression, observed exit, duration, dropped detection tolerance, lost-track closure |
| PPE aggregation | Positive helmet/vest, explicit negative class, and the rule that absence remains `UNKNOWN` |
| Temporal confirmation | Required observations, no repeated active alert, compliant clearing, and fresh evidence for reactivation |
| Event deduplication | Independent incident keys and reactivation after close |
| Timestamps | Source timestamp preference and FPS fallback |
| SQLite | Complete round trip and event-ID idempotency |
| Reports | JSON/CSV generation, observed counts, and unavailable-PPE disclosure |
| Video errors | Missing path, unsupported suffix, and zero decoded frames |
| Model adapter | Fake YOLO results verify person filtering and track-ID parsing |

The fake-model tests exercise application integration only. They do not test neural-network quality and are named accordingly.

## Real inference smoke test

After installing all dependencies and obtaining network access for first-run weights, process a short video:

```bash
siteguard sample.mov --output outputs/smoke --download-ppe-model
```

Verify that:

1. `annotated_video.mp4` opens and has the same visual duration as the source;
2. boxes follow visible people and IDs do not change on every frame;
3. `summary.json` metadata matches the source;
4. PPE says `UNKNOWN` when no evidence is visible rather than inventing a violation;
5. every event row points to a real evidence JPEG when one could be written;
6. SQLite, JSON, and CSV contain the same event IDs.

This smoke test must be recorded separately from unit-test results.
