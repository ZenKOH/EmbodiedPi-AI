from __future__ import annotations

import argparse

from embodiedpi.core import AgentAction, build_runtime, load_gestures, load_robot_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EmbodiedPi AI command-line tools")
    parser.add_argument("--profile", default="robot_profiles/default_7_servo.yaml")
    parser.add_argument("--gesture-dir", default="gestures")
    parser.add_argument("--dry-run", action="store_true", default=False)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-gestures", help="List available gesture actions")

    validate = sub.add_parser("validate-profile", help="Validate a robot profile")
    validate.add_argument("path")

    run = sub.add_parser("run-gesture", help="Run one approved gesture")
    run.add_argument("gesture")

    ask = sub.add_parser("ask", help="Parse a natural-language command and execute the chosen gesture")
    ask.add_argument("text")

    neutral = sub.add_parser("neutral", help="Move all servos to neutral")
    neutral.add_argument("--duration-ms", type=int, default=300)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    if args.command == "validate-profile":
        profile = load_robot_profile(args.path)
        print(f"Valid profile: {profile.name} ({len(profile.servos)} servos)")
        return

    if args.command == "list-gestures":
        for name, gesture in load_gestures(args.gesture_dir).items():
            print(f"{name}: {gesture.description}")
        return

    runtime = build_runtime(args.profile, args.gesture_dir, dry_run=args.dry_run)

    if args.command == "run-gesture":
        runtime.planner.execute(AgentAction(reply="Running gesture.", action=args.gesture))
        print(f"Executed {args.gesture}")
        return

    if args.command == "ask":
        print(runtime.handle_command(args.text))
        return

    if args.command == "neutral":
        runtime.planner.neutral(args.duration_ms)
        print("Moved to neutral")
        return


if __name__ == "__main__":
    main()
