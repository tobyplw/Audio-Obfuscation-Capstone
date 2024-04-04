import unittest
from utilities import parse_rtp_header

class TestParseRtpHeader(unittest.TestCase):
    def test_parse_rtp_header(self):
        data = b'\x80\xc1\x12\x34\x56\x78\x9a\xbc\xde\xf0\x00\x00'
        expected_result = {
            "version": 2,
            "padding": 0,
            "extension": 0,
            "csrc_count": 0,
            "marker": 1,
            "payload_type": 65,
            "sequence_number": 4660,
            "timestamp": 1450744508,
            "ssrc": 3740270592
        }
        result = parse_rtp_header(data)
        self.assertEqual(result, expected_result)

    def test_parse_rtp_header2(self):
        data = b'\x80\xc1\x12\x56\x56\x78\x9a\xbc\xde\xf0\x00\x00'
        expected_result = {
            "version": 2,
            "padding": 0,
            "extension": 0,
            "csrc_count": 0,
            "marker": 1,
            "payload_type": 65,
            "sequence_number": 4660,
            "timestamp": 1450744508,
            "ssrc": 3740270592
        }


        result = parse_rtp_header(data)
        self.assertNotEqual(result, expected_result)

if __name__ == '__main__':
    unittest.main()
