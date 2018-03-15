from .base import BaseTestCaseGenerator
from scapy.layers.dot15d4 import Dot15d4FCS, Dot15d4Data
from scapy.packet import fuzz, Packet, bind_layers
from scapy.fields import StrFixedLenField
import random

MAX_DOT15D4_LENGTH=120


class LengthRaw(Packet):
    name = "LengthRaw"
    #TODO: Determine why max_length being passed in is not coming through in this init:
    def __init__(self, max_length=MAX_DOT15D4_LENGTH-11):
        #TODO: Check max value being used
        self.max_frame_len = max_length
        self.fields_desc = [
             StrFixedLenField("load", "", length_from=self.get_load_length)
        ]
        Packet.__init__(self)

    def get_load_length(self, pkt):
        rand_len = random.randint(0, self.max_frame_len)
        #print("Choosing length between 0 and {}: {}".format(self.max_frame_len, rand_len))
        return rand_len


bind_layers(Dot15d4Data, LengthRaw)


class Dot15d4RandomPayloadGenerator(BaseTestCaseGenerator):
    def __init__(self):
        #super(BaseTestCaseGenerator)
        #super().__init__(includes_phy=False, includes_mac=True)
        BaseTestCaseGenerator.__init__(self, includes_phy=False, includes_mac=True)
        self.__target_pan_id = None
        self.__target_short_addr = None
        self.__src_short_addr = None
        self.__start_seqnum = 0

    def set_target(self, pan_id, short_addr):
        self.__target_pan_id = pan_id
        self.__target_short_addr = short_addr

    def set_source(self, short_addr):
        #TODO: Add long addresses
        self.__src_short_addr = short_addr

    def set_start_seqnum(self, value):
        if value >= 0 and value <= 0xff:
            self.__start_seqnum = value
        else:
            raise ValueError("Sequence number must be between 0x00 and 0xFF.")

    #TODO: Add set of values from a sample Scapy packet

    #def load_samples_from_pcap(self, pcap_filename):
    #    self.add_sample()

    def yield_control_case(self, count=1):
        pkt = Dot15d4FCS(fcf_srcaddrmode=2, fcf_ackreq=True, fcf_destaddrmode=2, fcf_panidcompress=True) / \
              Dot15d4Data(dest_panid=self.__target_pan_id, dest_addr=self.__target_short_addr, src_addr=self.__src_short_addr)
        for i in range(count):
            pkt.seqnum = self.__start_seqnum
            result = str(pkt)
            self.__start_seqnum = (self.__start_seqnum + 1) % (0xFF + 1)
            yield result

    def yield_test_case(self, count, constraints=None):
        """
        Is a Python generator which yields potential test cases to use.
        :param constraints: Dictionary of constraints to apply. Optionally takes an entry "check_valid"=False to disable checking to see if the produced frame makes sense to Scapy.
        :yield: A byte array generated as a possible test case.
        """
        check_valid = constraints.get('check_valid', True) if constraints is not None else True
        #print("*** Validity check status {}".format(check_valid))
        for i in range(count):
            pkt = Dot15d4FCS(seqnum=self.__start_seqnum, fcf_srcaddrmode=2, fcf_ackreq=True, fcf_destaddrmode=2, fcf_panidcompress=True) / \
                  Dot15d4Data(dest_panid=self.__target_pan_id, dest_addr=self.__target_short_addr, src_addr=self.__src_short_addr)
            base_pkt_length = len(pkt)
            pkt = pkt / fuzz(LengthRaw(max_length=MAX_DOT15D4_LENGTH-base_pkt_length))
            self.__start_seqnum = (self.__start_seqnum + 1) % (0xFF + 1)
            #pkt.show2()
            if not check_valid:
                yield str(pkt)
            else:
                # Due to use of fuzz(), each call to str(pkt) produces different values, and some of these aren't
                # seen as valid by Scapy. Thus we optionally retry till we get a "good" one.
                pb = str(pkt)
                is_valid = Dot15d4FCS(pb).haslayer(Dot15d4Data)
                while not is_valid:
                    print("Trying again as initial packet didn't pass validity check.")
                    #print("Initial pkt that failed - formed:", pkt.summary())
                    #print("Initial pkt that failed - parsed:", Dot15d4FCS(pb).summary())
                    pb = str(pkt)
                    is_valid = Dot15d4FCS(pb).haslayer(Dot15d4Data)
                    #print("New pkt - parsed:", Dot15d4FCS(pb).summary())
                yield pb
