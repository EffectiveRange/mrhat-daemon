import unittest
from unittest import TestCase, mock
from unittest.mock import MagicMock

import pigpio
from context_logger import setup_logging

from mrhat_daemon import IPiGpio, I2CConfig, I2CControl, I2CError


class I2cControlTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('mrhat-daemon', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_startup_and_shutdown(self):
        # Given
        pi_gpio, config = create_components(0)

        # When
        with I2CControl(pi_gpio, config) as i2c_control:
            i2c_control.open_device()

        # Then
        pi_gpio.get_control().i2c_close.assert_called_once_with(0)

    def test_open_device(self):
        # Given
        pi_gpio, config = create_components()
        i2c_control = I2CControl(pi_gpio, config)

        # When
        i2c_control.open_device()

        # Then
        pi_gpio.get_control().i2c_open.assert_called_once_with(1, 0x33)

    def test_clode_device(self):
        # Given
        pi_gpio, config = create_components(2)
        i2c_control = I2CControl(pi_gpio, config)
        i2c_control.open_device()

        # When
        i2c_control.close_device()

        # Then
        pi_gpio.get_control().i2c_close.assert_called_once_with(2)

    def test_read_block_data(self):
        # Given
        pi_gpio, config = create_components(1, 10)
        i2c_control = I2CControl(pi_gpio, config)
        i2c_control.open_device()

        # When
        result = i2c_control.read_block_data(10)

        # Then
        pi_gpio.get_control().i2c_read_device.assert_called_once_with(1, 10)
        self.assertEquals([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], result)

    def test_read_block_data_when_read_raises_error(self):
        # Given
        pi_gpio, config = create_components(1, 10)
        pi_gpio.get_control().i2c_read_device.side_effect = pigpio.error(5)
        i2c_control = I2CControl(pi_gpio, config)
        i2c_control.open_device()

        # When
        self.assertRaises(I2CError, i2c_control.read_block_data, 10)

        # Then
        pi_gpio.get_control().i2c_read_device.assert_called_with(1, 10)

    def test_read_block_data_when_read_returns_error_code(self):
        # Given
        pi_gpio, config = create_components(1, 10)
        pi_gpio.get_control().i2c_read_device.return_value = -2, []
        i2c_control = I2CControl(pi_gpio, config)
        i2c_control.open_device()

        # When
        self.assertRaises(I2CError, i2c_control.read_block_data, 10)

        # Then
        pi_gpio.get_control().i2c_read_device.assert_called_with(1, 10)

    def test_read_block_data_when_read_returns_incomplete_data(self):
        # Given
        pi_gpio, config = create_components(1, 10)
        pi_gpio.get_control().i2c_read_device.return_value = 9, [0, 1, 2, 3, 4, 5, 6, 7, 8]
        i2c_control = I2CControl(pi_gpio, config)
        i2c_control.open_device()

        # When
        self.assertRaises(I2CError, i2c_control.read_block_data, 10)

        # Then
        pi_gpio.get_control().i2c_read_device.assert_called_with(1, 10)

    def test_read_block_data_when_retry_succeeds(self):
        # Given
        pi_gpio, config = create_components(1, 10)
        pi_gpio.get_control().i2c_read_device.side_effect = [
            pigpio.error(5),
            (9, [0, 1, 2, 3, 4, 5, 6, 7, 8]),
            (-2, []),
            (10, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
        ]
        i2c_control = I2CControl(pi_gpio, config)
        i2c_control.open_device()

        # When
        result = i2c_control.read_block_data(10)

        # Then
        pi_gpio.get_control().i2c_read_device.assert_has_calls([mock.call(1, 10), mock.call(1, 10)])
        self.assertEquals([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], result)


def create_components(device: int = 0, length: int = 10):
    pi_gpio = MagicMock(spec=IPiGpio)
    pi_gpio.get_control().i2c_open.return_value = device
    pi_gpio.get_control().i2c_read_device.return_value = length, [x for x in range(length)]
    config = I2CConfig(1, 0x33, 3, 0.1)

    return pi_gpio, config


if __name__ == '__main__':
    unittest.main()
