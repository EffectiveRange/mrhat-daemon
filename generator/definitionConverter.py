# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import re

from common_utility import create_file
from context_logger import get_logger

from generator import ICodeFormatter

log = get_logger('DefinitionConverter')


class IDefinitionConverter(object):

    def convert(self, source_content: str) -> str:
        raise NotImplementedError()

    def convert_file(self, source_path: str, output_path: str, format_code: bool = True) -> None:
        raise NotImplementedError()


class DefinitionConverter(IDefinitionConverter):

    def __init__(self, code_formatter: ICodeFormatter):
        self._code_formatter = code_formatter

    def convert(self, source_content: str) -> str:
        define_pattern = re.compile(r'#define\s+(\w+)\s+(.+)')
        output_content = ''

        for source_line in source_content.splitlines():
            if match := define_pattern.match(source_line.strip()):
                name = match.group(1)
                value = match.group(2)

                try:
                    value = int(value, 0)
                except ValueError:
                    pass  # If it can't be converted, keep it as a string

                output_line = f'{name} = {value}'

                log.info('Converted line', source_line=source_line, output_line=output_line)

                output_content += output_line + '\n'

        return output_content

    def convert_file(self, source_path: str, output_path: str, format_code: bool = True) -> None:
        with open(source_path, 'r') as source_file:
            source_content = source_file.read()

        log.info('Converting source file', source=source_path)

        output_content = self.convert(source_content)

        if format_code:
            log.info('Formatting output file', output=output_path)
            output_content = self._code_formatter.format(output_content)

        create_file(output_path, output_content)
