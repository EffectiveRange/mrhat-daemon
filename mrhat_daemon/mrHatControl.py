# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
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
    PI_HB,
    REG_VAL_I2C_CLIENT_ERROR_NONE,
    REG_VAL_I2C_CLIENT_ERROR_BUS_COLLISION,
    REG_VAL_I2C_CLIENT_ERROR_WRITE_COLLISION,
    REG_VAL_I2C_CLIENT_ERROR_RECEIVE_OVERFLOW,
    REG_VAL_I2C_CLIENT_ERROR_TRANSMIT_UNDERFLOW,
    REG_VAL_I2C_CLIENT_ERROR_READ_UNDERFLOW,
    REG_ADDR_RD_END,
    REG_ADDR_WR_START,
    REG_ADDR_WR_END,
)
from mrhat_daemon import II2CControl, IPicProgrammer, IPlatformAccess, IPiGpio, I2CError

log = get_logger('MrHatControl')

REGISTER_SPACE_LENGTH = REG_ADDR_RD_END + 1


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


@dataclass
class MrHatControlConfig:
    upgrade_firmware: bool = False
    force_power_off: bool = False


class IMrHatControl(object):

    def initialize(self) -> None:
        raise NotImplementedError()

    def get_readable_registers(self) -> list[int]:
        raise NotImplementedError()

    def get_writable_registers(self) -> list[int]:
        raise NotImplementedError()

    def get_register(self, register: int) -> int:
        raise NotImplementedError()

    def set_register(self, register: int, value: int) -> None:
        raise NotImplementedError()

    def get_flag(self, register: int, flag: int) -> int:
        raise NotImplementedError()

    def set_flag(self, register: int, flag: int) -> None:
        raise NotImplementedError()

    def clear_flag(self, register: int, flag: int) -> None:
        raise NotImplementedError()


class MrHatControl(IMrHatControl):

    def __init__(
        self,
        pi_gpio: IPiGpio,
        pic_programmer: IPicProgrammer,
        i2c_control: II2CControl,
        platform_access: IPlatformAccess,
        config: MrHatControlConfig,
    ) -> None:
        self._pi_gpio = pi_gpio
        self._pic_programmer = pic_programmer
        self._i2c_control = i2c_control
        self._platform_access = platform_access
        self._config = config

    def __enter__(self) -> 'MrHatControl':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._close_connection()

    def initialize(self) -> None:
        self._pic_programmer.detect_device()

        self._open_connection()

        registers = self._get_registers_on_startup()

        self._get_device_status(registers)

        if self._check_firmware(registers) and self._config.upgrade_firmware:
            self._upgrade_firmware()

    def get_readable_registers(self) -> list[int]:
        return list(range(REGISTER_SPACE_LENGTH))

    def get_writable_registers(self) -> list[int]:
        return list(range(REG_ADDR_WR_START, REG_ADDR_WR_END + 1))

    def get_register(self, register: int) -> int:
        registers = self._get_device_registers()
        return registers[register]

    def set_register(self, register: int, value: int) -> None:
        self._i2c_control.write_register(register, value)

    def get_flag(self, register: int, flag: int) -> int:
        registers = self._get_device_registers()
        return (registers[register] & (1 << flag)) >> flag

    def set_flag(self, register: int, flag: int) -> None:
        registers = self._get_device_registers()
        value = registers[register] | (1 << flag)
        self._i2c_control.write_register(register, value)

    def clear_flag(self, register: int, flag: int) -> None:
        registers = self._get_device_registers()
        value = registers[register] & ~(1 << flag)
        self._i2c_control.write_register(register, value)

    def _open_connection(self) -> None:
        self._pi_gpio.start(self._handle_interrupt)
        self._i2c_control.open_device()

    def _close_connection(self) -> None:
        self._i2c_control.close_device()
        self._pi_gpio.stop()

    def _get_registers_on_startup(self) -> list[int]:
        try:
            registers = self._get_device_registers()
        except I2CError as error:
            log.error('Failed to read registers, possibly no firmware on device', error=error)
            self._upgrade_firmware()

            registers = self._get_device_registers()

        return registers

    def _get_device_status(self, registers: list[int]) -> list[DeviceStatus]:
        status = self._get_status_flags(registers)
        log.info('Retrieved device status', status=status)
        return status

    def _check_firmware(self, registers: list[int]) -> bool:
        current = self._get_current_firmware_version(registers)
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

    def _get_device_registers(self) -> list[int]:
        return self._i2c_control.read_block_data(REGISTER_SPACE_LENGTH)

    def _get_status_flags(self, registers: list[int]) -> list[DeviceStatus]:
        return [flag for flag in DeviceStatus if registers[REG_STAT_0_ADDR] & flag.value]

    def _get_current_firmware_version(self, registers: list[int]) -> Version:
        major = registers[REG_SW_VER_MAJOR_ADDR]
        minor = registers[REG_SW_VER_MINOR_ADDR]
        patch = registers[REG_SW_VER_PATCH_ADDR]

        return Version(f'{major}.{minor}.{patch}')

    def _get_target_firmware_version(self) -> Version:
        target_firmware = self._pic_programmer.load_firmware()
        return target_firmware.version if target_firmware else Version('0.0.0')

    def _handle_interrupt(self, gpio: int, level: int, tick: int) -> None:
        log.info('Received interrupt from the device', gpio=gpio, pin_level=level, tick=tick)

        registers = self._get_device_registers()
        status = self._get_device_status(registers)

        if DeviceStatus.SHUTDOWN_REQUESTED in status:
            force_power_off = self._config.force_power_off

            log.info("Shutdown request received, issuing 'poweroff' command", force=force_power_off)

            shutdown_command = ['poweroff']

            if force_power_off:
                shutdown_command.append('--force')

            self._platform_access.execute_command_async(shutdown_command)
