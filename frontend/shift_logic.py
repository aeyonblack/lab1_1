"""
shift_logic.py
Circular bit shift reference implementation.
Mirrors the FPGA hardware logic for validation.
"""


def circular_shift(byte_val: int, sw0: int, sw1: int) -> int:
    """
    Perform a circular bit shift on an 8-bit value.

    Args:
        byte_val: Input byte (0-255)
        sw0: Value of switch 0 (0 or 1)
        sw1: Value of switch 1 (0 or 1)

    Returns:
        Shifted byte (0-255)

    Shift table (from practical guide):
        SW1=0, SW0=0 → rotate left  by 1
        SW1=0, SW0=1 → rotate right by 1
        SW1=1, SW0=0 → rotate left  by 2
        SW1=1, SW0=1 → rotate right by 2
    """
    if sw1 == 0 and sw0 == 0:
        return _rotate_left(byte_val, 1)
    elif sw1 == 0 and sw0 == 1:
        return _rotate_right(byte_val, 1)
    elif sw1 == 1 and sw0 == 0:
        return _rotate_left(byte_val, 2)
    else:  # sw1 == 1, sw0 == 1
        return _rotate_right(byte_val, 2)


def _rotate_left(val: int, n: int) -> int:
    """Circular left shift of an 8-bit value by n positions."""
    # Shift left, then OR in the bits that overflowed past bit 7
    return ((val << n) | (val >> (8 - n))) & 0xFF


def _rotate_right(val: int, n: int) -> int:
    """Circular right shift of an 8-bit value by n positions."""
    return ((val >> n) | (val << (8 - n))) & 0xFF