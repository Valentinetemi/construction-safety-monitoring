# SiteGuard synthetic-video demo playbook

## Scope and disclosure

The three clips in `videos/` were generated with Sora and supplied for software testing. They are **not real footage from A & K Construction Limited**. Present the demonstration as an integration test of SiteGuard, not as proof of PPE-model accuracy, worker compliance, site safety, or production readiness.

No valid restricted-zone polygon was configured for these clips. The verified runs therefore omitted `--zone`. An empty zone-event report means zone monitoring was not active; it does not mean that a real site was inspected and found safe.

## Best presentation sequence

Use `video3` as the main demonstration. It is the longest input (361 frames, 15.041667 seconds), has the highest resolution (1024×576), and gives the clearest view of the worker, tracking, hardhat, and safety-vest overlays.

1. State the synthetic-media disclosure above.
2. Play `outputs/synthetic/video3/annotated_video.mp4`.
3. Pause around 5.0 seconds to show the tracked worker and associated PPE boxes.
4. Open `outputs/synthetic/video3/summary.json` and point to the source metadata, 361 processed frames, 19 observed track IDs, and PPE-model availability.
5. Open `outputs/synthetic/video3/events.json`. Explain that the empty list is the truthful result: no temporally confirmed PPE event was generated, and zone monitoring was intentionally inactive.
6. If asked about persistence, query `siteguard.db` and show that the table exists with zero event rows.
7. Finish with the known limitations: track IDs can fragment, PPE association is geometric, and unlabelled synthetic media cannot produce an accuracy score.

Do not describe the 19 track IDs as 19 unique people. ByteTrack can create a new ID after occlusion or loss of association.

## Prepared screenshots

These files are generated locally and are excluded from Git:

| Priority | File | What it demonstrates |
|---|---|---|
| 1 | `outputs/synthetic/presentation_frames/video3_frame_0120_5.0s.jpg` | Clearest close view of tracking, compliance classification, and PPE detections. |
| 2 | `outputs/synthetic/presentation_frames/video3_frame_0024_1.0s.jpg` | Simultaneous `COMPLIANT` and `UNKNOWN` classifications. |
| 3 | `outputs/synthetic/presentation_frames/video1_frame_0048_2.0s.jpg` | Wider construction-scene example. |
| 4 | `outputs/synthetic/presentation_frames/video2_frame_0048_2.0s.jpg` | More difficult scaffolded scene and a useful limitations discussion. |

These are demonstration stills, not event evidence. The `evidence/` folders are empty because the runs generated no events.

## Verified output locations

```text
outputs/synthetic/video1/annotated_video.mp4
outputs/synthetic/video1/events.csv
outputs/synthetic/video1/events.json
outputs/synthetic/video1/summary.json
outputs/synthetic/video1/siteguard.db

outputs/synthetic/video2/annotated_video.mp4
outputs/synthetic/video2/events.csv
outputs/synthetic/video2/events.json
outputs/synthetic/video2/summary.json
outputs/synthetic/video2/siteguard.db

outputs/synthetic/video3/annotated_video.mp4
outputs/synthetic/video3/events.csv
outputs/synthetic/video3/events.json
outputs/synthetic/video3/summary.json
outputs/synthetic/video3/siteguard.db
```

## Reproduce the command-line demonstration

Python 3.11 or newer is recommended. The first model-backed run requires network access to obtain model weights unless they are already cached.

```bash
cd /Users/user/Desktop/site-monitor
python3.12 -m venv .venv-demo
source .venv-demo/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[app,test]'
pytest -q
```

Process the main clip without a fabricated zone:

```bash
siteguard videos/video3.mp4 \
  --output outputs/synthetic/video3 \
  --device cpu \
  --download-ppe-model
```

Process all three clips:

```bash
siteguard videos/video1.mp4 --output outputs/synthetic/video1 --device cpu --download-ppe-model
siteguard videos/video2.mp4 --output outputs/synthetic/video2 --device cpu --download-ppe-model
siteguard videos/video3.mp4 --output outputs/synthetic/video3 --device cpu --download-ppe-model
```

Do not add `--zone` unless a reviewer supplies and validates a real polygon in source-video pixel coordinates.

Inspect the main result:

```bash
open outputs/synthetic/video3/annotated_video.mp4
python -m json.tool outputs/synthetic/video3/summary.json
python -m json.tool outputs/synthetic/video3/events.json
sqlite3 outputs/synthetic/video3/siteguard.db 'SELECT COUNT(*) AS event_count FROM safety_events;'
```

Launch the dashboard separately if the presentation needs the user interface:

```bash
streamlit run app.py
```

Upload `videos/video3.mp4`, enable the public PPE model, and leave hazard-zone monitoring disabled because no validated polygon is available for the clip.

## Measured reference results

The existing outputs were measured on CPU with cached weights. Wall-clock time includes decoding, person inference, tracking, PPE inference, annotation, encoding, and report generation.

| Video | Frames | Wall time | Effective throughput | Observed track IDs | Events |
|---|---:|---:|---:|---:|---:|
| `video1.mp4` | 97 | 8.49 s | 11.43 fps | 9 | 0 |
| `video2.mp4` | 97 | 7.68 s | 12.63 fps | 8 | 0 |
| `video3.mp4` | 361 | 22.43 s | 16.09 fps | 19 | 0 |

The initial `video1` cold run took 81.96 seconds because it included model downloads. Timing varies by hardware, cache state, and system load. See `RESULTS.md` for complete metadata and interpretation.

## Statements to use in the defense

- “These clips are synthetic test media, not company footage.”
- “The boxes and IDs come from actual model inference and ByteTrack; they are not scripted overlays.”
- “A track ID is an observed trajectory, not a guaranteed unique-person count.”
- “The system only creates a possible PPE violation after repeated explicit negative detections.”
- “No zone was configured, so I did not claim zone monitoring or zone safety from these runs.”
- “The evaluation verifies integration. Accuracy requires labelled ground truth and is not claimed here.”

## Results to show—and results not to claim

Show the annotated `video3` output, its `summary.json`, the empty but valid `events.json`, and the SQLite event-count query. If time allows, show the `video3` 5-second still and the `video2` scaffolded still to explain strengths and limitations.

Do not claim:

- an accuracy, precision, recall, or mAP value;
- that every visible person has a stable unique ID;
- that zero events proves all workers were safe;
- that hazard-zone monitoring ran on these clips;
- that the synthetic scene belongs to A & K Construction Limited; or
- that an `UNKNOWN` classification is a violation.
