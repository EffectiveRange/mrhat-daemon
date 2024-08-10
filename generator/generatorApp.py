#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import sys
from os.path import dirname, abspath
from pathlib import Path

from common_utility import SessionProvider, FileDownloader
from context_logger import setup_logging

from generator import ConfigLoader, DefinitionGenerator, DefinitionConverter, CodeFormatter

sys.path.insert(0, dirname(abspath(__file__)))


class GeneratorApp(object):

    def __init__(self, project_root: str) -> None:
        self._project_root = project_root

    def run(self) -> None:
        config_file = f'{self._project_root}/setup.cfg'
        configuration = ConfigLoader(config_file).load()

        session_provider = SessionProvider()
        download_dir = abspath(f'{self._project_root}/{configuration["download-dir"]}')
        file_downloader = FileDownloader(session_provider, download_dir)

        code_formatter = CodeFormatter()
        definition_converter = DefinitionConverter(code_formatter)

        definition_generator = DefinitionGenerator(
            self._project_root, configuration, file_downloader, definition_converter
        )

        definition_generator.generate()


def main() -> None:
    setup_logging('mrhat-daemon-generator')

    project_root = str(Path(dirname(__file__)).parent.absolute())

    generator_app = GeneratorApp(project_root)

    generator_app.run()


if __name__ == '__main__':
    main()
