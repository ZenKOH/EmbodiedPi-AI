import pytest

from embodiedpi.core import AgentAction, Gesture, GestureFrame, build_runtime, load_gestures, load_robot_profile, validate_gesture


def test_load_default_profile():
    profile = load_robot_profile("robot_profiles/default_7_servo.yaml")
    assert profile.name == "default_7_servo_companion"
    assert len(profile.servos) == 7
    assert profile.servo("body_lift").neutral == 90


def test_load_gestures():
    gestures = load_gestures("gestures")
    assert "wave" in gestures
    assert gestures["wave"].total_duration_ms > 0


def test_agent_action_json():
    action = AgentAction.from_json_text('{"reply":"ok","action":"wave","intensity":"gentle","duration_seconds":2}')
    assert action.action == "wave"


def test_rejects_out_of_range_angle():
    profile = load_robot_profile("robot_profiles/default_7_servo.yaml")
    bad = Gesture("bad", "bad", [GestureFrame(100, {"body_lift": 200})])
    with pytest.raises(ValueError):
        validate_gesture(profile, bad)


def test_rule_runtime_dry_run(tmp_path):
    runtime = build_runtime(dry_run=True, log_path=tmp_path / "sessions.db")
    result = runtime.handle_command("please wave hello")
    assert result["action"] == "wave"
