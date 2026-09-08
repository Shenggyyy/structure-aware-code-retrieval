from client import calculate_checksum


def test_checksum():
    assert calculate_checksum(b"abc") == 294
