# Technology stack

| Technology | Role | Rationale |
|---|---|---|
| Python 3.11+ | Application language | Strong CV/ML ecosystem and appropriate for the SIWES learning goal. |
| Ultralytics YOLO | Person and PPE model runtime | Provides pretrained person detection, custom checkpoints, device selection, and tracking integration. |
| ByteTrack | Multi-object tracking | Maintains IDs using motion and both high/low confidence detections without a separate re-identification model. |
| OpenCV | Decode, annotate, evidence, encode | Mature local video I/O and drawing support. |
| NumPy | Polygon arrays for drawing | Efficient representation passed to OpenCV. |
| SQLite | Event persistence | Serverless, inspectable, and portable for a laptop demonstration. |
| Streamlit | Demonstration dashboard | Provides upload, progress, playback, tables, and downloads with minimal UI code. |
| pytest | Automated tests | Fast deterministic tests with fixtures and clear failure reports. |
| Hugging Face Hub | Optional PPE checkpoint retrieval | Versioned public model hosting without committing weights to Git. |

## Apple Silicon profile

The default person checkpoint is the nano YOLO variant. The PPE checkpoint is YOLOv8s and approximately 22.6 MB in PyTorch format according to its repository. SiteGuard uses MPS if available but retains a CPU path because unsupported PyTorch operations and environment differences can still occur.

For the presentation, close memory-heavy applications and use a short 720p/1080p clip. Do not change frame rate or skip frames during evaluation unless that change is recorded, because temporal confirmation is frame-based.
