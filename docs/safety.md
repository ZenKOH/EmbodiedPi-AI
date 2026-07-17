# Safety Model

EmbodiedPi AI is designed around one rule: untrusted AI output must never control raw hardware directly.

## Guardrails

- The LLM may select only known gesture names.
- Gesture files use named servos, not arbitrary hardware channels.
- The planner rejects unknown servos, unknown actions, out-of-range angles, negative durations, unsafe frame durations, and emergency-stop state.
- Dry-run mode is the default for laptop development and first-time setup.

## Hardware safety

- Do not power multiple servos from the Raspberry Pi rail.
- Use a separate servo power supply with a shared ground.
- Start with servo horns disconnected.
- Test one servo at a time at low speed before attaching the robot body.
- Keep fingers, hair, and loose wires away from moving linkages.
- Add physical strain relief for servo leads.

## AI safety

- Keep the system in approved-action mode.
- Do not allow free-form model output to write gesture files while hardware is connected.
- Review generated gestures manually before running them on hardware.
- Log action decisions for review.

## Rehabilitation disclaimer

The rehabilitation coach demo is for engagement, reminders, and education. It is not a medical device and must not be used for diagnosis, treatment, assessment, clinical triage, or unsupervised therapy progression.
