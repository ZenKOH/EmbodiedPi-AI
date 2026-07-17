from __future__ import annotations

import argparse

import uvicorn
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse

from embodiedpi.core import AgentAction, EmbodiedPiRuntime, build_runtime

app = FastAPI(title="EmbodiedPi AI Dashboard")
_runtime: EmbodiedPiRuntime | None = None


def get_runtime() -> EmbodiedPiRuntime:
    global _runtime
    if _runtime is None:
        _runtime = build_runtime(dry_run=True)
    return _runtime


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    runtime = get_runtime()
    buttons = "".join(
        f'<button onclick="runGesture(\'{name}\')">{name}</button> '
        for name in sorted(runtime.gestures)
    )
    rows = "".join(
        f"<tr><td>{name}</td><td>{servo.channel}</td><td>{servo.min_angle}-{servo.max_angle}</td><td>{servo.neutral}</td></tr>"
        for name, servo in runtime.profile.servos.items()
    )
    return f"""
    <!doctype html><html><head><title>EmbodiedPi AI</title>
    <style>body{{font-family:system-ui;background:#0a1020;color:#eaf2ff;margin:32px}}button,input{{padding:10px;margin:4px;border-radius:10px}}section{{border:1px solid #24324f;border-radius:18px;padding:18px;margin:18px 0;background:#10192d}}table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #24324f;padding:8px;text-align:left}}#estop{{background:#c33;color:white}}#reset{{background:#29663b;color:white}}</style>
    </head><body>
    <h1>EmbodiedPi AI Dashboard</h1>
    <p>Profile: <strong>{runtime.profile.name}</strong></p>
    <section><h2>Ask</h2><form onsubmit="ask(event)"><input id="command" size="50" placeholder="please wave hello"><button>Ask robot</button></form><pre id="out"></pre></section>
    <section><h2>Gestures</h2>{buttons}</section>
    <section><h2>Safety</h2><button id="estop" onclick="post('/api/estop')">Emergency stop</button><button id="reset" onclick="post('/api/reset')">Reset stop</button></section>
    <section><h2>Servos</h2><table><tr><th>Name</th><th>Channel</th><th>Range</th><th>Neutral</th></tr>{rows}</table></section>
    <script>
    async function post(url, body){{let o={{method:'POST'}}; if(body) o.body=body; let r=await fetch(url,o); document.getElementById('out').textContent=JSON.stringify(await r.json(),null,2)}}
    async function runGesture(name){{await post('/api/gesture/'+name)}}
    async function ask(e){{e.preventDefault(); let f=new FormData(); f.append('command', document.getElementById('command').value); await post('/api/ask', f)}}
    </script></body></html>
    """


@app.get("/api/status")
def status() -> dict[str, object]:
    runtime = get_runtime()
    return {
        "profile": runtime.profile.name,
        "servos": list(runtime.profile.servos),
        "gestures": list(runtime.gestures),
        "emergency_stop": runtime.planner.safety.emergency_stop,
    }


@app.post("/api/gesture/{gesture_name}")
def run_gesture(gesture_name: str) -> JSONResponse:
    runtime = get_runtime()
    try:
        runtime.planner.execute(AgentAction(reply="Running gesture", action=gesture_name))
        return JSONResponse({"ok": True, "gesture": gesture_name})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)


@app.post("/api/ask")
def ask(command: str = Form(...)) -> JSONResponse:
    runtime = get_runtime()
    try:
        result = runtime.handle_command(command)
        return JSONResponse({"ok": True, "result": result})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)


@app.post("/api/estop")
def estop() -> dict[str, object]:
    runtime = get_runtime()
    runtime.planner.safety.stop()
    return {"ok": True, "emergency_stop": True}


@app.post("/api/reset")
def reset() -> dict[str, object]:
    runtime = get_runtime()
    runtime.planner.safety.reset()
    return {"ok": True, "emergency_stop": False}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the EmbodiedPi AI dashboard")
    parser.add_argument("--profile", default="robot_profiles/default_7_servo.yaml")
    parser.add_argument("--gesture-dir", default="gestures")
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    global _runtime
    _runtime = build_runtime(args.profile, args.gesture_dir, dry_run=args.dry_run)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
