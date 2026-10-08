# SIWES presentation outline

## 1. Problem and objective

- Manual review of site footage is time-consuming.
- Objective: turn video into reviewable worker tracks, PPE evidence, zone events, and reports.
- Boundary: decision support, not an autonomous safety authority.

## 2. Requirements

- Real person inference, persistent tracking, PPE-specific evidence
- Configured polygon zones
- Timestamped events, screenshots, database, and downloadable reports
- Laptop-friendly local demonstration

## 3. Architecture

- Show the diagram from `architecture.md`.
- Explain why person and PPE models are separate.
- Explain ByteTrack state and per-video isolation.

## 4. Algorithms

- Person boxes and track IDs
- Bottom-centre ground approximation and point-in-polygon
- Helmet/head and vest/torso association
- Temporal confirmation and duplicate suppression

## 5. Data and persistence

- Walk through one event ID across evidence JPEG, JSON/CSV, and SQLite.
- Explain source timestamp versus processing time.

## 6. Demonstration

- Configure a zone, analyze a real clip, and review the annotated output.
- Show `UNKNOWN` behavior when evidence is absent or the PPE model is disabled.

## 7. Testing

- Present deterministic test areas and the actual current test result.
- Clearly separate mocked model tests from real-video evaluation.

## 8. Evaluation

- Insert only results produced from the supplied evaluation footage.
- Show both a correct case and a failure case.
- Do not add an accuracy number without labelled ground truth.

## 9. Limitations and ethics

- False positives/negatives, occlusion, ID switches, perspective, privacy, and human review.

## 10. Future improvements

- Pose-based PPE association
- Camera calibration and world-coordinate zones
- Manually labelled evaluation set
- Optional event review/approval workflow
- Performance profiling and model quantization based on measured results

## 11. Questions

Keep `summary.json`, one database query, the architecture diagram, and the limitations slide ready for technical questions.
