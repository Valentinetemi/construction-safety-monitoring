# Methodology

## 1. Video preparation

SiteGuard accepts MP4 and MOV files and reads the source frame rate, reported frame count, width, and height with OpenCV. It uses the source presentation position in milliseconds when OpenCV supplies one, with `frame_number / fps` as a deterministic fallback.

## 2. Worker detection and tracking

The default `yolo11n.pt` checkpoint detects COCO class 0 (`person`). It is intentionally small for a 16 GB Apple Silicon laptop. Consecutive frames are passed to Ultralytics tracking with `persist=True` and `tracker="bytetrack.yaml"`. A track ID is counted as a worker tracking ID, not as a verified unique human identity.

Device selection is MPS first when PyTorch reports it available, otherwise CPU. If an operation fails on MPS, the adapter retries it on CPU and keeps using CPU for the rest of that model instance.

## 3. PPE evidence

PPE is a separate inference task. The default optional checkpoint is `buildvision-hazards-v0.3.pt` from `constructelligence/construction-site-safety-hazards`, pinned to revision `45d07d8e27a4754df1ea651f62153e000133bece`. It documents explicit worn and missing labels for hard hats and safety vests.

Detection centres are assigned to simple anatomical regions derived from each tracked person box:

- helmet evidence: upper portion of the person box;
- vest evidence: middle/torso portion of the person box.

This is not pose estimation. It is fast and explainable, but overlapping workers can cause association errors.

Per gear item:

- an explicit negative label produces `POSSIBLE_VIOLATION`;
- a positive label produces `COMPLIANT`;
- no usable evidence produces `UNKNOWN`.

The overall worker state is `POSSIBLE_VIOLATION` if either item has explicit negative evidence, `COMPLIANT` only when both have positive evidence, and otherwise `UNKNOWN`.

The default event threshold is three negative observations within five observations. One event is emitted for the continuous incident. Two consecutive compliant observations clear the incident; historical negative evidence is then discarded before a later incident can be confirmed.

## 4. Hazard zones

Users supply a named polygon in source-image pixel coordinates. The bottom-centre of each worker box approximates contact with the ground. A boundary-inclusive ray-casting algorithm decides containment.

The zone state machine emits one entry when an outside track becomes inside and one exit when it later becomes outside. Short detection drops are tolerated. A track that remains missing is closed as `track_lost`; an open incident at end of video is closed as `stream_end`. Those reasons prevent inferred exits from being mistaken for directly observed motion.

These polygons are annotations chosen by the user. They do not prove that the pictured area is hazardous.

## 5. Evidence and reports

Confirmed events receive UUIDs. The annotated event frame is stored as a JPEG when OpenCV can write it. The same record is inserted into SQLite and exported to JSON/CSV. The summary reports observed counts and limitations; it contains no invented accuracy measurement.
