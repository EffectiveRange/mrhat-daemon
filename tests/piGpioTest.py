import unittest
from unittest import TestCase
from unittest.mock import MagicMock

from context_logger import setup_logging
from pigpio import pi
from systemd_dbus import Systemd

from mrhat_daemon import IPlatformAccess, ServiceConfig, InterruptConfig, PiGpio, GpioPullType, GpioEdgeType


class PiGpioTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('mrhat-daemon', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_startup_and_shutdown(self):
        # Given
        systemd, platform_access, service_config, interrupt_config, pi_mock = create_components()

        # When
        with PiGpio(systemd, platform_access, service_config, interrupt_config):
            platform_access.get_executable_path.assert_called_once_with('pigpiod')
            systemd.stop_service.assert_called_once_with('pigpiod')
            systemd.reset_mock()

        # Then
        systemd.stop_service.assert_called_once_with('pigpiod')

    def test_start_pigpio(self):
        # Given
        systemd, platform_access, service_config, interrupt_config, pi_mock = create_components()
        systemd.is_active.return_value = True
        pi_gpio = PiGpio(systemd, platform_access, service_config, interrupt_config, lambda: pi_mock)
        callback = MagicMock()

        # When
        pi_gpio.start(callback)

        # Then
        systemd.start_service.assert_called_once_with('pigpiod')
        pi_mock.callback.assert_called_once_with(interrupt_config.gpio_pin, interrupt_config.edge_type.value, callback)


def create_components():
    systemd = MagicMock(spec=Systemd)
    systemd.is_active.return_value = False
    platform_access = MagicMock(spec=IPlatformAccess)
    platform_access.get_executable_path.return_value = '/usr/bin/pigpiod'
    service_config = ServiceConfig(3, 0.1)
    interrupt_config = InterruptConfig(27, GpioPullType.PULL_UP, GpioEdgeType.FALLING_EDGE)
    pi_mock = MagicMock(spec=pi)
    pi_mock.connected = True

    return systemd, platform_access, service_config, interrupt_config, pi_mock


if __name__ == '__main__':
    unittest.main()
