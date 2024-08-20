import unittest
from unittest import TestCase
from unittest.mock import MagicMock

from common_utility import delete_directory
from context_logger import setup_logging

from generator import DefinitionConverter, ICodeFormatter
from tests import TEST_RESOURCE_ROOT


class DefinitionConverterTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('mrhat-daemon-generator', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()
        delete_directory(f'{TEST_RESOURCE_ROOT}/generated')

    def test_convert(self):
        # Given
        source_content = '''#define REG_STAT_0_ADDR 0xA
#define SHUT_REQ_POS 0
#define SHUT_REQ (1<<SHUT_REQ_POS)
#define SHUT_REQ_MASK (1<<SHUT_REQ_POS) & 0xFF
'''
        code_formatter = MagicMock(spec=ICodeFormatter)
        code_formatter.format.return_value = source_content
        definition_converter = DefinitionConverter(code_formatter)

        # When
        result = definition_converter.convert(source_content)

        # Then
        self.assertEqual(
            '''REG_STAT_0_ADDR = 10
SHUT_REQ_POS = 0
SHUT_REQ = (1<<SHUT_REQ_POS)
SHUT_REQ_MASK = (1<<SHUT_REQ_POS) & 0xFF
''',
            result,
        )

    def test_convert_file(self):
        # Given
        with (
            open(f'{TEST_RESOURCE_ROOT}/source/output', 'r') as output_file,
            open(f'{TEST_RESOURCE_ROOT}/expected/definitions.py', 'r') as formatted_file,
        ):
            output_content = output_file.read()
            formatted_content = formatted_file.read()

        code_formatter = MagicMock(spec=ICodeFormatter)
        code_formatter.format.return_value = formatted_content
        definition_converter = DefinitionConverter(code_formatter)

        # When
        definition_converter.convert_file(
            f'{TEST_RESOURCE_ROOT}/source/source', f'{TEST_RESOURCE_ROOT}/generated/definitions.py'
        )

        # Then
        code_formatter.format.assert_called_once_with(output_content)


if __name__ == '__main__':
    unittest.main()
