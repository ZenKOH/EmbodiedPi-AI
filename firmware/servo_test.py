#!/usr/bin/env python3
from __future__ import annotations

import argparse

from embodiedpi.core import MockServoBus, PCA9685ServoBus, load_robot_profile


def main() -> None:
    parser = argparse.ArgumentParser(description="Move one servo to a target angle")
    parser.add_argument("--profile", default="robot_profiles/default_7_servo.yaml")
    parser.add_argument("--servo", required=True)
    parser.add_argument("--angle", type=float, required=True)
    parser.add_argument("--duration-ms", type=int, default=500)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    profile = load_robot_profile(args.profile)
    servo = profile.servo(args.servo)
    servo.validate_angle(args.angle)
    bus = MockServoBus() if args.dry_run else PCA9685ServoBus(profile)
    try:
        bus.move(servo, args.angle, args.duration_ms)
    finally:
        bus.close()


if __name__ == "__main__":
    main()
