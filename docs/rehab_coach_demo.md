# EmbodiedPi Rehab Coach Demo

This is a non-medical demonstration mode showing how a small embodied agent could support rehabilitation engagement.

## Intended use

- Therapist-authored exercise reminders.
- Friendly check-ins.
- Encouragement for home-programme adherence.
- Simple logs for completed reminders.
- Caregiver prompts.

## Not intended use

- Diagnosis.
- Treatment prescription.
- Clinical assessment.
- Fall-risk assessment.
- Autonomous progression of therapy intensity.
- Replacement of therapist supervision.

## Example script idea

```yaml
script:
  name: shoulder_home_program_reminder
  prompts:
    - say: "It is time for your shoulder practice. Please check that your space is clear."
      gesture: attention
    - say: "Follow the plan your therapist gave you. Stop if you feel pain or unsafe."
      gesture: nod
    - say: "When you finish, press complete on the dashboard."
      gesture: wave
```

The same speech, gesture, safety, and logging stack used for maker robots can become a physical interface for connected care pathways, provided clinical claims are kept conservative and validation is added before healthcare deployment.
