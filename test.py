import unittest
import struct
from utilities import parse_rtp_header  # Adjust the import statement as needed

class TestParseRTPHeader(unittest.TestCase):
    def test_parse_rtp_header_correct(self):
        # Correct RTP header data
        data = bytes([
            0x80,  # Version: 2, Padding: 0, Extension: 0, CSRC Count: 0
            0x60,  # Marker: 0, Payload Type: 96
            0x00, 0x01,  # Sequence Number: 1
            0x00, 0x00, 0x00, 0x01,  # Timestamp: 1
            0x00, 0x00, 0x00, 0x02  # SSRC: 2
        ])
        
        expected_result = {
            "version": 2,
            "padding": 0,
            "extension": 0,
            "csrc_count": 0,
            "marker": 0,
            "payload_type": 96,
            "sequence_number": 1,
            "timestamp": 1,
            "ssrc": 2
        }
        
        self.assertEqual(parse_rtp_header(data), expected_result)

    def test_parse_rtp_header_incorrect(self):
        # Incorrect RTP header data (to demonstrate failure)
        data = bytes([
            0x80,  # Version: 2, Padding: 0, Extension: 0, CSRC Count: 0
            0x60,  # Marker: 0, Payload Type: 96
            0x00, 0x02,  # Sequence Number: 2 (Intentionally wrong for this test)
            0x00, 0x00, 0x00, 0x02,  # Timestamp: 2
            0x00, 0x00, 0x00, 0x03  # SSRC: 3
        ])
        
        # The expected result is intentionally set wrong for this test to fail
        incorrect_expected_result = {
            "version": 2,
            "padding": 0,
            "extension": 0,
            "csrc_count": 0,
            "marker": 0,
            "payload_type": 96,
            "sequence_number": 1,  # This is incorrect based on the data
            "timestamp": 1,  # Also incorrect
            "ssrc": 2  # Also incorrect
        }
        
        self.assertNotEqual(parse_rtp_header(data), incorrect_expected_result)
    
if __name__ == "__main__":
    unittest.main()
