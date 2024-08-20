import os.path
import unittest
from unittest import TestCase
from unittest.mock import MagicMock

from common_utility import IFileDownloader, delete_directory
from context_logger import setup_logging

from generator import DefinitionGenerator, IDefinitionConverter
from tests import TEST_RESOURCE_ROOT


class DefinitionGeneratorTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('mrhat-daemon-generator', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()
        delete_directory(f'{TEST_RESOURCE_ROOT}/generated')

    def test_generate_creates_package(self):
        # Given
        source_file = f'{TEST_RESOURCE_ROOT}/config/source-file.h'
        output_file = 'generated/definitions.py'
        configuration = {'source-file': source_file, 'output-file': output_file}
        file_downloader = MagicMock(spec=IFileDownloader)
        file_downloader.download.return_value = source_file
        definition_converter = MagicMock(spec=IDefinitionConverter)
        definition_generator = DefinitionGenerator(
            TEST_RESOURCE_ROOT, configuration, file_downloader, definition_converter
        )

        # When
        definition_generator.generate()

        # Then
        definition_converter.convert_file.assert_called_once_with(source_file, f'{TEST_RESOURCE_ROOT}/{output_file}')
        self.assertTrue(os.path.exists(f'{TEST_RESOURCE_ROOT}/generated/__init__.py'))


if __name__ == '__main__':
    unittest.main()
