import unittest
from unittest import TestCase, mock
from unittest.mock import MagicMock

from context_logger import setup_logging
from packaging.version import Version

from generated import (
    REG_STAT_0_ADDR,
    REG_STAT_I2C_ERR_AND_STICKY_ADDR,
    REG_SW_VER_MAJOR_ADDR,
    REG_SW_VER_MINOR_ADDR,
    REG_SW_VER_PATCH_ADDR,
)
from mrhat_daemon import MrHatControl, IPiGpio, IPicProgrammer, II2CControl, IPlatformAccess, FirmwareFile


class MrHatControlTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('mrhat-daemon', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_startup_and_shutdown(self):
        # Given
        pi_gpio, pic_programmer, i2c_control, platform_access = create_components()

        # When
        with MrHatControl(pi_gpio, pic_programmer, i2c_control, platform_access):
            pass

        # Then
        i2c_control.close_device.assert_called_once()
        pi_gpio.stop.assert_called_once()

    def test_initialize_when_running_firmware_is_up_to_date(self):
        # Given
        pi_gpio, pic_programmer, i2c_control, platform_access = create_components()
        mr_hat_control = MrHatControl(pi_gpio, pic_programmer, i2c_control, platform_access)

        # When
        mr_hat_control.initialize()

        # Then
        pic_programmer.detect_device.assert_called_once()
        pi_gpio.start.assert_called_once_with(mr_hat_control._handle_interrupt)
        i2c_control.open_device.assert_called_once()
        i2c_control.read_register.assert_has_calls(
            [
                mock.call(REG_STAT_0_ADDR),
                mock.call(REG_STAT_I2C_ERR_AND_STICKY_ADDR),
                mock.call(REG_SW_VER_MAJOR_ADDR),
                mock.call(REG_SW_VER_MINOR_ADDR),
                mock.call(REG_SW_VER_PATCH_ADDR),
            ]
        )

    def test_initialize_when_running_firmware_is_later(self):
        # Given
        pi_gpio, pic_programmer, i2c_control, platform_access = create_components([0x02, 0x80, 0x01, 0x01, 0x00])
        mr_hat_control = MrHatControl(pi_gpio, pic_programmer, i2c_control, platform_access)

        # When
        mr_hat_control.initialize()

        # Then
        pic_programmer.detect_device.assert_called_once()
        pi_gpio.start.assert_called_once_with(mr_hat_control._handle_interrupt)
        i2c_control.open_device.assert_called_once()
        i2c_control.read_register.assert_has_calls(
            [
                mock.call(REG_STAT_0_ADDR),
                mock.call(REG_STAT_I2C_ERR_AND_STICKY_ADDR),
                mock.call(REG_SW_VER_MAJOR_ADDR),
                mock.call(REG_SW_VER_MINOR_ADDR),
                mock.call(REG_SW_VER_PATCH_ADDR),
            ]
        )

    def test_initialize_when_running_firmware_needs_update(self):
        # Given
        pi_gpio, pic_programmer, i2c_control, platform_access = create_components([0x02, 0x80, 0x01, 0x00, 0x00])
        mr_hat_control = MrHatControl(pi_gpio, pic_programmer, i2c_control, platform_access)

        # When
        mr_hat_control.initialize()

        # Then
        pic_programmer.detect_device.assert_called_once()
        pi_gpio.start.assert_called_with(mr_hat_control._handle_interrupt)
        i2c_control.open_device.assert_called()
        i2c_control.read_register.assert_has_calls(
            [
                mock.call(REG_STAT_0_ADDR),
                mock.call(REG_STAT_I2C_ERR_AND_STICKY_ADDR),
                mock.call(REG_SW_VER_MAJOR_ADDR),
                mock.call(REG_SW_VER_MINOR_ADDR),
                mock.call(REG_SW_VER_PATCH_ADDR),
            ]
        )
        i2c_control.close_device.assert_called()
        pic_programmer.upgrade_firmware.assert_called_once()

    def test_handling_interrupt_when_shutdown_not_requested(self):
        # Given
        pi_gpio, pic_programmer, i2c_control, platform_access = create_components([0x02])
        mr_hat_control = MrHatControl(pi_gpio, pic_programmer, i2c_control, platform_access)

        # When
        mr_hat_control._handle_interrupt(27, 0, 12345678)

        # Then
        i2c_control.read_register.assert_called_once_with(REG_STAT_0_ADDR)
        platform_access.execute_command_async.assert_not_called()

    def test_handling_interrupt_when_shutdown_requested(self):
        # Given
        pi_gpio, pic_programmer, i2c_control, platform_access = create_components([0x03])
        mr_hat_control = MrHatControl(pi_gpio, pic_programmer, i2c_control, platform_access)

        # When
        mr_hat_control._handle_interrupt(27, 0, 12345678)

        # Then
        i2c_control.read_register.assert_called_once_with(REG_STAT_0_ADDR)
        platform_access.execute_command_async.assert_called_once_with(['shutdown'])


def create_components(i2c_data=None):
    if i2c_data is None:
        i2c_data = [0x02, 0x80, 0x01, 0x00, 0x01]
    pi_gpio = MagicMock(spec=IPiGpio)
    pic_programmer = MagicMock(spec=IPicProgrammer)
    pic_programmer.load_firmware.return_value = FirmwareFile('', '', Version('1.0.1'))
    i2c_control = MagicMock(spec=II2CControl)
    i2c_control.read_register.side_effect = i2c_data
    platform_access = MagicMock(spec=IPlatformAccess)

    return pi_gpio, pic_programmer, i2c_control, platform_access


if __name__ == '__main__':
    unittest.main()
