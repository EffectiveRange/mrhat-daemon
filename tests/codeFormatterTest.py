import unittest
from unittest import TestCase

from context_logger import setup_logging

from generator import CodeFormatter


class CodeFormatterTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('mrhat-daemon-generator', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_format(self):
        # Given
        code_formatter = CodeFormatter()
        source_code = '''REG_STAT_0_ADDR = 10
SHUT_REQ_POS = 0
SHUT_REQ = (1<<SHUT_REQ_POS)
SHUT_REQ_MASK = (1<<SHUT_REQ_POS) & 0xFF
'''

        # When
        result = code_formatter.format(source_code)

        # Then
        self.assertEqual(
            '''REG_STAT_0_ADDR = 10
SHUT_REQ_POS = 0
SHUT_REQ = 1 << SHUT_REQ_POS
SHUT_REQ_MASK = (1 << SHUT_REQ_POS) & 0xFF
''',
            result,
        )


if __name__ == '__main__':
    unittest.main()
