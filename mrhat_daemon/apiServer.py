# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from threading import Thread
from typing import Any

from context_logger import get_logger
from flask import Flask
from waitress.server import create_server

log = get_logger('ApiServer')


class IApiServer(object):

    def run(self) -> None:
        raise NotImplementedError()

    def shutdown(self) -> None:
        raise NotImplementedError()

    def is_running(self) -> bool:
        raise NotImplementedError()


class ApiServer(IApiServer):

    def __init__(self, port: int) -> None:
        self._port = port
        self._app = Flask(__name__)
        self._server = create_server(self._app, listen=f'*:{self._port}')
        self._thread = Thread(target=self._start_server)
        self._is_running = False

        self._set_up_endpoints()

    def __enter__(self) -> 'ApiServer':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()

    def run(self) -> None:
        log.info('Starting server', port=self._port)
        self._thread.run()

    def shutdown(self) -> None:
        if self._is_running:
            log.info('Shutting down')
            self._server.close()
            self._thread.join()
            self._is_running = False

    def is_running(self) -> bool:
        return self._is_running

    def _start_server(self) -> None:
        try:
            self._is_running = True
            self._server.run()
        except Exception as error:
            self._is_running = False
            log.info('Shutdown', reason=error)

    def _set_up_endpoints(self) -> None:
        # TODO: Implement
        pass
