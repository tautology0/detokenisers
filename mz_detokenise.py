#!/usr/bin/env python3
"""
mz_detokenise.py - Detokenise Sharp MZ BASIC .MZF program files.

A Python port and merge of three separate C detokenisers:
    mzdetokenise.c     - Sharp MZ-700
    mz80kdetokenise.c  - Sharp MZ-80K
    mz80adetokenise.c  - Sharp MZ-80A

Select the source machine with --machine {mz700,mz80k,mz80a}.

NOTE ON A SOURCE QUIRK (fixed here, not reproduced)
----------------------------------------------------
The original mz80adetokenise.c and mz80kdetokenise.c had a missing comma
between the "SIN(" and "COS(" entries in the `tokens2[]` initialiser,
which in C silently concatenates adjacent string literals into one
constant ("SIN(COS(") and shifts every following entry down by one
index. That was a genuine bug in the original source, not an
intentional format quirk, so this port corrects it: SIN( and COS( are
separate, correctly-indexed entries below.
"""

import argparse
import sys


# ---------------------------------------------------------------------------
# Shared "sharp ASCII" lower-case table (identical across all three originals)
# ---------------------------------------------------------------------------

def build_sharp_ascii():
    table = [' '] * 256
    mapping = {
        146: 'e', 150: 't', 151: 'g', 152: 'h', 154: 'b',
        155: 'x', 156: 'd', 157: 'r', 158: 'p', 159: 'c',
        160: 'q', 161: 'a', 162: 'z', 163: 'w', 164: 's',
        165: 'u', 166: 'i', 169: 'k', 170: 'f', 171: 'v',
        175: 'j', 176: 'n', 179: 'm', 183: 'o', 184: 'l',
        189: 'y',
    }
    for code, ch in mapping.items():
        table[code] = ch
    return table


SHARP_ASCII = build_sharp_ascii()


def pad(entries, size=128):
    """Pad a token list out to `size` entries with empty strings, matching
    the zero-fill behaviour of a partially-initialised C array."""
    out = list(entries) + [''] * (size - len(entries))
    return out[:size]


# ---------------------------------------------------------------------------
# MZ-80A token tables (from mz80adetokenise.c)
# ---------------------------------------------------------------------------

TOKENS1_MZ80A = pad([
    "REM", "DATA", "", "", "READ", "LIST", "RUN", "NEW", "PRINT", "LET", "FOR",       # 8A
    "IF", "THEN", "GOTO", "GOSUB", "RETURN", "NEXT", "STOP", "END", "", "ON", "LOAD",  # 95
    "SAVE", "VERIFY", "POKE", "DIM", "DEF FN", "INPUT", "RESTORE", "CLR", "MUSIC", "TEMPO", "USR(",  # A0
    "WOPEN", "ROPEN", "CLOSE", "MON", "LIMIT", "CONT", "GET", "INP#", "OUT#", "CURSOR", "SET",       # AB
    "RESET", "", "", "", "", "", "", "AUTO", "", "", "COPY/P",  # B6
    "PAGE/P",
])

TOKENS2_MZ80A = pad([
    "", "", "", "><", "<>", "=<", "<=", "=>", ">=", "", ">",          # 8A
    "<", "", "", "", "", "", "", "", "", "", "",                     # 95
    "", "", "", "", "", "", "", "", "TO", "STEP", "LEFT$(",          # A0
    "RIGHT$(", "MID$(", "LEN(", "CHR$(", "STR$(", "ASC(", "VAL(", "PEEK(", "TAB(", "SPACE$(", "SIZE",  # AB
    "", "", "", "STRING$(", "", "CHARACTER$(", "CRS", "CRS", "", "", "",  # B6
    "", "", "", "", "", "", "", "", "", "RND(", "SIN(",              # C1
    "COS(", "TAN(", "ATN(", "EXP(", "INT(", "LOG(", "LN(", "ABS(", "SGN(", "SQR(",
])


def decode_token_mz80a(work, get8):
    if work == 0x80:
        w2 = get8()
        idx = w2 - 0x80
        text = TOKENS1_MZ80A[idx] if 0 <= idx < len(TOKENS1_MZ80A) else ''
        is_rem = (w2 == 0x80)
        return text, is_rem
    else:
        idx = work - 0x80
        text = TOKENS2_MZ80A[idx] if 0 <= idx < len(TOKENS2_MZ80A) else ''
        return text, False


# ---------------------------------------------------------------------------
# MZ-80K token table (from mz80kdetokenise.c)
#
# NOTE: the original mz80kdetokenise.c also declares a tokens2[] array
# (identical text to MZ-80A's, including the same missing-comma bug), but
# never actually reads from it anywhere in main() - only tokens1[] is used.
# It is therefore dead code and has been omitted here.
# ---------------------------------------------------------------------------

