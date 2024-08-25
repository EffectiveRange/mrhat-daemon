import unittest
from unittest import TestCase

from context_logger import setup_logging

from generator import BuildConfigLoader
from tests import TEST_RESOURCE_ROOT


class BuildConfigLoaderTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('mrhat-daemon-generator', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_load_config_when_config_file_is_valid(self):
        # Given
        config_loader = BuildConfigLoader(f'{TEST_RESOURCE_ROOT}/config/setup-valid.cfg')

        # When
        result = config_loader.load()

        # Then
        self.assertTrue(result['source-file'].startswith('https://raw.githubusercontent.com/EffectiveRange/fw-mrhat/'))
        self.assertEqual('generated/definitions.py', result['output-file'])
        self.assertEqual('generated', result['download-dir'])

    def test_load_raises_error_when_config_file_is_invalid(self):
        # Given
        config_loader = BuildConfigLoader(f'{TEST_RESOURCE_ROOT}/config/setup-invalid.cfg')

        # When, Then
        self.assertRaises(AttributeError, config_loader.load)

    def test_load_raises_error_when_config_file_not_exists(self):
        # Given
        config_loader = BuildConfigLoader(f'{TEST_RESOURCE_ROOT}/config/setup-not-exists.cfg')

        # When, Then
        self.assertRaises(FileNotFoundError, config_loader.load)


if __name__ == '__main__':
    unittest.main()
