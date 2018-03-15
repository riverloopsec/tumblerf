import pytest

# Import Scapy, after surpressing the annoying IPv6 scapy runtime error
import logging
try:
    logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
    from scapy.all import *
except ImportError:
    print "This tool requires Scapy to be installed, including dot15d4 support."

from ..dot15d4_isotope_preamblelength import Dot15d4PreambleLengthGenerator


class TestDot15d4IsotopePreambleLengthGenerator(object):

    @pytest.fixture
    def dot15d4_generator(self):
        gen = Dot15d4PreambleLengthGenerator()
        return gen

    def test_included_values(self, dot15d4_generator):
        assert dot15d4_generator.includes_phy == True
        assert dot15d4_generator.includes_mac == True

    def test_set_addrs(self, dot15d4_generator):
        dot15d4_generator.set_target(0xABCD, 0xBEEF)
        packet_bytes = dot15d4_generator.get_test_case({
            'preamb_len': 10
        })
        print("Produced test bytes: {}".format(packet_bytes.encode('hex')))
        # Strip off SFD and Length bytes:
        print("Produced inner frame bytes: {}".format(packet_bytes[2:].encode('hex')))
        packet_scapy = Dot15d4FCS(packet_bytes[2:])
        packet_scapy.show()
        #print("Addresses: Dest: 0x{:04x}:0x{:04x} ; Src: 0x{:04x}".format(packet_scapy.dest_panid, packet_scapy.dest_addr, packet_scapy.src_addr))
        assert 0xABCD == packet_scapy.dest_panid
        assert 0xBEEF == packet_scapy.dest_addr

    def test_output_type(self, dot15d4_generator):
        case = dot15d4_generator.get_control_case()
        assert type(case) == str
        case = dot15d4_generator.get_test_case({
            'preamb_len': 1
        })
        assert type(case) == str

    def test_default_constraints(self, dot15d4_generator):
        dot15d4_generator.set_default_constraints({
            'preamb_len': 1
        })
        case = dot15d4_generator.get_test_case()
        assert type(case) == str

    def test_control_case(self, dot15d4_generator):
        dot15d4_generator.set_target(0xFFFF, 0x0000)
        count = 0
        for packet_bytes in dot15d4_generator.yield_control_case():
            print("Produced control bytes: {}".format(packet_bytes.encode('hex')))
            count += 1
            assert packet_bytes[:4] == "\x00"*4
        assert count == 1

    def test_seq_nums(self, dot15d4_generator):
        dot15d4_generator.set_start_seqnum(0xFF-1)
        cases = dot15d4_generator.get_test_cases(4, {
            'preamb_len': 1
        })
        assert len(cases) == 4
        assert cases[0] != cases[1]
        # Check the 4 produced have increasing, and wrapped, sequence numbers (byte 4 is the 802.15.4 seq num given leading SFD & len):
        assert ord(cases[0][4]) == 0xFF-1
        assert ord(cases[1][4]) == 0xFF
        assert ord(cases[2][4]) == 0x00
        assert ord(cases[3][4]) == 0x01

    def test_preamble_length(self, dot15d4_generator):
        dot15d4_generator.set_target(0xFFFF, 0x0000)
        cases = dot15d4_generator.get_test_cases(1, {
            'preamb_len': 10
        })
        assert len(cases) == 10     # number of cases is preamb_len * cases
        assert cases[0] != cases[1]
        #TODO: Ensure that the nibble inserts are working as intended.
        #for i, case in enumerate(cases):
        #    print("{}:\t{}".format(i, case.encode('hex')))
        # Using case 8 as a sample to ensure 8 nibbles of leading 0s were inserted:
        assert len(cases[0]) == len(cases[8][4:])
        assert cases[8][:4] == "\x00"*4
