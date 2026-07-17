# Wiring Guide

## Raspberry Pi 5 to PCA9685

| Raspberry Pi pin | PCA9685 pin | Purpose |
|---|---|---|
| 3.3V | VCC | Logic power |
| GND | GND | Shared ground |
| GPIO2 / SDA | SDA | I2C data |
| GPIO3 / SCL | SCL | I2C clock |
| External 5-6V + | V+ | Servo power |
| External supply ground | GND | Shared servo ground |

## Default 7-servo mapping

| Servo | PCA9685 channel |
|---|---:|
| front_left | 0 |
| front_right | 1 |
| mid_left | 2 |
| mid_right | 3 |
| rear_left | 4 |
| rear_right | 5 |
| body_lift | 6 |

## First power-up checklist

1. Disconnect servo horns from linkages.
2. Run `python firmware/i2c_scan.py`.
3. Test one servo at a time with `firmware/servo_test.py`.
4. Confirm each servo moves in the expected direction.
5. Set neutral angles in the profile.
6. Attach linkages only after neutral positions are confirmed.
