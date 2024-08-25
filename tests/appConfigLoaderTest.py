import unittest
from unittest import TestCase

from common_utility import delete_file
from context_logger import setup_logging

from mrhat_daemon import AppConfigLoader
from tests import RESOURCE_ROOT, TEST_RESOURCE_ROOT


class AppConfigLoaderTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('mrhat-daemon', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()
        delete_file(f'{TEST_RESOURCE_ROOT}/config/mrhat-daemon.conf')

    def test_load_config(self):
        # Given
        config_loader = AppConfigLoader(RESOURCE_ROOT)
        arguments = {
            'config_file': f'{RESOURCE_ROOT}/config/mrhat-daemon.conf',
            'interrupt_pin': 17,
        }

        # When
        result = config_loader.load(arguments)

        # Then
        self.assertEqual(17, result['interrupt_pin'])

    def test_load_default_config_when_config_file_not_found(self):
        # Given
        config_loader = AppConfigLoader(RESOURCE_ROOT)
        arguments = {
            'config_file': f'{RESOURCE_ROOT}/tests/config/mrhat-daemon.conf',
            'firmware_dir': 'path/to/firmwares',
        }

        # When
        result = config_loader.load(arguments)

        # Then
        self.assertEqual('path/to/firmwares', result['firmware_dir'])


if __name__ == '__main__':
    unittest.main()
