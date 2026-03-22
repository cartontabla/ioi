"""
LightingController — PCA9685 via smbus2 (no external library needed).

Channel mapping (0-indexed):
  visible:    0, 4,  8
  polarized:  1, 5,  9
  ir:         2, 6, 10
  uv:         3, 7, 11
"""
import time
import logging

GROUPS = {
    'visible':   [0, 4, 8],
    'polarized': [1, 5, 9],
    'ir':        [2, 6, 10],
    'uv':        [3, 7, 11],
}

def _percent_to_pwm(pct: float) -> int:
    """Convert 0–100% to 0–4095."""
    return int(max(0.0, min(100.0, pct)) / 100.0 * 4095)


class LightingController:
    def __init__(self, address=0x40, bus=1, freq_hz=60):
        self.address  = address
        self.bus_num  = bus
        self.freq_hz  = freq_hz
        self.available = False
        self._bus     = None
        self._init()

    def _init(self):
        try:
            from smbus2 import SMBus
            self._bus = SMBus(self.bus_num)
            self._bus.read_byte(self.address)          # check device present
            self._bus.write_byte_data(self.address, 0x00, 0x10)   # sleep
            prescale = round(25_000_000 / (4096 * self.freq_hz)) - 1
            self._bus.write_byte_data(self.address, 0xFE, prescale)
            self._bus.write_byte_data(self.address, 0x00, 0x00)   # wake
            time.sleep(0.005)
            self._bus.write_byte_data(self.address, 0x00, 0xA0)   # auto-increment
            self.available = True
            logging.info("LightingController: PCA9685 ready at 0x%02X", self.address)
        except Exception as e:
            logging.warning("LightingController: PCA9685 not available (%s)", e)
            self.available = False

    def _set_channel(self, channel: int, value: int):
        base = 0x06 + 4 * channel
        if value <= 0:
            data = [0x00, 0x00, 0x00, 0x10]   # full off
        elif value >= 4095:
            data = [0x00, 0x10, 0x00, 0x00]   # full on
        else:
            data = [0x00, 0x00, value & 0xFF, (value >> 8) & 0x0F]
        self._bus.write_i2c_block_data(self.address, base, data)

    def on(self, group: str = 'all', intensity_pct: float = 100.0):
        """Turn on a group at the given intensity (0–100%)."""
        if not self.available:
            return
        value = _percent_to_pwm(intensity_pct)
        channels = []
        if group == 'all':
            for ch_list in GROUPS.values():
                channels.extend(ch_list)
        else:
            channels = GROUPS.get(group, [])
        for ch in channels:
            self._set_channel(ch, value)

    def off(self, group: str = 'all'):
        """Turn off a group."""
        if not self.available:
            return
        channels = []
        if group == 'all':
            for ch_list in GROUPS.values():
                channels.extend(ch_list)
        else:
            channels = GROUPS.get(group, [])
        for ch in channels:
            self._set_channel(ch, 0)

    def all_off(self):
        self.off('all')
