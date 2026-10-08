# Real-world evaluation workflow

No construction-site footage was available during implementation. This document is a repeatable workflow and blank report template, not an evaluation result.

## Reproducible procedure

1. Preserve the original clip and record its filename, source, permission/consent status, resolution, frame rate, duration, and SHA-256 hash.
2. Define hazard polygons before inspecting model alerts. Save the exact command and coordinates.
3. Record the person model, PPE model/revision, thresholds, temporal window, Python version, package versions, and device.
4. Run SiteGuard into a new output directory; do not overwrite an earlier run.
5. Watch the source and annotated videos side-by-side at normal speed and frame-by-frame around every event.
6. Record successful person detections, ID switches, missed people, false people, PPE associations, explicit negative PPE errors, zone transitions, and decode/codec issues.
7. Select presentation screenshots from the actual evidence directory. Include at least one success and one limitation/failure case.
8. If quantitative metrics are needed, create ground-truth annotations first. Define matching thresholds and counting rules before computing any score.

Example command:

```bash
siteguard data/evaluation.mov \
  --output outputs/evaluation-01 \
  --zone 'Excavation:120,180;920,170;1040,690;80,700' \
  --download-ppe-model
```

## Blank evaluation record

| Field | Value |
|---|---|
| Evaluation date | _Not yet evaluated_ |
| Reviewer | _Not supplied_ |
| Source video and hash | _Not supplied_ |
| Consent/permission | _Not supplied_ |
| Person model | `yolo11n.pt` unless changed |
| PPE model/revision | `constructelligence/.../buildvision-hazards-v0.3.pt` unless changed |
| Device | _Record actual MPS/CPU_ |
| Configuration/command | _Not run_ |
| Total reviewed people/tracks | _Not measured_ |
| Correct detections | _Not measured_ |
| False positives | _Not measured_ |
| False negatives | _Not measured_ |
| ID switches | _Not measured_ |
| PPE association failures | _Not measured_ |
| Zone transition failures | _Not measured_ |

## Qualitative observations

### What worked

_Complete only after reviewing real output._

### Failure cases

_Complete only after reviewing real output. Include timestamps and evidence paths._

### Conclusion

_State only what the reviewed footage supports. Do not generalize from one short clip to all construction sites._
