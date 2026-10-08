# Known limitations and responsible use

- SiteGuard is not a certified safety product and must not replace trained personnel, site procedures, or emergency systems.
- Video monitoring may involve privacy, employment, biometric, and data-protection obligations. Obtain permission and minimize retention.
- ByteTrack IDs are temporary trajectory identifiers, not identities.
- Person detection can fail because of distance, occlusion, lighting, unusual poses, motion blur, or domain shift.
- The PPE model's own published results show weaker performance for missing-equipment classes than for worn equipment. Every possible violation needs human review.
- PPE association uses box geometry rather than body pose; overlapping people are a known failure mode.
- `UNKNOWN` is expected and safer than interpreting missing pixels as missing gear.
- A zone is a 2D polygon in image coordinates. Camera perspective and lens distortion are not calibrated.
- The bottom-centre of a person box is only an estimate of foot/ground contact.
- Tracking gaps are tolerated for a fixed number of frames. Longer gaps close an incident as `track_lost`, which is not proof that the worker physically exited.
- Frame-based temporal thresholds represent different durations at different source frame rates.
- OpenCV codec availability varies. An MP4 can be generated with `mp4v` yet require transcoding for a particular browser.
- Reports count tracking IDs and model incidents, not verified people or legal violations.
