"""
Test script for PCA9685 lighting controller via smbus2.

Channel mapping (0-indexed):
  Visible:    0, 4, 8
  Polarized:  1, 5, 9
  IR:         2, 6, 10
  UV:         3, 7, 11
"""
import time
from smbus2 import SMBus

ADDRESS  = 0x40
BUS      = 1
FREQ_HZ  = 60

GROUPS = {
    'visible':   [0, 4, 8],
    'polarized': [1, 5, 9],
    'ir':        [2, 6, 10],
    'uv':        [3, 7, 11],
}

# --- PCA9685 low-level ---

def _init(bus):
    bus.write_byte_data(ADDRESS, 0x00, 0x10)          # MODE1: sleep
    prescale = round(25_000_000 / (4096 * FREQ_HZ)) - 1
    bus.write_byte_data(ADDRESS, 0xFE, prescale)      # set frequency
    bus.write_byte_data(ADDRESS, 0x00, 0x00)          # MODE1: normal
    time.sleep(0.005)
    bus.write_byte_data(ADDRESS, 0x00, 0xA0)          # MODE1: auto-increment

def _set_channel(bus, channel, value):
    """Set channel PWM value (0–4095)."""
    base = 0x06 + 4 * channel
    if value == 0:
        bus.write_i2c_block_data(ADDRESS, base, [0x00, 0x00, 0x00, 0x10])  # full off
    elif value >= 4095:
        bus.write_i2c_block_data(ADDRESS, base, [0x00, 0x10, 0x00, 0x00])  # full on
    else:
        bus.write_i2c_block_data(ADDRESS, base, [0x00, 0x00, value & 0xFF, (value >> 8) & 0x0F])

def set_group(bus, group, value):
    for ch in GROUPS[group]:
        _set_channel(bus, ch, value)

def all_off(bus):
    for channels in GROUPS.values():
        for ch in channels:
            _set_channel(bus, ch, 0)

# --- Test ---

def test_sequence():
    with SMBus(BUS) as bus:
        _init(bus)
        all_off(bus)
        print("PCA9685 initialized")

        for name in ('visible', 'polarized', 'ir', 'uv'):
            print(f"  Group: {name}")
            set_group(bus, name, 4095)
            time.sleep(0.8)
            set_group(bus, name, 0)
            time.sleep(0.2)

        print("Test complete. All off.")

if __name__ == '__main__':
    test_sequence()
