import pytest

from ..interface_killerbee import KillerBeeInterface

class TestKillerBeeInterface(object):

    @pytest.fixture
    def interface(self, request):
        print("=== Setup KillerBeeInterface (for {})".format(request.function.__name__))
        interface = KillerBeeInterface()
        interface.open()
        yield interface
        print("=== Shutdown KillerBeeInterface (for {})".format(request.function.__name__))
        interface.close()

    def test_no_rx_support(self, interface):
        assert interface.implements_rx() is True
