# Synthetic video manifest

Evaluation date: **12 October 2026** (Africa/Lagos)

These inputs were generated with Sora and supplied by the project owner. They are synthetic demonstration media. They are **not footage from A & K Construction Limited** and must not be described as evidence of activity, safety performance, or incidents at that company.

The `videos/` directory is intentionally ignored by Git. This manifest records technical metadata and hashes without publishing the media.

## Verified inputs

| Input | Container / codec | Resolution | FPS | Video frames | Video duration | File size | SHA-256 |
|---|---|---:|---:|---:|---:|---:|---|
| `videos/video1.mp4` | ISO MP4 / H.264 High, YUV420p | 864×496 | 24 | 97 | 4.041667 s | 1,554,113 bytes | `f31aeaefc904ab661ea07e09b0f0ec7236be49daf6e2aabd1510a1d6cda926d4` |
| `videos/video2.mp4` | ISO MP4 / H.264 High, YUV420p | 864×496 | 24 | 97 | 4.041667 s | 1,321,238 bytes | `867140278e15e6086ee77e3950d030c914b97805aaf038fb87cd8789256dfc08` |
| `videos/video3.mp4` | ISO MP4 / H.264 High, YUV420p | 1024×576 | 24 | 361 | 15.041667 s | 4,805,266 bytes | `63d3df912966287ec272dba1ab172c13fbb7d915f47fb7d41cf0b53303e5abe0` |

Metadata was read with `ffprobe` from the first video stream. The MP4 container duration for videos 1 and 2 is 4.096 seconds, while the encoded video stream duration is 4.041667 seconds; SiteGuard correctly reports the frame-derived video duration (`97 / 24`).

## Hazard-zone configuration status

No saved restricted-zone polygon exists for these three clips. The repository contains example coordinates for explaining CLI/dashboard input, but no coordinates supplied as a valid annotation for these particular videos. Therefore all three evaluation runs intentionally omitted `--zone`; zero zone events means **zone analysis was not configured**, not that every visible location was safe.

## Re-probing command

```bash
for f in videos/*.mp4; do
  ffprobe -v error -select_streams v:0 \
    -show_entries stream=codec_name,profile,width,height,pix_fmt,avg_frame_rate,nb_frames,duration \
    -show_entries format=format_name,duration,size \
    -of json "$f"
done
```
