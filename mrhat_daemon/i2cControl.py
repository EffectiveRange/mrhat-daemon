# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Optional, Callable

import pigpio
from context_logger import get_logger

from generated import REG_STAT_I2C_ERR_AND_STICKY_ADDR, REG_VAL_I2C_CLIENT_ERROR_READ_UNDERFLOW
from mrhat_daemon import IPiGpio

log = get_logger('I2CControl')

I2C_ERR_CLEAN = 0x80


@dataclass
class I2CConfig:
    bus_id: int
    address: int
    retry_limit: int
    retry_delay: float


class I2CError(Exception):

    def __init__(
        self, message: str, operation: str, register: int, data: Optional[int] = None, error: Optional[Any] = None
    ) -> None:
        super().__init__(message)
        self.operation = operation
        self.register = register
        self.data = data
        self.error = error


class II2CControl(object):

    def open_device(self) -> None:
        raise NotImplementedError()

    def close_device(self) -> None:
        raise NotImplementedError()

    def write_register(self, register: int, data: int) -> None:
        raise NotImplementedError()

    def read_register(self, register: int) -> int:
        raise NotImplementedError()


class I2CControl(II2CControl):

    def __init__(self, pi_gpio: IPiGpio, config: I2CConfig):
        self._pi_gpio = pi_gpio
        self._i2c_bus_id = config.bus_id
        self._i2c_address = config.address
        self._retry_limit = config.retry_limit
        self._retry_delay = config.retry_delay
        self._device = None
        self._lock = Lock()

    def __enter__(self) -> 'I2CControl':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close_device()

    def open_device(self) -> None:
        if not self._device:
            self._lock.acquire()

            control = self._pi_gpio.control()
            self._device = control.i2c_open(self._i2c_bus_id, self._i2c_address)
            log.info('Opened I2C device', bus=self._i2c_bus_id, address=self._i2c_address, device=self._device)

            self._lock.release()

    def close_device(self) -> None:
        if self._device is not None:
            self._lock.acquire()

            control = self._pi_gpio.control()
            control.i2c_close(self._device)
            log.info('Closed I2C device', bus=self._i2c_bus_id, address=self._i2c_address, device=self._device)
            self._device = None

            self._lock.release()

    def read_register(self, register: int) -> int:
        return int(self._register_transaction(self._safe_read_register, register))

    def write_register(self, register: int, data: int) -> None:
        self._register_transaction(self._safe_write_register, register, data)

    def _register_transaction(self, operation: Callable[..., Any], *args: Any) -> Any:
        try:
            self._lock.acquire()

            for retry in range(1, self._retry_limit + 1):
                try:
                    return operation(*args)
                except I2CError as error:
                    if retry == self._retry_limit:
                        raise error
                    log.warn(
                        'I2C transaction failed, retrying',
                        operation=error.operation,
                        register=error.register,
                        data=error.data,
                        retry=retry,
                    )
                    time.sleep(self._retry_delay)
        finally:
            self._lock.release()

    def _safe_read_register(self, register: int) -> int:
        data = self._direct_read_register(register)
        status = self._direct_read_register(REG_STAT_I2C_ERR_AND_STICKY_ADDR)

        if status not in [I2C_ERR_CLEAN, I2C_ERR_CLEAN + REG_VAL_I2C_CLIENT_ERROR_READ_UNDERFLOW]:
            self._direct_write_register(REG_STAT_I2C_ERR_AND_STICKY_ADDR, I2C_ERR_CLEAN)

            if status == 0x00:
                raise I2CError('Failed to read I2C status register', 'read', REG_STAT_I2C_ERR_AND_STICKY_ADDR, status)
            else:
                raise I2CError('Failed to read I2C data register', 'read', register, data)
        else:
            log.info('I2C register read completed', register=register, data=data)

        return data

    def _safe_write_register(self, register: int, data: int) -> None:
        result = self._direct_write_register(register, data)

        if result < 0:
            raise I2CError('Failed to write I2C register', 'write', register, data, result)

        data_back = self.read_register(register)

        if data_back != data:
            raise I2CError('Read-back value mismatch', 'write', register, data, data_back)

        log.info('I2C register write completed', register=register, data=data)

    def _direct_read_register(self, register: int) -> int:
        control = self._pi_gpio.control()

        try:
            data: int = control.i2c_read_byte_data(self._device, register)
        except pigpio.error as error:
            raise I2CError('Failed to read I2C register', 'read', register, error=error)

        log.debug('I2C register direct read completed', register=register, data=data)

        return data

    def _direct_write_register(self, register: int, data: int) -> int:
        control = self._pi_gpio.control()

        try:
            result: int = control.i2c_write_byte_data(self._device, register, data)
        except pigpio.error as error:
            raise I2CError('Failed to write I2C register', 'write', register, data, error)

        log.debug('I2C register direct write completed', register=register, data=data)

        return result
