from smartcard.scard import *
from smartcard.util import toHexString


def readUID():
    result, context = SCardEstablishContext(SCARD_SCOPE_USER)
    assert result == SCARD_S_SUCCESS
    result, readers = SCardListReaders(context, [])
    assert len(readers) > 0
    reader = readers[0]
    result, card, protocol = SCardConnect(
        context,
        reader,
        SCARD_SHARE_SHARED,
        SCARD_PROTOCOL_T0 | SCARD_PROTOCOL_T1)
    try:
        result, response = SCardTransmit(card, protocol, [0xFF, 0xCA, 0x00, 0x00, 0x04])
        uid = toHexString(response, format=0).replace(" ", "")
        return int(uid, 16)
    except SystemError:
        return None


if __name__ == '__main__':
    while True:
        print(readUID())
