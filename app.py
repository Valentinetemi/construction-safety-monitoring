"""Minimal Streamlit dashboard for SiteGuard's real analysis pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import streamlit as st

from siteguard.errors import SiteGuardError
from siteguard.pipeline import PipelineConfig, analyze_video
from siteguard.zones import HazardZone


def parse_polygon(text: str) -> tuple[tuple[int, int], ...]:
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("Polygon must be a JSON list")
    points = tuple((int(point[0]), int(point[1])) for point in data)
    if len(points) < 3:
        raise ValueError("Polygon requires at least three points")
    return points


def download_button(path: Path, label: str, mime: str) -> None:
    st.download_button(
        label,
        data=path.read_bytes(),
        file_name=path.name,
        mime=mime,
        use_container_width=True,
    )


st.set_page_config(page_title="SiteGuard", page_icon="🦺", layout="wide")
st.title("SiteGuard — Construction Site Safety Monitoring")
st.caption(
    "Real YOLO + ByteTrack analysis. Alerts are evidence for human review, not certified safety decisions."
)

uploaded = st.file_uploader("Construction-site video", type=["mp4", "mov"])
use_zone = st.checkbox("Enable a user-configured hazard zone", value=True)
zone_name = st.text_input("Zone name", value="Hazard Zone", disabled=not use_zone)
polygon_text = st.text_area(
    "Polygon coordinates (source-video pixels, JSON)",
    value="[[100, 100], [900, 100], [900, 650], [100, 650]]",
    disabled=not use_zone,
    help="Use at least three [x, y] points. This region is configured by you; SiteGuard does not infer hazards.",
)

with st.expander("Model and confirmation settings"):
    person_confidence = st.slider("Person confidence", 0.10, 0.90, 0.35, 0.05)
    ppe_confidence = st.slider("PPE confidence", 0.10, 0.90, 0.35, 0.05)
    download_ppe = st.checkbox(
        "Download and use public PPE weights",
        value=True,
        help="Downloads AGPL-3.0 YOLOv8s weights from Hugging Face on first use. Disable to report PPE as UNKNOWN.",
    )
    confirmation_frames = st.slider("Negative PPE confirmations", 2, 10, 3)
    window_size = st.slider(
        "PPE evidence window", confirmation_frames, 20, max(5, confirmation_frames)
    )

if st.button("Start analysis", type="primary", disabled=uploaded is None):
    try:
        zones: tuple[HazardZone, ...] = ()
        if use_zone:
            zones = (HazardZone(zone_name, parse_polygon(polygon_text)),)
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
        run_dir = Path("outputs") / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(uploaded.name).suffix.lower()
        input_path = run_dir / f"source{suffix}"
        input_path.write_bytes(uploaded.getbuffer())
        bar = st.progress(0.0, text="Preparing models…")

        def update_progress(current: int, total: int) -> None:
            fraction = min(1.0, current / total) if total else 0.0
            bar.progress(fraction, text=f"Processed {current}/{total or '?'} frames")

        result = analyze_video(
            PipelineConfig(
                input_path=input_path,
                output_dir=run_dir,
                zones=zones,
                download_ppe_model=download_ppe,
                person_confidence=person_confidence,
                ppe_confidence=ppe_confidence,
                ppe_confirmation_frames=confirmation_frames,
                ppe_window_size=window_size,
            ),
            update_progress,
        )
        bar.progress(1.0, text="Analysis complete")
        st.session_state["siteguard_result"] = result
    except (SiteGuardError, ValueError, json.JSONDecodeError) as exc:
        st.error(str(exc))
    except Exception as exc:
        st.exception(exc)

result = st.session_state.get("siteguard_result")
if result:
    st.subheader("Analysis result")
    metrics = st.columns(4)
    metrics[0].metric("Tracking IDs", result.summary["unique_tracking_ids"])
    metrics[1].metric("Zone entries", result.summary["hazard_zone_entries"])
    metrics[2].metric(
        "Possible PPE violations", result.summary["possible_ppe_violations"]
    )
    metrics[3].metric("Frames", result.summary["frames_processed"])
    st.video(str(result.annotated_video))
    st.dataframe([event.to_dict() for event in result.events], use_container_width=True)

    st.subheader("Downloads")
    columns = st.columns(5)
    with columns[0]:
        download_button(result.annotated_video, "Annotated MP4", "video/mp4")
    with columns[1]:
        download_button(result.events_json, "Events JSON", "application/json")
    with columns[2]:
        download_button(result.events_csv, "Events CSV", "text/csv")
    with columns[3]:
        download_button(result.summary_json, "Summary JSON", "application/json")
    with columns[4]:
        download_button(result.database_path, "SQLite database", "application/x-sqlite3")

    with st.expander("Limitations recorded in this run"):
        for limitation in result.summary["limitations"]:
            st.write(f"- {limitation}")
