# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import time
from dataclasses import dataclass
from enum import Enum
from shutil import which
from typing import Any, Callable, Optional

import pigpio
from context_logger import get_logger
from pigpio import pi
from systemd_dbus import Systemd

log = get_logger('PiGpio')


class GpioPullType(Enum):
    PULL_UP = pigpio.PUD_UP
    PULL_DOWN = pigpio.PUD_DOWN
    PULL_OFF = pigpio.PUD_OFF

    def __repr__(self) -> str:
        return str(self.value)


class GpioEdgeType(Enum):
    RISING_EDGE = pigpio.RISING_EDGE
    FALLING_EDGE = pigpio.FALLING_EDGE
    EITHER_EDGE = pigpio.EITHER_EDGE

    def __repr__(self) -> str:
        return str(self.value)


@dataclass
class ServiceConfig:
    retry_limit: int
    retry_delay: float


@dataclass
class InterruptConfig:
    gpio_pin: int
    pull_type: GpioPullType
    edge_type: GpioEdgeType


class PiGpioError(Exception):

    def __init__(self, message: str):
        super().__init__(message)


class IPiGpio(object):

    def start(self, handler: Optional[Callable[[int, int, int], None]] = None) -> None:
        raise NotImplementedError()

    def stop(self) -> None:
        raise NotImplementedError()

    def control(self) -> pi:
        raise NotImplementedError()


class PiGpio(IPiGpio):
    SERVICE_NAME = 'pigpiod'

    def __init__(self, systemd: Systemd, service_config: ServiceConfig, interrupt_config: InterruptConfig) -> None:
        self._systemd = systemd
        self._service_config = service_config
        self._interrupt_config = interrupt_config
        self._interrupt_handler = None
        self._pi = None
        self._callback = None

    def __enter__(self) -> 'PiGpio':
        self._check_service()
        self.stop()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()

    def start(self, handler: Optional[Callable[[int, int, int], None]] = None) -> None:
        self._wait_for_service_state(True)

        if not self._pi:
            self._pi = pi()

        if self._pi and self._pi.connected:
            self._set_up_interrupt(handler)

    def stop(self) -> None:
        if self._pi:
            if self._pi.connected:
                self._cancel_interrupt()
                self._pi.stop()
            self._pi = None

        self._wait_for_service_state(False)

    def control(self) -> pi:
        if not self._pi or not self._pi.connected:
            self.start()

        return self._pi

    def _check_service(self) -> None:
        if not (service := which(self.SERVICE_NAME)):
            log.error('Service is not available', service=self.SERVICE_NAME)
            raise PiGpioError('Service is not available')

        log.info('Service is available', service=self.SERVICE_NAME, path=service)

    def _wait_for_service_state(self, active: bool) -> None:
        if active:
            self._systemd.start_service(self.SERVICE_NAME)
            state = 'active'
        else:
            self._systemd.stop_service(self.SERVICE_NAME)
            state = 'inactive'

        config = self._service_config
        for retry in range(1, config.retry_limit + 1):
            if self._systemd.is_active(self.SERVICE_NAME) == active:
                return
            else:
                if retry == config.retry_limit:
                    log.error(f'Service failed to enter {state} state', service=self.SERVICE_NAME)
                    raise PiGpioError(f'Service failed to enter {state} state')

                log.info(f'Waiting for service to enter {state} state', service=self.SERVICE_NAME, retry=retry)
                time.sleep(config.retry_delay)

    def _set_up_interrupt(self, handler: Optional[Callable[[int, int, int], None]] = None) -> None:
        if handler and self._pi:
            config = self._interrupt_config
            self._pi.set_mode(config.gpio_pin, pigpio.INPUT)
            self._pi.set_pull_up_down(config.gpio_pin, config.pull_type.value)
            self._callback = self._pi.callback(config.gpio_pin, config.edge_type.value, handler)

    def _cancel_interrupt(self) -> None:
        if self._callback:
            self._callback.cancel()
            self._callback = None
