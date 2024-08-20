# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import os
import shutil
from configparser import ConfigParser
from pathlib import Path
from typing import Any

from context_logger import get_logger

log = get_logger('AppConfigLoader')


class IAppConfigLoader(object):

    def load(self, arguments: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError()


class AppConfigLoader(IAppConfigLoader):

    def __init__(self, resource_root: str):
        self._resource_root = resource_root

    def load(self, arguments: dict[str, Any]) -> dict[str, Any]:
        config_file = Path(arguments['config_file'])

        if not os.path.exists(config_file):
            log.info('Loading default configuration file', config_file=str(config_file))
            default_config = f'{self._resource_root}/config/mrhat-daemon.conf'
            config_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(default_config, config_file)
        else:
            log.info('Using configuration file', config_file=str(config_file))

        parser = ConfigParser()
        parser.read(config_file)

        configuration = {}

        for section in parser.sections():
            configuration.update(dict(parser[section]))

        configuration.update(arguments)

        return configuration
