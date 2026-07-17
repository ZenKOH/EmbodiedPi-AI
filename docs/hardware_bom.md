# Hardware Bill of Materials

## Baseline tabletop companion

| Item | Purpose | Notes |
|---|---|---|
| Raspberry Pi 5 | Main compute | 4GB works for rule/cloud mode; 8GB is better for local AI experiments. |
| Active cooler | Thermal stability | Recommended for sustained audio, vision, and dashboard use. |
| PCA9685 16-channel PWM/servo driver | Servo control | I2C-controlled multi-servo driver. |
| 3-7 micro servos | Gesture actuation | Start with 3 servos before moving to a 7-servo body. |
| External 5-6V servo supply | Servo power | Do not power multiple servos from the Pi 5V rail. |
| USB or I2S microphone | Voice input | USB is easiest for the first build. |
| Small speaker | Voice output | Keep volume low during testing. |
| Optional camera module | Perception | Useful for later object/person-presence demos. |
| Optional AI HAT+ / AI HAT+ 2 | Edge AI acceleration | Useful for supported vision and local AI workloads. |

## First prototype recommendation

Use the 3-servo profile first, verify wiring and calibration, then move to the 7-servo profile.