TOKENS1_MZ80K = pad([
    "REM", "DATA", "LIST", "RUN", "NEW", "PRINT", "LET", "FOR", "IF", "GOTO", "READ",         # 8A
    "GOSUB", "RETURN", "NEXT", "STOP", "END", "ON", "LOAD", "SAVE", "VERIFY", "POKE", "DIM",  # 95
    "DEF FN", "INPUT", "RESTORE", "CLR", "MUSIC", "TEMPO", "USR(", "WOPEN", "ROPEN", "CLOSE", "BYE",  # A0
    "LIMIT", "CONT", "SET", "RESET", "GET", "INP#", "OUT#", "", "", "", "",                   # AB
    "", "THEN", "TO", "STEP", "><", "<>", "=<", "<=", "=>", ">=", "=",                         # B6
    ">", "<", "AND", "OR", "NOT", "+", "-", "*", "/", "LEFT$(", "RIGHT$(",                     # C1
    "MID$(", "LEN(", "CHR$(", "STR$(", "ASC(", "VAL(", "PEEK(", "TAB(", "SP(", "SIZE", "",     # CC
    "", "", "^", "RND(", "SIN(", "COS(", "TAN(", "ATN(", "EXP(", "INT(", "LOG(",               # D7
    "LN(", "ABS(", "SGN(", "SQR(",
])


def decode_token_mz80k(work, get8):
    idx = work - 0x80
    text = TOKENS1_MZ80K[idx] if 0 <= idx < len(TOKENS1_MZ80K) else ''
    is_rem = work in (0x80, 0x81)
    return text, is_rem


# ---------------------------------------------------------------------------
# MZ-700 token tables (from mzdetokenise.c)
# ---------------------------------------------------------------------------

TOKENS_MZ700 = pad([
    "GOTO", "GOSUB", "", "RUN", "RETURN", "RESTORE", "RESUME", "LIST", "", "DELETE", "RENUMBER", "AUTO", "", "FOR", "NEXT", "PRINT",
    "", "INPUT", "", "IF", "DATA", "READ", "DIM", "REM", "END", "STOP", "CONT", "CLS", "", "ON", "LET", "NEW",
    "POKE", "OFF", "MODE", "SKIP", "PLOT", "LINE", "RLINE", "MOVE", "RMOVE", "TRON", "TROFF", "INP#", "", "GET", "PCOLOR", "PHOME",
    "HSET", "GPRINT", "KEY", "AXIS", "LOAD", "SAVE", "MERGE", "", "CONSOLE", "", "OUT", "CIRCLE", "TEST", "PAGE", "", "",
    "ERASE", "ERROR", "", "USR", "BYE", "", "", "DEF", "", "", "", "", "", "", "WOPEN", "CLOSE",
    "ROPEN", "", "", "", "", "", "", "", "", "KILL", "", "", "", "", "", "",
    "TO", "STEP", "THEN", "USING", "", "", "TAB", "SPC", "", "", "", "OR", "AND", "", "><", "<>",
    "=<", "<=", "=>", ">=", "=", ">", "<", "+", "-", "", "", "/", "*", "^", "ext1", "ext2",
])

ETOKENS1_MZ700 = pad([
    "", "SET", "RESET", "COLOR", "", "", "", "", "", "", "", "", "", "", "", "",
    "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
    "", "", "MUSIC", "TEMPO", "CURSOR", "VERIFY", "CLR", "LIMIT", "", "", "", "", "", "", "BOOT", "",
])

ETOKENS2_MZ700 = pad([
    "INT", "ABS", "SIN", "COS", "TAN", "LN", "EXP", "SQR", "RND", "PEEK", "ATN", "SGN", "LOG", "PAI", "", "RAD",
    "", "", "", "", "", "EOF", "", "", "", "", "", "", "", "", "JOY", "",
    "", "STR$", "HEX$", "", "", "", "", "", "", "", "", "ASC", "LEN", "VAL", "", "",
    "", "", "", "ERN", "ERL", "SIZE", "", "", "", "", "LEFT$", "RIGHT$", "MID$", "", "", "",
    "", "", "", "", "TI$", "", "", "FN",
])


def decode_token_mz700(work, get8):
    if work == 0xFE:
        w2 = get8()
        idx = w2 - 0x80
        text = ETOKENS1_MZ700[idx] if 0 <= idx < len(ETOKENS1_MZ700) else ''
        return text, False
    elif work == 0xFF:
        w2 = get8()
        idx = w2 - 0x80
        text = ETOKENS2_MZ700[idx] if 0 <= idx < len(ETOKENS2_MZ700) else ''
        return text, False
    else:
        idx = work - 0x80
        text = TOKENS_MZ700[idx] if 0 <= idx < len(TOKENS_MZ700) else ''
        is_rem = work in (0x97, 0x94)  # REM, DATA
        return text, is_rem


