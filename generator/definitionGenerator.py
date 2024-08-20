# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from os.path import abspath
from pathlib import Path

from common_utility import create_file, IFileDownloader
from context_logger import get_logger

from generator import IDefinitionConverter

log = get_logger('DefinitionGenerator')


class IDefinitionGenerator(object):

    def generate(self) -> None:
        raise NotImplementedError()


class DefinitionGenerator(IDefinitionGenerator):

    def __init__(
        self,
        project_root: str,
        configuration: dict[str, str],
        file_downloader: IFileDownloader,
        definition_converter: IDefinitionConverter,
    ) -> None:
        self._project_root = project_root
        self._configuration = configuration
        self._file_downloader = file_downloader
        self._definition_converter = definition_converter

    def generate(self) -> None:
        source_file = self._get_source_file_path()
        output_file = self._get_output_file_path()

        self._create_output_package(output_file)

        log.info('Converting C source/header file to Python file', source=source_file, output=output_file)

        self._definition_converter.convert_file(source_file, output_file)

    def _get_source_file_path(self) -> str:
        source_file = self._configuration['source-file']

        source_file = self._file_downloader.download(source_file, skip_if_exists=False)

        return abspath(source_file)

    def _get_output_file_path(self) -> str:
        output_file = self._configuration['output-file']
        return abspath(f'{self._project_root}/{output_file}')

    def _create_output_package(self, output_file: str) -> None:
        output_path = Path(output_file)
        output_dir = str(output_path.parent)

        log.info('Creating output package', output=output_dir)

        create_file(f'{output_dir}/__init__.py', f'from .{output_path.stem} import *\n')
