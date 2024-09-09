import unittest
from threading import Thread
from unittest import TestCase
from unittest.mock import MagicMock

from context_logger import setup_logging
from test_utility import wait_for_condition

from mrhat_daemon import ApiServerConfiguration, IMrHatControl, ApiServer
from tests import RESOURCE_ROOT


class ApiServerTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('mrhat-daemon', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_startup_and_shutdown(self):
        # Given
        config, mr_hat_control = create_components()

        with ApiServer(config, mr_hat_control) as api_server:
            # When
            Thread(target=api_server.run).start()

            # Then
            wait_for_condition(1, lambda: api_server.is_running())

        wait_for_condition(1, lambda: not api_server.is_running())

    def test_returns_200_when_get_register_requested(self):
        # Given
        config, mr_hat_control = create_components()
        mr_hat_control.get_register.return_value = 123

        with ApiServer(config, mr_hat_control) as api_server:
            # When
            client = api_server._app.test_client()
            Thread(target=api_server.run).start()

            # When
            response = client.get('/api/register/2')

            # Then
            mr_hat_control.get_register.assert_called_once_with(2)
            self.assertEqual(200, response.status_code)
            self.assertEqual(123, response.json['value'])

    def test_returns_400_when_get_register_requested_with_invalid_parameter(self):
        # Given
        config, mr_hat_control = create_components()

        with ApiServer(config, mr_hat_control) as api_server:
            # When
            client = api_server._app.test_client()
            Thread(target=api_server.run).start()

            # When
            response = client.get('/api/register/10')

            # Then
            self.assertEqual(400, response.status_code)

    def test_returns_500_when_get_register_requested_and_failed(self):
        # Given
        config, mr_hat_control = create_components()
        mr_hat_control.get_register.side_effect = Exception('Failed to read register')

        with ApiServer(config, mr_hat_control) as api_server:
            # When
            client = api_server._app.test_client()
            Thread(target=api_server.run).start()

            # When
            response = client.get('/api/register/2')

            # Then
            self.assertEqual(500, response.status_code)

    def test_returns_202_when_set_register_requested(self):
        # Given
        config, mr_hat_control = create_components()

        with ApiServer(config, mr_hat_control) as api_server:
            # When
            client = api_server._app.test_client()
            Thread(target=api_server.run).start()

            # When
            response = client.post('/api/register/0', json={'value': '123'})

            # Then
            mr_hat_control.set_register.assert_called_once_with(0, 123)
            self.assertEqual(202, response.status_code)

    def test_returns_400_when_set_register_requested_with_invalid_parameter(self):
        # Given
        config, mr_hat_control = create_components()

        with ApiServer(config, mr_hat_control) as api_server:
            # When
            client = api_server._app.test_client()
            Thread(target=api_server.run).start()

            # When
            response = client.post('/api/register/1', json={'value': '256'})

            # Then
            self.assertEqual(400, response.status_code)

    def test_returns_500_when_set_register_requested_and_failed(self):
        # Given
        config, mr_hat_control = create_components()
        mr_hat_control.set_register.side_effect = Exception('Failed to write register')

        with ApiServer(config, mr_hat_control) as api_server:
            # When
            client = api_server._app.test_client()
            Thread(target=api_server.run).start()

            # When
            response = client.post('/api/register/0', json={'value': '123'})

            # Then
            self.assertEqual(500, response.status_code)

    def test_returns_200_when_get_register_flag_requested(self):
        # Given
        config, mr_hat_control = create_components()
        mr_hat_control.get_flag.return_value = 1

        with ApiServer(config, mr_hat_control) as api_server:
            # When
            client = api_server._app.test_client()
            Thread(target=api_server.run).start()

            # When
            response = client.get('/api/register/2/6')

            # Then
            mr_hat_control.get_flag.assert_called_once_with(2, 6)
            self.assertEqual(200, response.status_code)
            self.assertEqual(1, response.json['value'])

    def test_returns_400_when_get_register_flag_requested_with_invalid_parameter(self):
        # Given
        config, mr_hat_control = create_components()

        with ApiServer(config, mr_hat_control) as api_server:
            # When
            client = api_server._app.test_client()
            Thread(target=api_server.run).start()

            # When
            response = client.get('/api/register/2/9')

            # Then
            self.assertEqual(400, response.status_code)

    def test_returns_500_when_get_register_flag_requested_and_failed(self):
        # Given
        config, mr_hat_control = create_components()
        mr_hat_control.get_flag.side_effect = Exception('Failed to read register')

        with ApiServer(config, mr_hat_control) as api_server:
            # When
            client = api_server._app.test_client()
            Thread(target=api_server.run).start()

            # When
            response = client.get('/api/register/2/6')

            # Then
            self.assertEqual(500, response.status_code)

    def test_returns_202_when_set_register_flag_requested(self):
        # Given
        config, mr_hat_control = create_components()

        with ApiServer(config, mr_hat_control) as api_server:
            # When
            client = api_server._app.test_client()
            Thread(target=api_server.run).start()

            # When
            response = client.post('/api/register/1/3', json={'value': '1'})

            # Then
            mr_hat_control.set_flag.assert_called_once_with(1, 3)
            self.assertEqual(202, response.status_code)

    def test_returns_202_when_clear_register_flag_requested(self):
        # Given
        config, mr_hat_control = create_components()

        with ApiServer(config, mr_hat_control) as api_server:
            # When
            client = api_server._app.test_client()
            Thread(target=api_server.run).start()

            # When
            response = client.post('/api/register/1/3', json={'value': '0'})

            # Then
            mr_hat_control.clear_flag.assert_called_once_with(1, 3)
            self.assertEqual(202, response.status_code)

    def test_returns_400_when_set_register_flag_requested_with_invalid_parameter(self):
        # Given
        config, mr_hat_control = create_components()

        with ApiServer(config, mr_hat_control) as api_server:
            # When
            client = api_server._app.test_client()
            Thread(target=api_server.run).start()

            # When
            response = client.post('/api/register/1/5', json={'value': '2'})

            # Then
            self.assertEqual(400, response.status_code)

    def test_returns_500_when_set_register_flag_requested_and_failed(self):
        # Given
        config, mr_hat_control = create_components()
        mr_hat_control.set_flag.side_effect = Exception('Failed to write register')

        with ApiServer(config, mr_hat_control) as api_server:
            # When
            client = api_server._app.test_client()
            Thread(target=api_server.run).start()

            # When
            response = client.post('/api/register/1/5', json={'value': '1'})

            # Then
            self.assertEqual(500, response.status_code)


def create_components():
    config = ApiServerConfiguration(0, RESOURCE_ROOT)
    mr_hat_control = MagicMock(spec=IMrHatControl)
    mr_hat_control.get_readable_registers.return_value = [0, 1, 2, 3]
    mr_hat_control.get_writable_registers.return_value = [0, 1]

    return config, mr_hat_control


if __name__ == '__main__':
    unittest.main()
