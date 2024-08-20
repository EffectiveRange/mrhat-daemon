# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import black


class ICodeFormatter(object):

    def format(self, source_code: str) -> str:
        raise NotImplementedError()


class CodeFormatter(ICodeFormatter):

    def __init__(self, line_length: int = 120, string_normalization: bool = False):
        self._line_length = line_length
        self._string_normalization = string_normalization

    def format(self, source_code: str) -> str:
        mode = black.Mode(line_length=self._line_length, string_normalization=self._string_normalization)

        return black.format_file_contents(source_code, fast=False, mode=mode)
