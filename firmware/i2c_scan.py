#!/usr/bin/env python3
from __future__ import annotations


def main() -> None:
    try:
        import board
        import busio
    except ImportError as exc:
        raise SystemExit("Install Pi dependencies with `pip install -e .[pi]` first") from exc

    i2c = busio.I2C(board.SCL, board.SDA)
    while not i2c.try_lock():
        pass
    try:
        devices = i2c.scan()
    finally:
        i2c.unlock()

    if not devices:
        print("No I2C devices found")
        return
    print("I2C devices:")
    for address in devices:
        print(f"- 0x{address:02x}")


if __name__ == "__main__":
    main()
