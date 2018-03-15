import pytest

try:
    from ..interface_gr_ieee802_15_4 import GR_IEEE802_15_4
except ImportError as e:
    print("WARN: Unable to load GR_IEEE802_15_4 due to {}.".format(e))
    GR_IEEE802_15_4 = None


class TestGnuRadioIeee802154Interface(object):

    @pytest.fixture
    def interface(self, request):
        # If the interface isn't installed, we skip these tests:
        if GR_IEEE802_15_4 is None:
            pytest.skip()
        # Otherwise set up the interface:
        print("=== Setup GnuRadioIeee802154Interface (for {})".format(request.function.__name__))
        interface = GR_IEEE802_15_4()
        interface.open()
        yield interface
        print("=== Shutdown GnuRadioIeee802154Interface (for {})".format(request.function.__name__))
        interface.close()

    def test_no_rx_support(self, interface):
        assert interface.implements_rx() is False
