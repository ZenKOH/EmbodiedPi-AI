# EmbodiedPi AI

**EmbodiedPi AI** is a Raspberry Pi 5 framework for building small voice-controlled, gesture-capable, AI-powered tabletop robots.

The project is inspired by recent Raspberry Pi maker work combining a Raspberry Pi 5, a PCA9685 servo driver, microphone, speaker, multiple servos, speech recognition, LLM replies, text-to-speech, and physical gesture execution. This repository turns that idea into a reusable embodied-AI stack rather than a one-off character replica.

The central design rule is simple: **the LLM never controls raw servo angles**. It may only select approved actions. The deterministic motion layer validates the selected gesture against the robot profile, servo limits, duration limits, and emergency-stop state before anything moves.

## Architecture

```text
Voice or typed command
   ↓
STT / text input
   ↓
LLM or rule-based intent parser
   ↓
Structured action JSON
   ↓
Motion planner
   ↓
Safety validation
   ↓
Mock bus or PCA9685 servo bus
   ↓
Physical gesture + spoken reply
```

Example action schema:

```json
{
  "reply": "Sure. I will wave hello.",
  "action": "wave",
  "intensity": "gentle",
  "duration_seconds": 2.0
}
```

## Features

- Voice/text-to-gesture runtime.
- Rule-based provider for offline demos and tests.
- Optional Ollama-compatible local LLM provider.
- Optional OpenAI-compatible cloud provider.
- YAML robot profiles for 3-servo and 7-servo bodies.
- YAML gesture library with wave, fist bump, attention, nod, shake head, idle breathing, thinking pose, happy bounce, sleepy mode, and curious tilt.
- Mock servo bus for safe laptop development.
- PCA9685 servo bus wrapper for Raspberry Pi hardware.
- FastAPI dashboard for command testing, gesture triggering, emergency stop, and recent logs.
- Firmware utilities for I2C scanning and servo testing.
- Documentation for hardware, wiring, safety, local AI, and rehabilitation-coach demo use.
- CI tests for profile loading, gesture loading, action parsing, and safety rejection.

## Quick start on a laptop

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
python -m embodiedpi.cli list-gestures
python -m embodiedpi.cli run-gesture wave --dry-run
python -m embodiedpi.cli ask "please wave hello" --dry-run
```

## Quick start on Raspberry Pi 5

```bash
sudo raspi-config nonint do_i2c 0
python -m venv .venv
source .venv/bin/activate
pip install -e .[pi]
python firmware/i2c_scan.py
python firmware/servo_test.py --profile robot_profiles/default_7_servo.yaml --servo front_left --angle 90
python -m embodiedpi.dashboard --profile robot_profiles/default_7_servo.yaml
```

Then open:

```text
http://localhost:8000
```

## Recommended hardware

- Raspberry Pi 5.
- PCA9685 16-channel PWM/servo driver board or HAT.
- 3-7 micro servos.
- USB microphone or I2S microphone.
- Small speaker or USB audio output.
- External 5-6V servo power supply.
- Optional Raspberry Pi Camera Module.
- Optional Raspberry Pi AI HAT+ or AI HAT+ 2 for local edge-AI experiments.

Do **not** power multiple servos directly from the Raspberry Pi 5V rail. Use a separate servo supply with a shared ground.

## Repository layout

```text
embodiedpi/
  core.py          # profiles, gestures, LLM providers, planner, servo bus, runtime
  cli.py           # command-line interface
  dashboard.py     # FastAPI dashboard
robot_profiles/    # reusable body definitions
gestures/          # safe motion primitives
firmware/          # Pi hardware utilities
docs/              # hardware, wiring, safety, local AI, rehab demo
tests/             # validation tests
```

## Rehabilitation companion demo

The `docs/rehab_coach_demo.md` file describes a non-medical companion mode for engagement, reminders, and therapist-authored scripts. It is **not** intended for diagnosis, treatment, assessment, clinical triage, or autonomous therapy progression.

## Safety status

EmbodiedPi AI is for education, research prototyping, and maker projects. It is not a medical device, not a child-care device, and not an autonomous safety system.

MIT License.
