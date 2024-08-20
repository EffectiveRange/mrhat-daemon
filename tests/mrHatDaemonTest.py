import unittest
from unittest import TestCase
from unittest.mock import MagicMock

from context_logger import setup_logging

from mrhat_daemon import MrHatDaemon, IMrHatControl, IApiServer


class MrHatDaemonTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('mrhat-daemon', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_run(self):
        # Given
        mr_hat_control, api_server = create_components()
        mr_hat_daemon = MrHatDaemon(mr_hat_control, api_server)

        # When
        mr_hat_daemon.run()

        # Then
        mr_hat_control.initialize.assert_called_once()
        api_server.run.assert_called_once()

    def test_shutdown(self):
        # Given
        mr_hat_control, api_server = create_components()
        mr_hat_daemon = MrHatDaemon(mr_hat_control, api_server)
        mr_hat_daemon.run()

        # When
        mr_hat_daemon.shutdown()

        # Then
        api_server.shutdown.assert_called_once()


def create_components():
    mr_hat_control = MagicMock(spec=IMrHatControl)
    api_server = MagicMock(spec=IApiServer)

    return mr_hat_control, api_server


if __name__ == '__main__':
    unittest.main()
