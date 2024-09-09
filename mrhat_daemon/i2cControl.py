# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable, Optional, Union

import pigpio
from context_logger import get_logger

from mrhat_daemon import IPiGpio

log = get_logger('I2CControl')

I2C_NO_DEVICE = -1
I2C_ERR_CLEAN = 0x80


@dataclass
class I2CConfig:
    bus_id: int
    address: int
    retry_limit: int
    retry_delay: float


class I2CError(Exception):

    def __init__(self, message: str, error: Any, data: Union[int, list[int]], register: Optional[int] = None) -> None:
        super().__init__(message)
        self.message = message
        self.error = error
        self.data = data
        self.register = register

    def __repr__(self) -> str:
        properties = f'{self.message}, error={self.error}, data={self.data}'

        if self.register is not None:
            properties += f', register={self.register}'

        return f'I2CError({properties})'


class II2CControl(object):

    def open_device(self) -> None:
        raise NotImplementedError()

    def close_device(self) -> None:
        raise NotImplementedError()

    def read_block_data(self, length: int) -> list[int]:
        raise NotImplementedError()

    def write_register(self, register: int, data: int) -> None:
        raise NotImplementedError()


class I2CControl(II2CControl):

    def __init__(self, pi_gpio: IPiGpio, config: I2CConfig):
        self._pi_gpio = pi_gpio
        self._i2c_bus_id = config.bus_id
        self._i2c_address = config.address
        self._retry_limit = config.retry_limit
        self._retry_delay = config.retry_delay
        self._device = I2C_NO_DEVICE
        self._lock = Lock()

    def __enter__(self) -> 'I2CControl':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close_device()

    def open_device(self) -> None:
        with self._lock:
            if self._device == I2C_NO_DEVICE:
                control = self._pi_gpio.get_control()
                self._device = control.i2c_open(self._i2c_bus_id, self._i2c_address)
                log.info('Opened I2C device', bus=self._i2c_bus_id, address=self._i2c_address, device=self._device)

    def close_device(self) -> None:
        with self._lock:
            if self._device != I2C_NO_DEVICE:
                control = self._pi_gpio.get_control()
                control.i2c_close(self._device)
                log.info('Closed I2C device', bus=self._i2c_bus_id, address=self._i2c_address, device=self._device)
                self._device = I2C_NO_DEVICE

    def read_block_data(self, length: int) -> list[int]:
        return list(self._i2c_transaction(self._read_block_data, length))

    def write_register(self, register: int, data: int) -> None:
        self._i2c_transaction(self._write_register, register, data)

    def _i2c_transaction(self, operation: Callable[..., Any], *args: Any) -> Any:
        self.open_device()

        with self._lock:
            for retry in range(0, self._retry_limit + 1):
                try:
                    return operation(*args)
                except I2CError as error:
                    if retry == self._retry_limit:
                        log.error(f'{error.message} -> giving up', error=error, retry=retry)
                        raise error
                    log.warn(f'{error.message} -> retrying', error=error, retry=retry)
                    time.sleep(self._retry_delay)

    def _read_block_data(self, length: int) -> list[int]:
        control = self._pi_gpio.get_control()

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

    def _write_register(self, register: int, data: int) -> None:
        control = self._pi_gpio.get_control()

        try:
            result: int = control.i2c_write_byte_data(self._device, register, data)
        except pigpio.error as error:
            raise I2CError('Failed to write I2C register (exception)', error=error, data=data, register=register)

        if result < 0:
            raise I2CError('Failed to write I2C register (error code)', error=result, data=data, register=register)

        log.info('I2C register write completed', result=result, data=data)
