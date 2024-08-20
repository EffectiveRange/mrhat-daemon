# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from configparser import ConfigParser
from os.path import exists

from context_logger import get_logger

log = get_logger('BuildConfigLoader')


class IBuildConfigLoader(object):

    def load(self) -> dict[str, str]:
        raise NotImplementedError()


class BuildConfigLoader(IBuildConfigLoader):

    def __init__(self, config_file: str):
        self._config_file = config_file

    def load(self) -> dict[str, str]:
        if not exists(self._config_file):
            log.error('Configuration file not found', file=self._config_file)
            raise FileNotFoundError('Configuration file not found')

        parser = ConfigParser()
        parser.read(self._config_file)

        if not parser.has_section('generate-definitions'):
            log.error('Configuration file is missing [generate-definitions] section', file=self._config_file)
            raise AttributeError('Configuration file is missing [generate-definitions] section')

        return dict(parser['generate-definitions'])