# ---------------------------------------------------------------------------
# Machine definitions
# ---------------------------------------------------------------------------

class Machine:
    def __init__(self, name, header_bytes, eol_byte, decode_token):
        self.name = name
        # header_bytes: set of acceptable first-byte values, or None if the
        # original tool performed no such check (MZ-700).
        self.header_bytes = header_bytes
        self.eol_byte = eol_byte
        self.decode_token = decode_token


MACHINES = {
    'mz80a': Machine('MZ-80A', {0x05, 0x02}, 0x0D, decode_token_mz80a),
    'mz80k': Machine('MZ-80K', {0x05, 0x02}, 0x0D, decode_token_mz80k),
    'mz700': Machine('MZ-700', None, 0x00, decode_token_mz700),
}


# ---------------------------------------------------------------------------
# Byte-level input stream (mirrors the C get8bit()/get16bit() helpers)
# ---------------------------------------------------------------------------

class ByteStream:
    """Mimics C's fgetc()-based get8bit()/get16bit() helpers, including
    their EOF quirks, closely enough for well-formed .MZF files."""

    def __init__(self, f):
        self.f = f
        self.eof = False

    def _fgetc(self):
        b = self.f.read(1)
        if not b:
            self.eof = True
            return -1
        return b[0]

    def get8(self):
        # unsigned char get8bit(): -1 truncates to 0xFF
        return self._fgetc() & 0xFF

    def get16(self):
        # int get16bit(): low/high kept as plain (possibly -1) ints
        low = self._fgetc()
        high = self._fgetc()
        return (high << 8) + low


# ---------------------------------------------------------------------------
# Shared MZF floating point decoding (identical across all three originals)
# ---------------------------------------------------------------------------

def decode_float(get8):
    exponent = get8()
    if exponent & 0x80:
        exponent -= 0x80
    elif exponent != 0:
        exponent = 0x80 - exponent

    fp = 2.0 ** exponent
    count = 1
    mantissa = 0.0
    for _ in range(4):
        morework = get8()
        for j in range(7, 0, -1):
            if morework & (1 << j):
                mantissa += 2.0 ** (-count)
            count += 1

    mantissa += 2.0 ** -1
    fp *= mantissa
    if exponent == 0:
        fp = 0.0
    return fp


def fmt_g(value):
    """Approximate C's printf("%g", value)."""
    return "{:g}".format(value)


# ---------------------------------------------------------------------------
# Main detokenise routine
# ---------------------------------------------------------------------------

def detokenise(path, machine, out):
    with open(path, 'rb') as f:
        stream = ByteStream(f)

        if machine.header_bytes is not None:
            first = stream.get8()
            if first not in machine.header_bytes:
                print("This isn't an MZ BASIC file", file=sys.stderr)
                sys.exit(1)

        f.seek(0x80, 0)
        stream.eof = False

        while not stream.eof:
            # line length (unused beyond checking for end-of-program marker)
            length = stream.get16()
            if stream.eof:
                break
            if length == 0x0:
                break  # end of program

            lineno = stream.get16()
            out(f"{lineno} ")

            quote = False
            token = False

            while True:
                work = stream.get8()
                if stream.eof:
                    break

                if work == machine.eol_byte:
                    out("\n")
                elif work in (0x0B, 0x0C):
                    if not quote:
                        morework = stream.get16()
                        out(f"{morework}")
                elif work == 0x11:
                    if not quote:
                        morework = stream.get16()
                        out(f"${morework:X}")
                elif work == 0x15:
                    if not quote:
                        fp = decode_float(stream.get8)
                        out(fmt_g(fp))

                if work >= 0x80 and not quote and not token:
                    text, is_rem = machine.decode_token(work, stream.get8)
                    out(text)
                    if is_rem:
                        token = True
                elif work != 0x0:
                    if work >= 0x80:
                        out(SHARP_ASCII[work])
                    elif work == ord('"'):
                        quote = not quote
                        out('"')
                    elif work >= 0x19:
                        out(chr(work))

                    if work == 0x3A:  # ':'
                        token = False

                if work == machine.eol_byte:
                    break


def main():
    parser = argparse.ArgumentParser(
        description="Detokenise a Sharp MZ BASIC .MZF program file.")
    parser.add_argument('infile', help="path to the .MZF file")
    parser.add_argument('--machine', required=True, choices=sorted(MACHINES),
                         help="source machine BASIC dialect: "
                              "mz80a (Sharp MZ-80A), mz80k (Sharp MZ-80K), "
                              "mz700 (Sharp MZ-700)")
    args = parser.parse_args()

    machine = MACHINES[args.machine]
    detokenise(args.infile, machine, lambda s: sys.stdout.write(s))


if __name__ == '__main__':
    main()
