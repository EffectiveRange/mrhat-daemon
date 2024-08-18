# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable

import pigpio
from context_logger import get_logger

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

    def __init__(self, message: str, error: Any, data: list[int]) -> None:
        super().__init__(message)
        self.message = message
        self.error = error
        self.data = data


class II2CControl(object):

    def open_device(self) -> None:
        raise NotImplementedError()

    def close_device(self) -> None:
        raise NotImplementedError()

    def read_block_data(self, length: int) -> list[int]:
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

    def read_block_data(self, length: int) -> list[int]:
        return list(self._i2c_transaction(self._read_block_data, length))

    def _i2c_transaction(self, operation: Callable[..., Any], *args: Any) -> Any:
        try:
            self._lock.acquire()

            for retry in range(1, self._retry_limit + 1):
                try:
                    return operation(*args)
                except I2CError as error:
                    if retry > self._retry_limit:
                        raise error
                    log.warn(f'{error.message} -> retrying', error=error.error, data=error.data, retry=retry)
                    time.sleep(self._retry_delay)
        finally:
            self._lock.release()

    def _read_block_data(self, length: int) -> list[int]:
        control = self._pi_gpio.control()

        try:
            count, byte_data = control.i2c_read_device(self._device, length)
            data = [x for x in byte_data]
        except pigpio.error as error:
            raise I2CError('Failed to read I2C block data (exception)', error=error, data=[])

        if count < 0:
            raise I2CError('Failed to read I2C block data (error code)', error=count, data=data)

        if count != length:
            raise I2CError('Failed to read I2C block data (incomplete)', error=count, data=data)

        log.info('I2C block data read completed', data=data)

        return data
