# SiteGuard synthetic-video evaluation results

Evaluation date: **12 October 2026** (Africa/Lagos)

## Scope and truthfulness statement

These are Sora-generated synthetic construction-site clips supplied by the project owner. They are not real footage from A & K Construction Limited. The runs demonstrate that the implemented software can decode video, execute the configured models, track detected people, associate visible PPE evidence, annotate frames, and export reports. They do **not** establish real-world accuracy, precision, recall, mAP, safety compliance, or deployment readiness.

No restricted-zone polygon was configured for these clips. SiteGuard was therefore run without `--zone`. It would be incorrect to call the zero zone-event counts “safe-zone results.”

## Runtime configuration

- Person model: `yolo11n.pt` (COCO person class only)
- Tracker: ByteTrack through Ultralytics `tracker="bytetrack.yaml"`, persistent across consecutive frames
- PPE model: pinned `constructelligence/construction-site-safety-hazards` revision `45d07d8e27a4754df1ea651f62153e000133bece`, file `buildvision-hazards-v0.3.pt`
- Person confidence threshold: 0.35 (default)
- PPE confidence threshold: 0.35 (default)
- PPE confirmation: 3 negative observations in a 5-observation window (defaults)
- Runtime: Python 3.14.7, OpenCV 4.14.0, PyTorch 2.14.1, Ultralytics 8.4.175
- Device used: CPU. PyTorch reported MPS support was built but MPS was unavailable inside the execution sandbox.
- Zone list: empty for all three runs

## Verified results

| Video | Frames processed | Tracking IDs observed | PPE model available | Confirmed PPE events | Zone entries/exits | Cached end-to-end time | Throughput |
|---|---:|---:|---|---:|---:|---:|---:|
| `video1.mp4` | 97/97 | 9 | Yes | 0 | 0 / 0 | 8.49 s | 11.43 frames/s |
| `video2.mp4` | 97/97 | 8 | Yes | 0 | 0 / 0 | 7.68 s | 12.63 frames/s |
| `video3.mp4` | 361/361 | 19 | Yes | 0 | 0 / 0 | 22.43 s | 16.09 frames/s |

The first `video1` run took 81.96 seconds because it included first-run person/PPE model retrieval and cold startup. It was rerun with cached weights to obtain the comparable 8.49-second measurement above. Timings include decoding, both model passes, tracking, association, annotation, video encoding, SQLite operations, and report writing. They are measurements of this run, not guaranteed performance on another machine.

“Tracking IDs observed” is deliberately not labelled “workers counted.” ByteTrack can assign more than one ID to the same visible person after an occlusion or lost track.

## Output integrity checks

All three output MP4 files reopened successfully with OpenCV and preserved the corresponding input width, height, 24 FPS, frame count, and frame-derived duration.

| Output | Resolution | FPS | Frames | Duration | Output size |
|---|---:|---:|---:|---:|---:|
| `outputs/synthetic/video1/annotated_video.mp4` | 864×496 | 24 | 97 | 4.041667 s | 1,102,375 bytes |
| `outputs/synthetic/video2/annotated_video.mp4` | 864×496 | 24 | 97 | 4.041667 s | 969,176 bytes |
| `outputs/synthetic/video3/annotated_video.mp4` | 1024×576 | 24 | 361 | 15.041667 s | 6,359,567 bytes |

For every video:

- `summary.json` reports `ppe_model_available: true`;
- `events.json` contains an empty JSON list;
- `events.csv` contains its header and zero event rows;
- `siteguard.db` contains zero `safety_events` rows;
- the evidence directory contains zero JPEGs because evidence is written only when an event is created;
- no zone event was expected because the zone list was empty.

## What the annotated videos actually show

Visual inspection found real output overlays from the two inference paths:

