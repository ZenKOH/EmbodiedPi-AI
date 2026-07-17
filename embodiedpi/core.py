from __future__ import annotations

import json
import os
import sqlite3
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal, Any

import requests
import yaml
from pydantic import BaseModel, Field, ValidationError


@dataclass(frozen=True)
class ServoConfig:
    name: str
    channel: int
    min_angle: float
    max_angle: float
    neutral: float
    max_speed_dps: float = 90.0
    inverted: bool = False

    def validate_angle(self, angle: float) -> None:
        if angle < self.min_angle or angle > self.max_angle:
            raise ValueError(
                f"Servo '{self.name}' target {angle} outside safe range [{self.min_angle}, {self.max_angle}]"
            )


@dataclass(frozen=True)
class RobotProfile:
    name: str
    description: str
    version: str
    servos: dict[str, ServoConfig]

    def servo(self, name: str) -> ServoConfig:
        if name not in self.servos:
            raise KeyError(f"Unknown servo '{name}'. Known servos: {sorted(self.servos)}")
        return self.servos[name]


def load_robot_profile(path: str | Path) -> RobotProfile:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Robot profile {path} must be a YAML mapping")
    robot = data.get("robot", {})
    servos = data.get("servos", {})
    if not isinstance(robot, dict) or not isinstance(servos, dict) or not servos:
        raise ValueError("Profile must contain robot and servos mappings")
    parsed: dict[str, ServoConfig] = {}
    used_channels: set[int] = set()
    for name, raw in servos.items():
        if not isinstance(raw, dict):
            raise ValueError(f"Servo {name} must be a mapping")
        channel = int(raw["channel"])
        if channel in used_channels:
            raise ValueError(f"Duplicate PCA9685 channel {channel}")
        used_channels.add(channel)
        cfg = ServoConfig(
            name=str(name),
            channel=channel,
            min_angle=float(raw["min_angle"]),
            max_angle=float(raw["max_angle"]),
            neutral=float(raw["neutral"]),
            max_speed_dps=float(raw.get("max_speed_dps", 90.0)),
            inverted=bool(raw.get("inverted", False)),
        )
        if cfg.min_angle >= cfg.max_angle:
            raise ValueError(f"Servo {name} min_angle must be below max_angle")
        cfg.validate_angle(cfg.neutral)
        parsed[str(name)] = cfg
    return RobotProfile(
        name=str(robot.get("name", path.stem)),
        description=str(robot.get("description", "")),
        version=str(robot.get("version", "0.1")),
        servos=parsed,
    )


@dataclass(frozen=True)
class GestureFrame:
    duration_ms: int
    positions: dict[str, float]


@dataclass(frozen=True)
class Gesture:
    name: str
    description: str
    frames: list[GestureFrame]

    @property
    def total_duration_ms(self) -> int:
        return sum(frame.duration_ms for frame in self.frames)


def load_gesture(path: str | Path) -> Gesture:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Gesture {path} must be a YAML mapping")
    frames = data.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError(f"Gesture {path} must define frames")
    parsed: list[GestureFrame] = []
    for index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            raise ValueError(f"Frame {index} in {path} must be a mapping")
        duration = int(frame.get("duration_ms", 0))
        positions = frame.get("positions", {})
        if duration <= 0:
            raise ValueError(f"Frame {index} in {path} must have positive duration_ms")
        if not isinstance(positions, dict) or not positions:
            raise ValueError(f"Frame {index} in {path} must define positions")
        parsed.append(GestureFrame(duration, {str(k): float(v) for k, v in positions.items()}))
    return Gesture(str(data.get("name", path.stem)), str(data.get("description", "")), parsed)


def load_gestures(directory: str | Path) -> dict[str, Gesture]:
    directory = Path(directory)
    gestures: dict[str, Gesture] = {}
    for path in sorted(directory.glob("*.yaml")):
        gesture = load_gesture(path)
        if gesture.name in gestures:
            raise ValueError(f"Duplicate gesture name {gesture.name}")
        gestures[gesture.name] = gesture
    if not gestures:
        raise ValueError(f"No gesture YAML files found in {directory}")
    return gestures


Intensity = Literal["gentle", "normal", "high"]


