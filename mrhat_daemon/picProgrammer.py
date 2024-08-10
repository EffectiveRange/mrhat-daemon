# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import re
from dataclasses import dataclass
from os import listdir
from shutil import which
from typing import Any, Tuple, Optional

from common_utility import IFileDownloader
from context_logger import get_logger
from packaging.version import Version, InvalidVersion

from mrhat_daemon import IPlatformAccess

log = get_logger('PicProgrammer')


@dataclass
class ProgrammerConfig:
    firmware_dir: Optional[str]
    firmware_file: Optional[str]
    gpio_options: dict[str, Any]


@dataclass
class FirmwareFile:
    path: str
    format: str
    version: Version


class ProgrammerError(Exception):

    def __init__(self, message: str) -> None:
        super().__init__(message)


class IPicProgrammer(object):

    def detect_device(self) -> None:
        raise NotImplementedError()

    def load_firmware(self) -> FirmwareFile:
        raise NotImplementedError()

    def upgrade_firmware(self) -> None:
        raise NotImplementedError()


class PicProgrammer(IPicProgrammer):
    PROGRAMMER = 'picprogrammer'
    DEVICE_ID = 'PIC18F16Q20'

    def __init__(
        self,
        config: ProgrammerConfig,
        platform_access: IPlatformAccess,
        file_downloader: IFileDownloader,
    ) -> None:
        self._base_command = self._get_base_command(config.gpio_options)
        self._firmware_dir = config.firmware_dir
        self._firmware_file = config.firmware_file
        self._platform_access = platform_access
        self._file_downloader = file_downloader
        self._target_firmware: Optional[FirmwareFile] = None

    def __enter__(self) -> 'PicProgrammer':
        self._check_programmer()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        return

    def detect_device(self) -> None:
        log.info('Detecting device')

        success, info = self._execute_command(['-i'])

        if not success:
            log.error('Failed to detect device')
            raise ProgrammerError('Failed to detect device')

        log.info('Device info', info=f'\n{info}')

        if self.DEVICE_ID not in info:
            log.error('No compatible device found', device_id=self.DEVICE_ID)
            raise ProgrammerError('No compatible device found')

        log.info('Device detected successfully', device_id=self.DEVICE_ID)

    def load_firmware(self) -> FirmwareFile:
        if not self._target_firmware:
            self._target_firmware = self._get_firmware()

        return self._target_firmware

    def upgrade_firmware(self) -> None:
        firmware = self.load_firmware()

        log.info('Upgrading firmware', firmware=firmware)

        success, _ = self._execute_command(['-f', firmware.path, f'--{firmware.format}', '--write'])

        if not success:
            log.error('Failed to upgrade firmware', firmware=firmware)
            raise ProgrammerError('Failed to upgrade firmware')

        log.info('Firmware upgraded successfully', firmware=firmware)

    def _get_firmware(self) -> FirmwareFile:
        firmware_file = None

        if self._firmware_file:
            firmware_file = self._get_firmware_file(self._firmware_file)
        elif self._firmware_dir:
            firmware_file = self._find_latest_firmware_file()

        if not firmware_file:
            log.error('Firmware file not found', dir=self._firmware_dir, file=self._firmware_file)
            raise ProgrammerError('Firmware file not found')

        return firmware_file

    def _get_firmware_file(self, firmware_file: str) -> FirmwareFile:
        file_path = self._file_downloader.download(firmware_file)
        file_version = self._get_file_version(file_path)
        file_format = self._get_file_format(file_path)

        return FirmwareFile(file_path, file_format, file_version)

    def _find_latest_firmware_file(self) -> FirmwareFile:
        firmware_files = listdir(self._firmware_dir)

        file_version_map = {file_name: self._get_file_version(file_name) for file_name in firmware_files}

        latest_file = max(file_version_map, key=file_version_map.__getitem__)

        file_path = f'{self._firmware_dir}/{latest_file}'
        file_version = file_version_map[latest_file]
        file_format = self._get_file_format(latest_file)

        return FirmwareFile(file_path, file_format, file_version)

    def _get_file_version(self, file_name: str) -> Version:
        version_pattern = r'\d+\.\d+\.\d+(-\w+)?'
        version = Version('0.0.0')

        if match := re.search(version_pattern, file_name):
            try:
                version = Version(match.group(0))
            except InvalidVersion as error:
                log.warn('Invalid version number', error=error, file_name=file_name)
        else:
            log.warn('Version number not found in file name', file_name=file_name)

        return version

    def _get_file_format(self, file_name: str) -> str:
        file_format = file_name.split('.')[-1]

        if not file_format or file_format not in ['hex', 'elf', 'bin']:
            file_format = 'hex'
            log.warn(f"Invalid file extension, using default '{file_format}' format", file_path=file_name)

        return file_format

    def _get_base_command(self, config: dict[str, Any]) -> list[str]:
        command = ['picprogrammer']

        for key, value in config.items():
            if key.startswith('gpio_'):
                command.extend([f'--{key.replace("_", "-")}', str(value)])

        return command

    def _check_programmer(self) -> None:
        if not (programmer := which(self.PROGRAMMER)):
            log.error('Programmer is not available', programmer=self.PROGRAMMER)
            raise ProgrammerError('Programmer is not available')

        log.info('Programmer is available', programmer=self.PROGRAMMER, path=programmer)

    def _execute_command(self, options: list[str]) -> Tuple[bool, str]:
        command = self._base_command + options

        result = self._platform_access.execute_command(command)

        return result.returncode == 0, result.stdout
