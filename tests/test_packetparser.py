import pytest

from velbustcp.lib.packet.packetparser import PacketParser
from velbustcp.lib.consts import ETX, STX

checksum_data = [
    (bytearray([0x0F, 0xFB, 0x1F, 0x08, 0xFB, 0x08, 0x03, 0x08, 0x80, 0x00, 0x00, 0x00]), 0x41),
    (bytearray([0x0F, 0xFB, 0x3D, 0x05, 0xB7, 0x06, 0x0A, 0x07, 0xE5]), 0x01),
    (bytearray([0x0F, 0xFB, 0x3B, 0x08, 0xB8, 0x01, 0x00, 0x45, 0x80, 0x00, 0x00, 0x00]), 0x35)
]

@pytest.mark.parametrize("data, expected_result", checksum_data)
def test_checksum(data, expected_result):
    assert PacketParser.checksum(data) == expected_result


acceptance_data = [STX, 0xFB, 0x1C, 0x08, 0xFB, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xCF, ETX]
acceptance_packet = bytearray(acceptance_data)
next_test_data = [
    (bytearray([]), None),                                                              # No data/header incomplete
    (bytearray([STX, 0xFB, 0x01, 0x04, 0x00]), None),                                   # Header ok (4bytes), but not a valid packet length (min_packet_length=6bytes)
    (bytearray([STX, 0xFB, 0x01, 0x04, 0x00, 0xF1, ETX]), None),                        # Header ok (4bytes), but packet too short for specified data length (4bytes)
    (acceptance_packet, acceptance_packet),                                             # OK
    (bytearray([STX, 0x13, 0x00, 0xEF, 0x00] + acceptance_data), acceptance_packet),    # Realign due to invalid start, still returns packet
    (bytearray([STX, 0x13, 0x00, 0xEF, 0x00, STX, 0x13, 0x00, 0xEF, 0x00]), None)       # Realign due to invalid start, and returns None
]

@pytest.mark.parametrize("data, expected_result", next_test_data)
def test_next(data, expected_result):
    parser = PacketParser()
    parser.feed(data)
    assert expected_result == parser.next()