class AgentAction(BaseModel):
    reply: str = Field(..., min_length=1, max_length=500)
    action: str = Field(..., min_length=1, max_length=64)
    intensity: Intensity = "gentle"
    duration_seconds: float = Field(default=2.0, ge=0.1, le=30.0)

    @classmethod
    def from_json_text(cls, text: str) -> "AgentAction":
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`").removeprefix("json").strip()
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM did not return valid JSON: {text[:120]}") from exc
        try:
            return cls.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"LLM JSON failed schema validation: {exc}") from exc


class LLMProvider(ABC):
    @abstractmethod
    def parse(self, command: str, allowed_actions: Iterable[str]) -> AgentAction:
        raise NotImplementedError


class RuleBasedProvider(LLMProvider):
    KEYWORDS = {
        "fist": "fist_bump", "bump": "fist_bump", "wave": "wave", "hello": "wave",
        "hi": "wave", "nod": "nod", "yes": "nod", "shake": "shake_head", "no": "shake_head",
        "think": "thinking_pose", "curious": "curious_tilt", "sleep": "sleepy_mode",
        "idle": "idle_breathing", "happy": "happy_bounce", "attention": "attention",
    }

    def parse(self, command: str, allowed_actions: Iterable[str]) -> AgentAction:
        allowed = set(allowed_actions)
        lower = command.lower()
        for key, action in self.KEYWORDS.items():
            if key in lower and action in allowed:
                return AgentAction(
                    reply=f"Okay. I will do {action.replace('_', ' ')}.",
                    action=action,
                    intensity="gentle",
                    duration_seconds=2.0,
                )
        fallback = "attention" if "attention" in allowed else sorted(allowed)[0]
        return AgentAction(reply="I heard you. I will respond safely.", action=fallback)


SYSTEM_PROMPT = """You are the intent parser for EmbodiedPi AI, a small tabletop robot.
Return JSON only. No markdown.
Allowed schema: {"reply":"short spoken reply","action":"approved gesture name","intensity":"gentle|normal|high","duration_seconds":number}
Never output raw servo angles, code, shell commands, wiring instructions, or unsafe physical actions.
"""


def build_user_prompt(command: str, allowed_actions: list[str]) -> str:
    return f"User command: {command.strip()}\nAllowed actions: {', '.join(sorted(allowed_actions))}\nChoose exactly one allowed action."


class OllamaProvider(LLMProvider):
    def __init__(self, url: str | None = None, model: str | None = None, timeout: float = 30.0):
        self.url = url or os.getenv("EMBODIEDPI_OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model = model or os.getenv("EMBODIEDPI_OLLAMA_MODEL", "llama3.2:1b")
        self.timeout = timeout

    def parse(self, command: str, allowed_actions: Iterable[str]) -> AgentAction:
        allowed = list(allowed_actions)
        response = requests.post(self.url, json={
            "model": self.model,
            "prompt": SYSTEM_PROMPT + "\n\n" + build_user_prompt(command, allowed),
            "stream": False,
            "format": "json",
        }, timeout=self.timeout)
        response.raise_for_status()
        action = AgentAction.from_json_text(response.json().get("response", ""))
        if action.action not in set(allowed):
            return AgentAction(reply="That action is not available, so I will stay attentive.", action="attention")
        return action


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None, timeout: float = 30.0):
        self.api_key = api_key or os.getenv("EMBODIEDPI_OPENAI_API_KEY")
        self.model = model or os.getenv("EMBODIEDPI_OPENAI_MODEL", "gpt-4o-mini")
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("EMBODIEDPI_OPENAI_API_KEY is required")

    def parse(self, command: str, allowed_actions: Iterable[str]) -> AgentAction:
        allowed = list(allowed_actions)
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": self.model,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(command, allowed)},
                ],
                "temperature": 0.2,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        action = AgentAction.from_json_text(response.json()["choices"][0]["message"]["content"])
        if action.action not in set(allowed):
            return AgentAction(reply="That action is not available, so I will stay attentive.", action="attention")
        return action


def build_provider(name: str | None = None) -> LLMProvider:
    provider = (name or os.getenv("EMBODIEDPI_LLM_PROVIDER", "rule")).lower()
    if provider == "rule":
        return RuleBasedProvider()
    if provider == "ollama":
        return OllamaProvider()
    if provider == "openai":
        return OpenAIProvider()
    raise ValueError(f"Unknown LLM provider {provider}")


@dataclass
class SafetyState:
    emergency_stop: bool = False
    max_frame_duration_ms: int = 10_000

    def stop(self) -> None:
        self.emergency_stop = True

    def reset(self) -> None:
        self.emergency_stop = False


def validate_gesture(profile: RobotProfile, gesture: Gesture, safety: SafetyState | None = None) -> None:
    safety = safety or SafetyState()
    if safety.emergency_stop:
        raise RuntimeError("Emergency stop is active; refusing motion")
    for frame in gesture.frames:
        if frame.duration_ms <= 0 or frame.duration_ms > safety.max_frame_duration_ms:
            raise ValueError(f"Unsafe frame duration: {frame.duration_ms} ms")
        for servo_name, angle in frame.positions.items():
            profile.servo(servo_name).validate_angle(angle)


class ServoBus(ABC):
    @abstractmethod
    def move(self, servo: ServoConfig, angle: float, duration_ms: int) -> None:
        raise NotImplementedError

    def close(self) -> None:
        return None


@dataclass
class MockServoBus(ServoBus):
    moves: list[dict[str, float | int | str]] = field(default_factory=list)
    sleep: bool = False

    def move(self, servo: ServoConfig, angle: float, duration_ms: int) -> None:
        self.moves.append({"servo": servo.name, "channel": servo.channel, "angle": angle, "duration_ms": duration_ms})
        print(f"[dry-run] {servo.name}@ch{servo.channel} -> {angle:.1f} degrees over {duration_ms} ms")
        if self.sleep:
            time.sleep(duration_ms / 1000)


class PCA9685ServoBus(ServoBus):
    def __init__(self, profile: RobotProfile, frequency: int = 50):
        try:
            from adafruit_servokit import ServoKit
        except ImportError as exc:
            raise RuntimeError("Install Pi dependencies with `pip install -e .[pi]` or use --dry-run") from exc
        self.profile = profile
        self.kit = ServoKit(channels=16)
        self.kit.frequency = frequency
        for servo in profile.servos.values():
            self.kit.servo[servo.channel].set_pulse_width_range(500, 2500)
            self.kit.servo[servo.channel].angle = servo.neutral

    def move(self, servo: ServoConfig, angle: float, duration_ms: int) -> None:
        target = 180 - angle if servo.inverted else angle
        self.kit.servo[servo.channel].angle = target
        time.sleep(duration_ms / 1000)

    def close(self) -> None:
        for servo in self.profile.servos.values():
            self.kit.servo[servo.channel].angle = None


@dataclass
class MotionPlanner:
    profile: RobotProfile
    gestures: dict[str, Gesture]
    bus: ServoBus
    safety: SafetyState

    def execute(self, action: AgentAction) -> Gesture:
        if action.action not in self.gestures:
            raise ValueError(f"Unknown action {action.action}. Known gestures: {sorted(self.gestures)}")
        gesture = self.gestures[action.action]
        validate_gesture(self.profile, gesture, self.safety)
        for frame in gesture.frames:
            for servo_name, angle in frame.positions.items():
                self.bus.move(self.profile.servo(servo_name), angle, frame.duration_ms)
        return gesture

    def neutral(self, duration_ms: int = 300) -> None:
        if self.safety.emergency_stop:
            raise RuntimeError("Emergency stop is active; refusing motion")
        for servo in self.profile.servos.values():
            self.bus.move(servo, servo.neutral, duration_ms)


class SessionLog:
    def __init__(self, path: str | Path = "embodiedpi_sessions.db"):
        self.path = Path(path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    command TEXT NOT NULL,
                    reply TEXT NOT NULL,
                    action TEXT NOT NULL,
                    intensity TEXT NOT NULL,
                    duration_seconds REAL NOT NULL,
                    status TEXT NOT NULL
                )
            """)

    def add(self, command: str, reply: str, action: str, intensity: str, duration_seconds: float, status: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO events(command, reply, action, intensity, duration_seconds, status) VALUES (?, ?, ?, ?, ?, ?)",
                (command, reply, action, intensity, duration_seconds, status),
            )

    def recent(self, limit: int = 25) -> list[dict[str, Any]]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]


@dataclass
class EmbodiedPiRuntime:
    profile: RobotProfile
    gestures: dict[str, Gesture]
    provider: LLMProvider
    planner: MotionPlanner
    log: SessionLog

    def handle_command(self, command: str) -> dict[str, str | float]:
        action = self.provider.parse(command, self.gestures.keys())
        status = "ok"
        try:
            gesture = self.planner.execute(action)
        except Exception as exc:
            status = f"refused: {exc}"
            raise
        finally:
            self.log.add(command, action.reply, action.action, action.intensity, action.duration_seconds, status)
        print(f"Robot says: {action.reply}")
        return {
            "reply": action.reply,
            "action": action.action,
            "intensity": action.intensity,
            "duration_seconds": action.duration_seconds,
            "gesture_duration_ms": gesture.total_duration_ms,
        }


def build_runtime(
    profile_path: str | Path = "robot_profiles/default_7_servo.yaml",
    gesture_dir: str | Path = "gestures",
    dry_run: bool = True,
    provider_name: str | None = None,
    log_path: str | Path = "embodiedpi_sessions.db",
) -> EmbodiedPiRuntime:
    profile = load_robot_profile(profile_path)
    gestures = load_gestures(gesture_dir)
    bus: ServoBus = MockServoBus() if dry_run else PCA9685ServoBus(profile)
    planner = MotionPlanner(profile, gestures, bus, SafetyState())
    return EmbodiedPiRuntime(profile, gestures, build_provider(provider_name), planner, SessionLog(log_path))
