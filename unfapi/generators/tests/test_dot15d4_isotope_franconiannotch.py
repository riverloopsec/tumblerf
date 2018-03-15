import pytest

# Import Scapy, after surpressing the annoying IPv6 scapy runtime error
import logging
try:
    logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
    from scapy.all import *
except ImportError:
    print "This tool requires Scapy to be installed, including dot15d4 support."

from ..dot15d4_isotope_franconiannotch import Dot15d4FranconianNotchGenerator


class TestDot15d4FranconianNotchGenerator(object):

    @pytest.fixture
    def dot15d4_generator(self):
        gen = Dot15d4FranconianNotchGenerator()
        gen.set_target(0xFFFF, 0x0000)
        return gen

    def test_included_values(self, dot15d4_generator):
        assert dot15d4_generator.includes_phy == True
        assert dot15d4_generator.includes_mac == True

    def test_set_addrs(self, dot15d4_generator):
        print("Target PAN: 0x{:04x}".format(dot15d4_generator.get_target_pan_id()))
        dot15d4_generator.set_target(0xABCD, 0xBEEF)
        print("Target PAN 2: 0x{:04x}".format(dot15d4_generator.get_target_pan_id()))
        packet_bytes = dot15d4_generator.get_test_case()
        print("Produced test bytes: {}".format(packet_bytes.encode('hex')))
        # Strip off SFD and Length bytes:
        print("Produced inner frame bytes: {}".format(packet_bytes[4+2:].encode('hex')))
        packet_scapy = Dot15d4FCS(packet_bytes[4+2:])
        packet_scapy.show()
        print("Addresses: Dest: 0x{:04x}:0x{:04x}".format(packet_scapy.dest_panid, packet_scapy.dest_addr))
        assert 0xABCD == packet_scapy.dest_panid
        assert 0xBEEF == packet_scapy.dest_addr

    def test_control_case(self, dot15d4_generator):
        count = 0
        for packet_bytes in dot15d4_generator.yield_control_case():
            print("Produced control bytes: {}".format(packet_bytes.encode('hex')))
            count += 1
            assert packet_bytes[:4] == "\x00"*4
            assert packet_bytes[4] == "\xa7"
        assert count == 1

    def test_output_type(self, dot15d4_generator):
        case = dot15d4_generator.get_control_case()
        assert type(case) == str
        case = dot15d4_generator.get_test_case()
        assert type(case) == str

    def test_seq_nums(self, dot15d4_generator):
        dot15d4_generator.set_start_seqnum(0xFF-1)
        cases = dot15d4_generator.get_test_cases(1)
        assert len(cases) == 9  # no nibbles filled, and then 0-8 nibbles filled = 9 total
        assert cases[0] != cases[1]
        # Check the 4 produced have increasing, and wrapped, sequence numbers (byte 8 is the 802.15.4 seq num given leading SFD & len & 4 preamble bytes):
        assert ord(cases[0][8]) == 0xFF-1
        assert ord(cases[1][8]) == 0xFF
        assert ord(cases[2][8]) == 0x00
        assert ord(cases[3][8]) == 0x01

    def test_preamble_length(self, dot15d4_generator):
        cases = dot15d4_generator.get_test_cases(1, {
            'max_fill': 4
        })
        assert len(cases) == 5     # number of cases is max_fill * cases
        assert cases[0] != cases[1]
        #for i, case in enumerate(cases):
        #    print("{}:\t{}".format(i, case.encode('hex')))
        # Using case 3 as a sample to ensure preamble is "00 00 f0 ff"
        assert cases[3][:4] == "\x00\x00\xf0\xff"
        # Using case 4 as a sample to ensure preamble is "00 00 ff ff"
        assert cases[4][:4] == "\x00\x00\xff\xff"