- green person boxes with persistent worker IDs and `PPE COMPLIANT` where both positive helmet and vest evidence were associated;
- yellow person boxes with `PPE UNKNOWN` when both required positive items were not established;
- smaller PPE boxes labelled with classes such as `hardhat` and `safety vest` plus model confidence;
- bottom-centre ground points for detected worker boxes;
- no red hazard polygon, because none was supplied;
- no `PPE_POSSIBLE_VIOLATION` event, because the temporal rule did not confirm repeated explicit negative-class evidence.

The overlay text can overlap in crowded frames. That is a presentation limitation, especially in videos 1 and 2, and should be acknowledged rather than hidden.

## Clearest demonstration

**`video3.mp4` is the clearest overall demonstration.** It is 15.04 seconds long, has the highest resolution (1024×576), shows workers at larger scale, visibly displays both hard-hat and safety-vest boxes, and provides enough motion to demonstrate persistent tracking IDs. Its crowded moments also honestly illustrate label-overlap and association limitations.

Videos 1 and 2 are useful shorter backups. Video 1 has a clear wide shot of several workers; video 2 demonstrates a more difficult scene with scaffolding and foreground/background scale variation.

## Recommended SIWES screenshots

Generated presentation frames are stored under the ignored `outputs/synthetic/presentation_frames/` directory.

1. **Primary:** `video3_frame_0120_5.0s.jpg` — frame 120, 5.0 seconds. Large workers, visible `hardhat` and `safety vest` boxes, green tracked-worker boxes, and readable `PPE COMPLIANT` labels.
2. **State comparison:** `video3_frame_0024_1.0s.jpg` — frame 24, 1.0 second. Shows several tracked workers and includes both green `COMPLIANT` and yellow `UNKNOWN` output, useful for explaining conservative classification.
3. **Wide-scene backup:** `video1_frame_0048_2.0s.jpg` — frame 48, 2.0 seconds. Shows tracking across multiple people in a wide site scene.
4. **Challenging-scene backup:** `video2_frame_0048_2.0s.jpg` — frame 48, 2.0 seconds. Shows detection across workers at different scales around scaffolding.

Do not label any of these as evidence of a real company or as proof of model accuracy.

## Reports to show during the defense

Use these in order:

1. Play `outputs/synthetic/video3/annotated_video.mp4` to show real frame-by-frame inference and tracking.
2. Open `outputs/synthetic/video3/summary.json` to show source metadata, 361 processed frames, 19 observed track IDs, PPE model availability, and zero fabricated events.
3. Open `outputs/synthetic/video3/events.json` and explain that an empty list is correct because no temporal violation was confirmed and no zone was configured.
4. Optionally query `outputs/synthetic/video3/siteguard.db` to show that persistence is present even when a run produces no incident rows.
5. In Streamlit, upload `video3.mp4`, **disable the hazard-zone checkbox unless you have defined and justified a real polygon for that clip**, run analysis, and show the same metrics and downloads.

There are no event evidence images to show from these runs. Using an ordinary annotated frame as though it were an incident screenshot would be misleading.

## Reproduction commands

From the repository root, after creating and activating a Python 3.11+ environment and installing the requirements:

```bash
PYTHONPATH=src python -m siteguard videos/video1.mp4 \
  --output outputs/synthetic/video1 \
  --download-ppe-model

PYTHONPATH=src python -m siteguard videos/video2.mp4 \
  --output outputs/synthetic/video2 \
  --download-ppe-model

PYTHONPATH=src python -m siteguard videos/video3.mp4 \
  --output outputs/synthetic/video3 \
  --download-ppe-model
```

No `--zone` flag appears because no valid zone annotation was supplied. On an Apple Silicon terminal where PyTorch exposes MPS, omit `--device` and SiteGuard selects MPS automatically; it retries on CPU if MPS inference fails.

## Unverified points

- No manual frame-level ground truth was created, so false-positive/false-negative rates are unknown.
- PPE classification quality was not quantitatively measured.
- Identity continuity was not manually scored, so ID-switch count is unknown.
- The synthetic videos do not establish performance on real construction footage.
- Hazard-zone transitions were not evaluated on these clips.
- Timing was measured once per cached run on the available CPU environment; no formal benchmark distribution was collected.
