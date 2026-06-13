from .structures import GUID
import ctypes


def uuid_to_guid(u):
    return GUID(
        u.time_low,
        u.time_mid,
        u.time_hi_version,
        (ctypes.c_ubyte * 8)(
            (u.clock_seq_hi_variant << 8 | u.clock_seq_low) >> 8,
            (u.clock_seq_hi_variant << 8 | u.clock_seq_low) & 0xFF,
            *u.node.to_bytes(6, "big"),
        ),
    )
