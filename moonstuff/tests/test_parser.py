from unittest import mock
from django.test import TestCase
from ..parser import ScanParser
from .parser_strings import with_header, without_header, with_quad_spaces, malformed


class TestScanParser(TestCase):
    def setUp(self):
        self.expected_result = {
            40217116: [
                {'ore_id': 45493, 'quantity': '0.239822223783', 'moon_id': 40217116},
                {'ore_id': 45499, 'quantity': '0.557235956192', 'moon_id': 40217116},
                {'ore_id': 45490, 'quantity': '0.202941834927', 'moon_id': 40217116}
            ]
        }

    def test_with_header(self):
        """
        Test the parser with scan data that contains a header.
        :return:
        """
        result = ScanParser(with_header).parse()
        self.assertEqual(result, self.expected_result)

    def test_without_header(self):
        """
        Test that the ScanParser will handle scan data that does not contain a header.
        :return:
        """
        result = ScanParser(without_header).parse()
        self.assertEqual(result, self.expected_result)

    def test_with_quad_spaces(self):
        """
        Test that the ScanParser will handle data that has 4 spaces rather than tabs.
        :return:
        """
        result = ScanParser(with_quad_spaces).parse()
        self.assertEqual(result, self.expected_result)

    def test_malformed(self):
        """
        Test that the ScanParser will raise an exception when the data is malformed.
        :return:
        """
        parser_obj = ScanParser(malformed)
        self.assertRaises(Exception, parser_obj.parse)

    def test_string_from_tabs(self):
        """
        Test that the __str__ method returns the original scan.
        :return:
        """
        scan_str = ScanParser(with_header).__str__()
        self.assertEqual(scan_str, with_header)

    def test_string_from_quad_spaces(self):
        """
        Test that the __str__ method returns the original scan but converted to tabbed.
        :return:
        """
        scan_str = ScanParser(with_quad_spaces).__str__()
        self.assertEqual(scan_str, with_header)
