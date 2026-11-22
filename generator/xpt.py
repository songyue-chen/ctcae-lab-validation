#!/usr/bin/env python3
"""
xpt.py - writes a SAS transport file (XPORT version 5) with the standard library only.

The version 5 transport format (SAS technical note TS-140) is readable by every SAS release through
LIBNAME XPORT, by R (haven::read_xpt) and by pandas (read_sas). Its limits: variable names of 8
characters, labels of 40, character values of 200 bytes, one dataset label of 40.

    write_xpt(path, variables, rows, dsname='RECORDS', dslabel='', created=datetime(...))

variables: list of dicts {name, label, type ('num' | 'char'), length (chars only), format (optional,
e.g. 'DATE9')}; rows: iterable of lists in variable order; numeric None = missing; a date is passed as a
datetime.date and stored as a SAS date (days since 1960-01-01). The output is byte-identical for the same
input and `created` timestamp.
"""
import datetime as dt
import math
import struct

SAS_EPOCH = dt.date(1960, 1, 1)

def ibm_double(x):
    """IEEE double -> 8-byte IBM hexadecimal float, as SAS stores numerics in a transport file"""
    if x is None: return b'.' + b'\x00' * 7            # SAS missing value
    x = float(x)
    if x == 0: return b'\x00' * 8
    sign = 0x80 if x < 0 else 0
    m, e = math.frexp(abs(x))                            # abs(x) = m * 2**e, 0.5 <= m < 1
    q = -((-e) // 4)                                     # ceil(e / 4): abs(x) = (m / 2**s) * 16**q
    s = 4 * q - e                                        # 0 .. 3, so 1/16 <= fraction < 1
    exponent = q + 64
    if not 0 <= exponent <= 127: raise OverflowError(f'{x} is outside the IBM float range')
    mantissa = int(m * (1 << (56 - s)))                 # exact: 53 significant bits shifted by at most 3
    return bytes([sign | exponent]) + mantissa.to_bytes(7, 'big')

def _rec(text):
    b = text.encode('ascii')
    if len(b) > 80: raise ValueError('header record longer than 80 bytes')
    return b.ljust(80)

def _pad80(b):
    return b + b' ' * (-len(b) % 80)

def _namestr(i, v, pos):
    name = v['name'].upper()
    if len(name) > 8 or len(v['label']) > 40: raise ValueError(f'{name}: name longer than 8 or label longer than 40')
    ntype = 1 if v['type'] == 'num' else 2
    length = 8 if ntype == 1 else int(v['length'])
    if ntype == 2 and not 1 <= length <= 200: raise ValueError(f'{name}: character length {length} outside 1..200')
    fmt = v.get('format', '')
    nform, nfl = (b' ' * 8, 0)
    if fmt:
        m = fmt.rstrip('.')
        digits = ''.join(ch for ch in m if ch.isdigit())
        nform, nfl = m.rstrip('0123456789').encode('ascii').ljust(8), (int(digits) if digits else 0)
    return struct.pack('>hhhh8s40s8shhh2s8shhl52s', ntype, 0, length, i, name.encode('ascii').ljust(8),
                       v['label'].encode('ascii').ljust(40), nform, nfl, 0, 0, b'  ', b' ' * 8, 0, 0, pos, b' ' * 52)

def write_xpt(path, variables, rows, dsname='RECORDS', dslabel='', created=None, sas_version='9.4', os_name='PYTHON'):
    created = created or dt.datetime(2000, 1, 1)
    stamp = created.strftime('%d%b%y:%H:%M:%S').upper()
    if len(dsname) > 8 or len(dslabel) > 40: raise ValueError('dataset name longer than 8 or label longer than 40')
    out = bytearray()
    out += _rec('HEADER RECORD*******LIBRARY HEADER RECORD!!!!!!!000000000000000000000000000000')
    out += _rec('SAS     SAS     SASLIB  ' + sas_version.ljust(8) + os_name.ljust(8) + ' ' * 24 + stamp)
    out += _rec(stamp)
    out += _rec('HEADER RECORD*******MEMBER  HEADER RECORD!!!!!!!000000000000000001600000000140')
    out += _rec('HEADER RECORD*******DSCRPTR HEADER RECORD!!!!!!!000000000000000000000000000000')
    out += _rec('SAS     ' + dsname.upper().ljust(8) + 'SASDATA ' + sas_version.ljust(8) + os_name.ljust(8) + ' ' * 24 + stamp)
    out += _rec(stamp + ' ' * 16 + dslabel.ljust(40) + ' ' * 8)
    out += _rec('HEADER RECORD*******NAMESTR HEADER RECORD!!!!!!!000000%04d00000000000000000000' % len(variables))
    names = bytearray(); pos = 0
    for i, v in enumerate(variables, 1):
        names += _namestr(i, v, pos)
        pos += 8 if v['type'] == 'num' else int(v['length'])
    out += _pad80(bytes(names))
    out += _rec('HEADER RECORD*******OBS     HEADER RECORD!!!!!!!000000000000000000000000000000')
    obs = bytearray()
    for row in rows:
        if len(row) != len(variables): raise ValueError('row length differs from the variable list')
        for v, x in zip(variables, row):
            if v['type'] == 'num':
                if isinstance(x, dt.date): x = (x - SAS_EPOCH).days
                obs += ibm_double(x)
            else:
                b = ('' if x is None else str(x)).encode('ascii')
                if len(b) > int(v['length']): raise ValueError(f'{v["name"]}: value longer than {v["length"]}')
                obs += b.ljust(int(v['length']))
    out += _pad80(bytes(obs))
    with open(path, 'wb') as f: f.write(out)
    return len(out)
