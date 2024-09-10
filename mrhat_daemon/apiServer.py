# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import json
from dataclasses import dataclass
from typing import Any

from context_logger import get_logger
from flask import Flask, request, Response, jsonify
from waitress.server import create_server

from mrhat_daemon import IMrHatControl

log = get_logger('ApiServer')


@dataclass
class ApiServerConfiguration:
    server_port: int
    resource_root: str


class IApiServer(object):

    def run(self) -> None:
        raise NotImplementedError()

    def shutdown(self) -> None:
        raise NotImplementedError()

    def is_running(self) -> bool:
        raise NotImplementedError()


class ApiServer(IApiServer):

    def __init__(self, configuration: ApiServerConfiguration, mr_hat_control: IMrHatControl) -> None:
        self._configuration = configuration
        self._mr_hat_control = mr_hat_control
        self._port = self._configuration.server_port
        self._app = Flask(__name__)
        self._server = create_server(self._app, listen=f'*:{self._port}')
        self._is_running = False

        self._set_up_register_api()
        self._set_up_register_flag_api()

    def __enter__(self) -> 'ApiServer':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()

    def run(self) -> None:
        log.info('Starting web server', port=self._configuration.server_port)
        try:
            self._is_running = True
            self._server.run()
        except Exception as error:
            self._is_running = False
            log.info('Server exited', reason=error)

    def shutdown(self) -> None:
        log.info('Shutting down')
        try:
            self._server.close()
        except Exception as error:
            log.info('Shutdown', reason=error)
        finally:
            self._is_running = False

    def is_running(self) -> bool:
        return self._is_running

    def _set_up_register_api(self) -> None:

        @self._app.route('/api/register/<address>', methods=['GET', 'POST'])
        def register_api(address: str) -> Response:
            log.info('Register API request', request=request, data=request.data)

            try:
                write = request.method == 'POST'

                register = int(address)
                self._validate_register(register, write)

                if write:
                    data = json.loads(request.data)
                    value = int(data['value'])
                    self._validate_byte(value)

                    self._mr_hat_control.set_register(register, value)
                    return Response(status=202)
                else:
                    value = self._mr_hat_control.get_register(register)
                    return jsonify({'value': value})
            except ValueError as error:
                log.error('Invalid request', request=request, data=request.data, error=error)
                return Response(status=400)
            except Exception as error:
                log.error('Serving the request failed', address=address, error=error)
                return Response(status=500)

    def _set_up_register_flag_api(self) -> None:

        @self._app.route('/api/register/<address>/<position>', methods=['GET'])
        def register_get_flag_api(address: str, position: str) -> Response:
            log.info('Register flag read API request', request=request, data=request.data)

            try:
                register = int(address)
                self._validate_register(register, False)
                flag = int(position)
                self._validate_flag(flag)

                value = self._mr_hat_control.get_flag(register, flag)
                return jsonify({'value': value})
            except ValueError as error:
                log.error('Invalid request', request=request, data=request.data, error=error)
                return Response(status=400)
            except Exception as error:
                log.error('Serving the request failed', address=address, position=position, error=error)
                return Response(status=500)

        @self._app.route('/api/register/<address>/<position>/<value>', methods=['POST'])
        def register_set_flag_api(address: str, position: str, value: str) -> Response:
            log.info('Register flag write API request', request=request, data=request.data)

            try:
                register = int(address)
                self._validate_register(register, True)
                flag = int(position)
                self._validate_flag(flag)
                is_set = int(value)
                self._validate_bit(is_set)

                if is_set:
                    self._mr_hat_control.set_flag(register, flag)
                else:
                    self._mr_hat_control.clear_flag(register, flag)
                return Response(status=202)
            except ValueError as error:
                log.error('Invalid request', request=request, data=request.data, error=error)
                return Response(status=400)
            except Exception as error:
                log.error('Serving the request failed', address=address, position=position, error=error)
                return Response(status=500)

    def _validate_register(self, register: int, read_write: bool) -> None:
        if read_write:
            registers = self._mr_hat_control.get_writable_registers()
        else:
            registers = self._mr_hat_control.get_readable_registers()

        if register not in registers:
            raise ValueError(f'Register number must be in {registers}')

    def _validate_flag(self, position: int) -> None:
        if not (0 <= position <= 7):
            raise ValueError('Flag position must be between 0 and 7')

    def _validate_byte(self, value: int) -> None:
        if not (0 <= value <= 255):
            raise ValueError('Byte value must be between 0 and 255')

    def _validate_bit(self, value: int) -> None:
        if not (0 <= value <= 1):
            raise ValueError('Flag value must be between 0 and 1')
