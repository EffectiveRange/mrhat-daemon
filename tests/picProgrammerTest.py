import unittest
from subprocess import CompletedProcess
from unittest import TestCase
from unittest.mock import MagicMock

from common_utility import IFileDownloader
from context_logger import setup_logging
from packaging.version import Version

from mrhat_daemon import PicProgrammer, ProgrammerConfig, IPlatformAccess, ProgrammerError
from tests import TEST_RESOURCE_ROOT


class PicProgrammerTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('mrhat-daemon', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_startup_and_shutdown(self):
        # Given
        config, platform_access, file_downloader = create_components()
        config = ProgrammerConfig({'gpio_prog_en': 8, 'gpio_mclr': 11, 'gpio_clk': 6, 'gpio_data': 7})

        # When
        with PicProgrammer(config, platform_access, file_downloader) as pic_programmer:
            self.assertEquals(
                ['picprogrammer', '--gpio-prog-en', '8', '--gpio-mclr', '11', '--gpio-clk', '6', '--gpio-data', '7'],
                pic_programmer._base_command,
            )

        # Then
        platform_access.get_executable_path.assert_called_once_with('picprogrammer')

    def test_startup_when_programmer_is_not_available(self):
        # Given
        config, platform_access, file_downloader = create_components()
        platform_access.get_executable_path.return_value = None

        def create_pic_programmer():
            with PicProgrammer(config, platform_access, file_downloader):
                pass

        # When
        self.assertRaises(ProgrammerError, create_pic_programmer)

        # Then
        platform_access.get_executable_path.assert_called_once_with('picprogrammer')

    def test_detect_device_when_device_is_available(self):
        # Given
        config, platform_access, file_downloader = create_components()
        pic_programmer = PicProgrammer(config, platform_access, file_downloader)

        # When
        pic_programmer.detect_device()

        # Then
        platform_access.execute_command.assert_called_once_with(['picprogrammer', '-i'])

    def test_detect_device_raises_error_when_info_command_fails(self):
        # Given
        config, platform_access, file_downloader = create_components(1)
        pic_programmer = PicProgrammer(config, platform_access, file_downloader)

        # When
        self.assertRaises(ProgrammerError, pic_programmer.detect_device)

        # Then
        platform_access.execute_command.assert_called_once_with(['picprogrammer', '-i'])

    def test_detect_device_raises_error_when_device_id_not_found_in_info(self):
        # Given
        config, platform_access, file_downloader = create_components(device_id='PIC18F16XXX')
        pic_programmer = PicProgrammer(config, platform_access, file_downloader)

        # When
        self.assertRaises(ProgrammerError, pic_programmer.detect_device)

        # Then
        platform_access.execute_command.assert_called_once_with(['picprogrammer', '-i'])

    def test_load_firmware_file(self):
        # Given
        firmware_file = f'{TEST_RESOURCE_ROOT}/firmware/fw-mrhat-1.0.1-production.hex'
        config, platform_access, file_downloader = create_components()
        config = ProgrammerConfig(firmware_file=firmware_file)
        file_downloader.download.return_value = firmware_file
        pic_programmer = PicProgrammer(config, platform_access, file_downloader)

        # When
        result = pic_programmer.load_firmware()

        # Then
        self.assertEquals(f'{TEST_RESOURCE_ROOT}/firmware/fw-mrhat-1.0.1-production.hex', result.path)
        self.assertEquals('hex', result.format)
        self.assertEquals(Version('1.0.1'), result.version)

    def test_load_firmware_file_when_no_extension(self):
        # Given
        firmware_file = f'{TEST_RESOURCE_ROOT}/firmware/fw-mrhat-1.0.0-production'
        config, platform_access, file_downloader = create_components()
        config = ProgrammerConfig(firmware_file=firmware_file)
        file_downloader.download.return_value = firmware_file
        pic_programmer = PicProgrammer(config, platform_access, file_downloader)

        # When
        result = pic_programmer.load_firmware()

        # Then
        self.assertEquals(f'{TEST_RESOURCE_ROOT}/firmware/fw-mrhat-1.0.0-production', result.path)
        self.assertEquals('hex', result.format)
        self.assertEquals(Version('1.0.0'), result.version)

    def test_load_firmware_file_when_no_version(self):
        # Given
        firmware_file = f'{TEST_RESOURCE_ROOT}/firmware/fw-mrhat-production.hex'
        config, platform_access, file_downloader = create_components()
        config = ProgrammerConfig(firmware_file=firmware_file)
        file_downloader.download.return_value = firmware_file
        pic_programmer = PicProgrammer(config, platform_access, file_downloader)

        # When
        result = pic_programmer.load_firmware()

        # Then
        self.assertEquals(f'{TEST_RESOURCE_ROOT}/firmware/fw-mrhat-production.hex', result.path)
        self.assertEquals('hex', result.format)
        self.assertEquals(Version('0.0.0'), result.version)

    def test_load_firmware_file_when_file_not_exists(self):
        # Given
        firmware_file = f'{TEST_RESOURCE_ROOT}/firmware/fw-mrhat-production.hex'
        config, platform_access, file_downloader = create_components()
        config = ProgrammerConfig(firmware_file=firmware_file)
        file_downloader.download.side_effect = FileNotFoundError(firmware_file)
        pic_programmer = PicProgrammer(config, platform_access, file_downloader)

        # When
        result = pic_programmer.load_firmware()

        # Then
        self.assertIsNone(result)

    def test_load_latest_firmware_file(self):
        # Given
        firmware_dir = f'{TEST_RESOURCE_ROOT}/firmware'
        config, platform_access, file_downloader = create_components()
        config = ProgrammerConfig(firmware_dir=firmware_dir)
        pic_programmer = PicProgrammer(config, platform_access, file_downloader)

        # When
        result = pic_programmer.load_firmware()

        # Then
        self.assertEquals(f'{TEST_RESOURCE_ROOT}/firmware/fw-mrhat-1.1.1-production.hex', result.path)
        self.assertEquals('hex', result.format)
        self.assertEquals(Version('1.1.1'), result.version)

    def test_load_latest_firmware_file_when_directory_not_exists(self):
        # Given
        firmware_dir = f'{TEST_RESOURCE_ROOT}/invalid'
        config, platform_access, file_downloader = create_components()
        config = ProgrammerConfig(firmware_dir=firmware_dir)
        pic_programmer = PicProgrammer(config, platform_access, file_downloader)

        # When
        result = pic_programmer.load_firmware()

        # Then
        self.assertIsNone(result)

    def test_load_latest_firmware_file_when_file_not_exists(self):
        # Given
        firmware_file = f'{TEST_RESOURCE_ROOT}/firmware/fw-mrhat-production.hex'
        firmware_dir = f'{TEST_RESOURCE_ROOT}/firmware'
        config, platform_access, file_downloader = create_components()
        config = ProgrammerConfig(firmware_file=firmware_file, firmware_dir=firmware_dir)
        file_downloader.download.side_effect = FileNotFoundError(firmware_file)
        pic_programmer = PicProgrammer(config, platform_access, file_downloader)

        # When
        result = pic_programmer.load_firmware()

        # Then
        self.assertEquals(f'{TEST_RESOURCE_ROOT}/firmware/fw-mrhat-1.1.1-production.hex', result.path)
        self.assertEquals('hex', result.format)
        self.assertEquals(Version('1.1.1'), result.version)

    def test_upgrade_firmware_when_device_is_available(self):
        # Given
        firmware_dir = f'{TEST_RESOURCE_ROOT}/firmware'
        config, platform_access, file_downloader = create_components()
        config = ProgrammerConfig(firmware_dir=firmware_dir)
        pic_programmer = PicProgrammer(config, platform_access, file_downloader)

        # When
        pic_programmer.upgrade_firmware()

        # Then
        platform_access.execute_command.assert_called_once_with(
            ['picprogrammer', '-f', f'{TEST_RESOURCE_ROOT}/firmware/fw-mrhat-1.1.1-production.hex', '--hex', '--write']
        )

    def test_upgrade_firmware_raises_error_when_no_firmware_file(self):
        # Given
        firmware_dir = f'{TEST_RESOURCE_ROOT}/invalid'
        config, platform_access, file_downloader = create_components()
        config = ProgrammerConfig(firmware_dir=firmware_dir)
        pic_programmer = PicProgrammer(config, platform_access, file_downloader)

        # When, Then
        self.assertRaises(ProgrammerError, pic_programmer.upgrade_firmware)

    def test_upgrade_firmware_raises_error_when_upgrade_fails(self):
        # Given
        firmware_dir = f'{TEST_RESOURCE_ROOT}/firmware'
        config, platform_access, file_downloader = create_components(1)
        config = ProgrammerConfig(firmware_dir=firmware_dir)
        pic_programmer = PicProgrammer(config, platform_access, file_downloader)

        # When
        self.assertRaises(ProgrammerError, pic_programmer.upgrade_firmware)

        # Then
        platform_access.execute_command.assert_called_once_with(
            ['picprogrammer', '-f', f'{TEST_RESOURCE_ROOT}/firmware/fw-mrhat-1.1.1-production.hex', '--hex', '--write']
        )


def get_device_info(device_id: str):
    return f'''Device Id: 0x7a40 ({device_id})
Revision Id: 0xa042 (B2)
Device Configuration Information:
  Erase page size: 128 words
  No. of erasable pages: 256 pages
  EEPROM size: 256 bytes
  Pin count: 20 pins
Device Information Area:
  Microchip UID: 4232:6111:9161:1613:2000:ffff:ffff:ffff:ffff
  Optional Ext. UID: ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff
  Temperature Sensor Parameters(low range):
    Gain: 0xf59f (0.000407 C_deg)
    ADC 90 deg. reading: 0x01dd
    Offset: 0x16a8
  Temperature Sensor Parameters(high range):
    Gain: 0xf902 (0.000402 C_deg)
    ADC 90 deg. reading: 0x028c
    Offset: 0x1523
Fixed Voltage Reference Data:
  ADC FVR1 Output Voltage 1X: 0x0401 (1025 mV)
  ADC FVR1 Output Voltage 2X: 0x0803 (2051 mV)
  ADC FVR1 Output Voltage 4X: 0x1002 (4098 mV)
  Comparator FVR2 Output Voltage 1X: 0xffff (65535 mV)
  Comparator FVR2 Output Voltage 2X: 0xffff (65535 mV)
  Comparator FVR2 Output Voltage 4X: 0xffff (65535 mV)'''


def create_components(return_code: int = 0, device_id: str = 'PIC18F16Q20'):
    config = ProgrammerConfig()
    platform_access = MagicMock(spec=IPlatformAccess)
    platform_access.get_executable_path.return_value = '/usr/local/bin/picprogrammer'
    completed_process = MagicMock(spec=CompletedProcess)
    completed_process.returncode = return_code
    completed_process.stdout = get_device_info(device_id)
    platform_access.execute_command.return_value = completed_process
    file_downloader = MagicMock(spec=IFileDownloader)

    return config, platform_access, file_downloader


if __name__ == '__main__':
    unittest.main()
