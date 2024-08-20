# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from context_logger import get_logger

from mrhat_daemon import IApiServer, IMrHatControl

log = get_logger('MrHatDaemon')


class MrHatDaemon(object):

    def __init__(self, mr_hat_control: IMrHatControl, api_server: IApiServer) -> None:
        self._mr_hat_control = mr_hat_control
        self._api_server = api_server

    def run(self) -> None:
        log.info('Initializing components')

        self._mr_hat_control.initialize()

        self._api_server.run()

    def shutdown(self) -> None:
        log.info('Shutting down components')
        self._api_server.shutdown()
