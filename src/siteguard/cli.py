"""Command-line entry point for repeatable SiteGuard analysis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .errors import SiteGuardError
from .pipeline import PipelineConfig, analyze_video
from .zones import HazardZone


def parse_zone(value: str) -> HazardZone:
    """Parse NAME:x,y;x,y;x,y into a validated hazard zone."""
    try:
        name, coordinates = value.split(":", 1)
        points = tuple(
            tuple(int(component.strip()) for component in pair.split(",", 1))
            for pair in coordinates.split(";")
            if pair.strip()
        )
        if any(len(point) != 2 for point in points):
            raise ValueError
        return HazardZone(name.strip(), points)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError(
            "zone must be NAME:x,y;x,y;x,y with at least three integer points"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="siteguard",
        description="Analyze construction-site MP4/MOV footage with real CV models.",
    )
    parser.add_argument("input", type=Path, help="MP4 or MOV source video")
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/run"), help="output directory"
    )
    parser.add_argument(
        "--zone",
        type=parse_zone,
        action="append",
        default=[],
        help="repeatable NAME:x,y;x,y;x,y polygon",
    )
    parser.add_argument("--person-model", default="yolo11n.pt")
    parser.add_argument("--ppe-model", type=Path)
    parser.add_argument(
        "--download-ppe-model",
        action="store_true",
        help="download the documented public PPE weights when no local path is set",
    )
    parser.add_argument("--device", choices=("mps", "cpu"))
    parser.add_argument("--person-confidence", type=float, default=0.35)
    parser.add_argument("--ppe-confidence", type=float, default=0.35)
    parser.add_argument("--ppe-confirmation-frames", type=int, default=3)
    parser.add_argument("--ppe-window-size", type=int, default=5)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = PipelineConfig(
        input_path=args.input,
        output_dir=args.output,
        zones=tuple(args.zone),
        person_model=args.person_model,
        ppe_model_path=args.ppe_model,
        download_ppe_model=args.download_ppe_model,
        person_confidence=args.person_confidence,
        ppe_confidence=args.ppe_confidence,
        ppe_confirmation_frames=args.ppe_confirmation_frames,
        ppe_window_size=args.ppe_window_size,
        device=args.device,
    )

    def progress(current: int, total: int) -> None:
        if total and (current == 1 or current % 30 == 0 or current == total):
            print(f"Processed {current}/{total} frames", file=sys.stderr)

    try:
        result = analyze_video(config, progress)
    except (SiteGuardError, ValueError) as exc:
        print(f"SiteGuard error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.summary, indent=2, sort_keys=True))
    print(f"Annotated video: {result.annotated_video}")
    print(f"Reports: {result.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
