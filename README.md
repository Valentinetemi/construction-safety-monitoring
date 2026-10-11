# SiteGuard

SiteGuard is a local, evidence-backed construction-site video analysis system. It uses a real pretrained YOLO person detector, ByteTrack IDs, an optional PPE-specific detector, user-configured polygon zones, SQLite event storage, annotated video export, and machine-readable reports.

It is built for a final SIWES demonstration on Apple Silicon, with MPS acceleration when PyTorch supports it and automatic CPU retry when MPS inference fails.

## What is real—and what is not

- Person boxes come from Ultralytics YOLO, not hard-coded coordinates.
- Track IDs come from ByteTrack through `model.track(..., persist=True, tracker="bytetrack.yaml")`.
- PPE is evaluated only when a PPE-trained checkpoint is available. Otherwise every worker's PPE state is `UNKNOWN`; missing detections are never presented as proof of missing equipment.
- Hazard zones are polygons supplied by the user. SiteGuard does **not** infer whether a real-world area is hazardous.
- SiteGuard is a screening and demonstration tool, not a certified safety system. Every generated alert requires human review.
- No accuracy, benchmark, or real-video result is claimed until a labelled or reviewable evaluation video is actually processed.

## Features

- MP4 and MOV input with FPS, frame count, resolution, and source timestamps
- YOLO person detection and persistent ByteTrack worker IDs
- MPS selection on supported Macs with CPU fallback
- Optional, independently trained helmet and high-visibility-vest detection
- Conservative `COMPLIANT`, `POSSIBLE_VIOLATION`, and `UNKNOWN` PPE states
- Multi-frame confirmation before recording a possible PPE violation
- Polygon hazard-zone entry, exit, duration, and duplicate suppression
- Annotated `annotated_video.mp4` plus evidence JPEGs
- `events.json`, `events.csv`, `summary.json`, and SQLite persistence
- Streamlit upload/configuration/results workflow
- Unit tests that mock model inference separately from real-model evaluation

## Quick start

Python 3.11 or newer is required. The repository's old local `.venv` may use a different interpreter; create a fresh environment instead of reusing it.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[app,test]'
pytest
```

Run the dashboard:

```bash
streamlit run app.py
```

Or run the command-line pipeline:

```bash
siteguard input.mov \
  --output outputs/demo \
  --zone 'Excavation:100,100;900,100;900,650;100,650' \
  --download-ppe-model
```

Coordinates are source-video pixels in `x,y` order. At least three vertices are required. Omit `--zone` to run person/PPE analysis without zone events.

The first person-detection run may download the small `yolo11n.pt` checkpoint. `--download-ppe-model` downloads the PPE checkpoint to the Hugging Face cache. Neither checkpoint is copied into this repository or committed.

## PPE model provenance

The built-in optional adapter uses [`constructelligence/construction-site-safety-hazards`](https://huggingface.co/constructelligence/construction-site-safety-hazards), checkpoint `buildvision-hazards-v0.3.pt` (YOLOv8s, 640 px), pinned to model-repository revision `45d07d8e27a4754df1ea651f62153e000133bece`. Its documented labels include `person`, `hardhat`, `no-hardhat`, `safety vest`, and `no-safety vest`. The model card reports that it was trained from several CC BY 4.0 construction datasets and publishes the weights under AGPL-3.0. See [`docs/ppe-model.md`](docs/ppe-model.md) for the complete class list and provenance.

The model card also warns that missing-PPE classes are harder than worn-PPE classes. SiteGuard therefore:

1. requires an explicit negative class (`no-hardhat` / `no-safety vest`) before proposing a violation;
2. associates PPE detections spatially with a tracked worker;
3. requires repeated observations across frames; and
4. calls the result `POSSIBLE_VIOLATION`, never a definitive compliance decision.

You may instead pass a compatible local Ultralytics checkpoint with `--ppe-model /path/to/weights.pt`. The checkpoint's embedded class names must contain recognizable helmet/vest positive and negative labels.

## Output layout

```text
outputs/demo/
├── annotated_video.mp4
├── events.csv
├── events.json
├── summary.json
├── siteguard.db
└── evidence/
    └── <event-id>.jpg
```

Frame numbers in reports are zero-based. Timestamps are source-video seconds, taken from OpenCV's presentation timestamp when available and otherwise calculated as `frame_number / fps`.

## Architecture

```text
video -> YOLO person model -> ByteTrack -> worker tracks
  |                                  |-> polygon zone state machine
  |-> PPE-specific YOLO -> spatial matching -> temporal confirmation
                                             |
                                     event + evidence frame
                                             |
                          SQLite + JSON/CSV + summary + annotated MP4
```

See [`docs/architecture.md`](docs/architecture.md), [`docs/methodology.md`](docs/methodology.md), and [`docs/demo.md`](docs/demo.md) for the detailed design and presentation workflow.

## Verified synthetic demonstration

Three Sora-generated construction-site clips have been processed end to end with the real person detector, ByteTrack, and the pinned PPE detector. They are synthetic test media—not footage from A & K Construction Limited—and the results demonstrate pipeline execution rather than model accuracy. No restricted-zone polygon was configured, so the runs correctly contain no zone events.

- [`docs/synthetic-evaluation/VIDEO_MANIFEST.md`](docs/synthetic-evaluation/VIDEO_MANIFEST.md) records the input metadata and hashes.
- [`docs/synthetic-evaluation/RESULTS.md`](docs/synthetic-evaluation/RESULTS.md) records measured processing times and observed outputs.
- [`docs/synthetic-evaluation/DEMO_PLAYBOOK.md`](docs/synthetic-evaluation/DEMO_PLAYBOOK.md) gives the exact presentation and reproduction sequence.
- [`SIWES_DEFENSE_CODE_GUIDE.md`](SIWES_DEFENSE_CODE_GUIDE.md) explains the implementation and provides defense questions and answers.

The source clips and generated media remain under the ignored `videos/` and `outputs/` directories. They are intentionally not distributed through Git.

## Testing versus evaluation

`pytest` exercises deterministic geometry, state machines, timestamps, storage, reporting, and invalid-video behavior. Model-dependent unit tests use injected fakes and are marked clearly. Passing them proves software behavior, not model accuracy.

Real-world evaluation begins only after you provide construction footage. Follow [`docs/evaluation.md`](docs/evaluation.md); retain both successful and failed detections, and never report an accuracy percentage without ground-truth labels.

## Known limitations

- IDs can change after long occlusion, camera cuts, or crowded overlap.
- Ground-contact is approximated by the bottom-centre of the person box.
- Perspective is not calibrated; polygon coordinates are image-space only.
- PPE association is geometric and can be wrong when workers overlap.
- A detected negative PPE label is only model evidence, not proof.
- Video codec support depends on the local OpenCV build. SiteGuard tries common MP4 codecs and reports a clear error if none opens.
- MOV input is accepted, but the exported filename is always MP4.
- Processing is offline and frame-by-frame; it is not a real-time alarm service.

## Licensing note

Ultralytics and the optional PPE weights are offered under AGPL-3.0 unless you hold an applicable commercial licence. The PPE training sources are documented as CC BY 4.0 by the model publisher. Review those terms before redistribution or commercial deployment. Model weights and raw videos are deliberately excluded from Git
