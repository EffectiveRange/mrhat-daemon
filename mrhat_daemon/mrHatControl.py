# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT
from enum import Enum
from typing import Any

from context_logger import get_logger
from packaging.version import Version

from generated import (
    REG_STAT_0_ADDR,
    REG_SW_VER_MAJOR_ADDR,
    REG_SW_VER_MINOR_ADDR,
    REG_SW_VER_PATCH_ADDR,
    SHUT_REQ,
    REG_STAT_I2C_ERR_AND_STICKY_ADDR,
    PI_HB,
    REG_VAL_I2C_CLIENT_ERROR_NONE,
    REG_VAL_I2C_CLIENT_ERROR_BUS_COLLISION,
    REG_VAL_I2C_CLIENT_ERROR_WRITE_COLLISION,
    REG_VAL_I2C_CLIENT_ERROR_RECEIVE_OVERFLOW,
    REG_VAL_I2C_CLIENT_ERROR_TRANSMIT_UNDERFLOW,
    REG_VAL_I2C_CLIENT_ERROR_READ_UNDERFLOW,
)
from mrhat_daemon import II2CControl, IPicProgrammer, IPlatformAccess, IPiGpio

log = get_logger('MrHatControl')


class DeviceStatus(Enum):
    SHUTDOWN_REQUESTED = SHUT_REQ
    PI_HEART_BEAT_OK = PI_HB


class I2CStatus(Enum):
    NO_ERROR = REG_VAL_I2C_CLIENT_ERROR_NONE
    BUS_COLLISION = REG_VAL_I2C_CLIENT_ERROR_BUS_COLLISION
    WRITE_COLLISION = REG_VAL_I2C_CLIENT_ERROR_WRITE_COLLISION
    RECEIVE_OVERFLOW = REG_VAL_I2C_CLIENT_ERROR_RECEIVE_OVERFLOW
    TRANSMIT_UNDERFLOW = REG_VAL_I2C_CLIENT_ERROR_TRANSMIT_UNDERFLOW
    READ_UNDERFLOW = REG_VAL_I2C_CLIENT_ERROR_READ_UNDERFLOW


class IMrHatControl(object):

    def initialize(self) -> None:
        raise NotImplementedError()


class MrHatControl(IMrHatControl):

    def __init__(
        self,
        pi_gpio: IPiGpio,
        pic_programmer: IPicProgrammer,
        i2c_control: II2CControl,
        platform_access: IPlatformAccess,
    ) -> None:
        self._pi_gpio = pi_gpio
        self._pic_programmer = pic_programmer
        self._i2c_control = i2c_control
        self._platform_access = platform_access

    def __enter__(self) -> 'MrHatControl':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._close_connection()

    def initialize(self) -> None:
        self._pic_programmer.detect_device()

        self._open_connection()

        self._get_initial_status()

        if self._check_firmware():
            self._upgrade_firmware()

    def _open_connection(self) -> None:
        self._pi_gpio.start(self._handle_interrupt)
        self._i2c_control.open_device()

    def _close_connection(self) -> None:
        self._i2c_control.close_device()
        self._pi_gpio.stop()

    def _get_initial_status(self) -> None:
        status = self._get_status_flags()
        i2c_status = I2CStatus(self._get_i2c_status() & 0x0F)
        log.info('Initial status', status=status, i2c_status=i2c_status)

    def _check_firmware(self) -> bool:
        current = self._get_current_firmware_version()
        target = self._get_target_firmware_version()

        if current < target:
            log.info('Current firmware version is older than target version', current=current, target=target)
            return True
        elif current > target:
            log.info('Current firmware version is newer than target version', current=current, target=target)
        else:
            log.info('Firmware is up to date', current=current, target=target)

        return False

    def _upgrade_firmware(self) -> None:
        self._close_connection()

        self._pic_programmer.upgrade_firmware()

        self._open_connection()

    def _get_status_flags(self) -> list[DeviceStatus]:
        status = self._i2c_control.read_register(REG_STAT_0_ADDR)
        return [flag for flag in DeviceStatus if status & flag.value]

    def _get_i2c_status(self) -> int:
        return self._i2c_control.read_register(REG_STAT_I2C_ERR_AND_STICKY_ADDR)

    def _get_current_firmware_version(self) -> Version:
        major = self._i2c_control.read_register(REG_SW_VER_MAJOR_ADDR)
        minor = self._i2c_control.read_register(REG_SW_VER_MINOR_ADDR)
        patch = self._i2c_control.read_register(REG_SW_VER_PATCH_ADDR)

        return Version(f'{major}.{minor}.{patch}')

    def _get_target_firmware_version(self) -> Version:
        return self._pic_programmer.load_firmware().version

    def _handle_interrupt(self, gpio: int, level: int, tick: int) -> None:
        log.info('Received interrupt from the device, reading status', gpio=gpio, pin_level=level, tick=tick)

        status = self._get_status_flags()

        log.info('Read device status', status=status)

        if DeviceStatus.SHUTDOWN_REQUESTED in status:
            log.info('Shutdown request received, shutting down')
            self._platform_access.execute_command_async(['shutdown'])
