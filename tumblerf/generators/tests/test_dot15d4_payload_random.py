import pytest
#from scapy.layers.dot15d4 import *
#from scapy.fields import *
from scapy.all import *
#from scapy.layers.dot15d4 import Dot15d4FCS, Dot15d4, Dot15d4Data

from ..dot15d4_payload_random import Dot15d4RandomPayloadGenerator, LengthRaw

class TestDot15d4RandomPayloadGenerator(object):
    def setup_method(self, method):
        """Setup any state tied to the execution of the given method in a class. Invoked for every test method."""
        pass

    @pytest.fixture
    def dot15d4_generator(self):
        gen = Dot15d4RandomPayloadGenerator()
        gen.set_target(0xABCD, 0xBEEF)
        gen.set_source(0xDEAD)
        return gen

    def test_included_values(self, dot15d4_generator):
        assert dot15d4_generator.includes_phy == False
        assert dot15d4_generator.includes_mac == True

    def test_set_addrs(self, dot15d4_generator):
        packet_bytes = dot15d4_generator.get_test_case()
        print("Produced test bytes: {}".format(packet_bytes.encode('hex')))
        packet_scapy = Dot15d4FCS(packet_bytes)
        packet_scapy.show()
        #print("Addresses: Dest: 0x{:04x}:0x{:04x} ; Src: 0x{:04x}".format(packet_scapy.dest_panid, packet_scapy.dest_addr, packet_scapy.src_addr))
        assert 0xABCD == packet_scapy.dest_panid
        assert 0xBEEF == packet_scapy.dest_addr
        assert 0xDEAD == packet_scapy.src_addr

    def test_output_type(self, dot15d4_generator):
        case = dot15d4_generator.get_control_case()
        assert type(case) == str
        case = dot15d4_generator.get_test_case()
        assert type(case) == str

    def test_unique_cases(self, dot15d4_generator):
        cases = dot15d4_generator.get_test_cases(2)
        assert len(cases) == 2
        assert cases[0] != cases[1]

    def test_seq_nums(self, dot15d4_generator):
        dot15d4_generator.set_start_seqnum(0xFF - 1)
        cases = dot15d4_generator.get_test_cases(4)
        assert len(cases) == 4
        for i, case in enumerate(cases):
            print("{}:\t{}".format(i, case.encode('hex')))
        # Check the 4 produced have increasing, and wrapped, sequence numbers (byte 2 is the 802.15.4 seq num):
        assert ord(cases[0][2]) == 0xFF - 1
        assert ord(cases[1][2]) == 0xFF
        assert ord(cases[2][2]) == 0x00
        assert ord(cases[3][2]) == 0x01
