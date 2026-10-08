# Demo instructions

## Preparation

1. Use Python 3.11–3.13 and install `.[app,test]`.
2. Run `pytest` and retain the terminal output for the testing slide.
3. Choose a short, authorized construction clip with visible people and PPE.
4. Note the source resolution so polygon coordinates are easy to choose.
5. Let the model checkpoints download before the presentation if the venue network is unreliable; they remain in the user cache, not this repository.

## Dashboard flow

```bash
streamlit run app.py
```

1. Upload an MP4 or MOV.
2. Enter at least three polygon points in source-video pixel coordinates.
3. Keep the public PPE weights option enabled for real PPE inference.
4. Start analysis and wait for the progress bar to finish.
5. Show the annotated video, tracking-ID count, zone entries, possible PPE incidents, and event table.
6. Open one evidence JPEG from the run directory and show the matching event in JSON/SQLite.
7. State the limitations: configured zones, possible—not definitive—PPE violations, and tracking IDs—not identities.

## Command-line fallback

If the dashboard is unavailable, run:

```bash
PYTHONPATH=src python -m siteguard input.mp4 \
  --output outputs/presentation \
  --zone 'Restricted Area:100,100;800,100;800,600;100,600' \
  --download-ppe-model
```

Then play `outputs/presentation/annotated_video.mp4` and open the reports directly.

## Suggested live narration

“The person detector is a general pretrained YOLO model. ByteTrack maintains frame-to-frame IDs. PPE is handled by a separate PPE-trained checkpoint, and SiteGuard requires explicit negative detections across several frames. The red polygon is configured by the user; the system only tests whether the worker's estimated ground point crosses it. Each confirmed incident links to a source timestamp and evidence frame.”
