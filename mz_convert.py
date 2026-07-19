#!/usr/bin/env python3
"""
mz_convert.py - Convert a Sharp MZ BASIC .MZF program between MZ-80A,
MZ-80K, and MZ-700 dialects, or dump it as text.

    mz_convert.py --from mz80k --to mz700 IN.MZF OUT.MZF
    mz_convert.py --from mz80a --to mz80a --outform text IN.MZF OUT.TXT

Tokens are matched between dialects by their printed text (e.g. "PRINT",
"GOTO", "LEFT$(" ...). If the target dialect has no token with the exact
same text as a source token, that token is replaced with the target's
PRINT token instead (per the requested behaviour) and a note is written
to stderr.

Everything that isn't a keyword token - line numbers, embedded line
number references (0x0B/0x0C), hex integers (0x11), floating point
literals (0x15), quoted/plain characters - is carried over unchanged,
since that encoding is identical across all three dialects (only the
>=0x80 token byte values and the end-of-line marker differ between
them).

For --outform mzf, the output is wrapped in a standard 128-byte MZF
header (file type, 16-byte space-padded filename, terminator, size,
load address, exec address, reserved area) as in the sample
converttomzf.py, but with the filename/size/type filled in for real
rather than hardcoded to "MYSTERY".
"""

import argparse
import struct
import sys


# ---------------------------------------------------------------------------
# Shared "sharp ASCII" lower-case table (identical across all three machines)
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
    out = list(entries) + [''] * (size - len(entries))
    return out[:size]


# ---------------------------------------------------------------------------
# Per-machine token tables (see mz_detokenise.py for full provenance notes).
# ---------------------------------------------------------------------------

TOKENS1_MZ80A = pad([
    "REM", "DATA", "", "", "READ", "LIST", "RUN", "NEW", "PRINT", "LET", "FOR",
    "IF", "THEN", "GOTO", "GOSUB", "RETURN", "NEXT", "STOP", "END", "", "ON", "LOAD",
    "SAVE", "VERIFY", "POKE", "DIM", "DEF FN", "INPUT", "RESTORE", "CLR", "MUSIC", "TEMPO", "USR(",
    "WOPEN", "ROPEN", "CLOSE", "MON", "LIMIT", "CONT", "GET", "INP#", "OUT#", "CURSOR", "SET",
    "RESET", "", "", "", "", "", "", "AUTO", "", "", "COPY/P",
    "PAGE/P",
])

TOKENS2_MZ80A = pad([
    "", "", "", "><", "<>", "=<", "<=", "=>", ">=", "", ">",
    "<", "", "", "", "", "", "", "", "", "", "",
    "", "", "", "", "", "", "", "", "TO", "STEP", "LEFT$(",
    "RIGHT$(", "MID$(", "LEN(", "CHR$(", "STR$(", "ASC(", "VAL(", "PEEK(", "TAB(", "SPACE$(", "SIZE",
    "", "", "", "STRING$(", "", "CHARACTER$(", "CRS", "CRS", "", "", "",
    "", "", "", "", "", "", "", "", "", "RND(", "SIN(",
    "COS(", "TAN(", "ATN(", "EXP(", "INT(", "LOG(", "LN(", "ABS(", "SGN(", "SQR(",
])

TOKENS1_MZ80K = pad([
    "REM", "DATA", "LIST", "RUN", "NEW", "PRINT", "LET", "FOR", "IF", "GOTO", "READ",
    "GOSUB", "RETURN", "NEXT", "STOP", "END", "ON", "LOAD", "SAVE", "VERIFY", "POKE", "DIM",
    "DEF FN", "INPUT", "RESTORE", "CLR", "MUSIC", "TEMPO", "USR(", "WOPEN", "ROPEN", "CLOSE", "BYE",
    "LIMIT", "CONT", "SET", "RESET", "GET", "INP#", "OUT#", "", "", "", "",
    "", "THEN", "TO", "STEP", "><", "<>", "=<", "<=", "=>", ">=", "=",
    ">", "<", "AND", "OR", "NOT", "+", "-", "*", "/", "LEFT$(", "RIGHT$(",
    "MID$(", "LEN(", "CHR$(", "STR$(", "ASC(", "VAL(", "PEEK(", "TAB(", "SP(", "SIZE", "",
    "", "", "^", "RND(", "SIN(", "COS(", "TAN(", "ATN(", "EXP(", "INT(", "LOG(",
    "LN(", "ABS(", "SGN(", "SQR(",
])

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


def decode_token_mz80a(work, get8):
    if work == 0x80:
        w2 = get8()
        idx = w2 - 0x80
        text = TOKENS1_MZ80A[idx] if 0 <= idx < len(TOKENS1_MZ80A) else ''
        return text, (w2 == 0x80)
    idx = work - 0x80
    text = TOKENS2_MZ80A[idx] if 0 <= idx < len(TOKENS2_MZ80A) else ''
    return text, False


def decode_token_mz80k(work, get8):
    idx = work - 0x80
    text = TOKENS1_MZ80K[idx] if 0 <= idx < len(TOKENS1_MZ80K) else ''
    return text, work in (0x80, 0x81)


def decode_token_mz700(work, get8):
    if work == 0xFE:
        w2 = get8()
        idx = w2 - 0x80
        text = ETOKENS1_MZ700[idx] if 0 <= idx < len(ETOKENS1_MZ700) else ''
        return text, False
    if work == 0xFF:
        w2 = get8()
        idx = w2 - 0x80
        text = ETOKENS2_MZ700[idx] if 0 <= idx < len(ETOKENS2_MZ700) else ''
        return text, False
    idx = work - 0x80
    text = TOKENS_MZ700[idx] if 0 <= idx < len(TOKENS_MZ700) else ''
    return text, work in (0x97, 0x94)  # REM, DATA


class Machine:
    def __init__(self, key, name, header_bytes, eol_byte, decode_token):
        self.key = key
        self.name = name
        self.header_bytes = header_bytes  # None => no header check (MZ-700)
        self.eol_byte = eol_byte
        self.decode_token = decode_token


MACHINES = {
    'mz80a': Machine('mz80a', 'MZ-80A', {0x05, 0x02}, 0x0D, decode_token_mz80a),
    'mz80k': Machine('mz80k', 'MZ-80K', {0x05, 0x02}, 0x0D, decode_token_mz80k),
    'mz700': Machine('mz700', 'MZ-700', None, 0x00, decode_token_mz700),
}


def build_token_encode_table(key):
    """Inverse of decode_token: token text -> bytes needed to encode it."""
    table = {}
    if key == 'mz80a':
        for i, text in enumerate(TOKENS1_MZ80A):
            if text:
                table.setdefault(text, bytes([0x80, 0x80 + i]))
        for i, text in enumerate(TOKENS2_MZ80A):
            if text:
                table.setdefault(text, bytes([0x80 + i]))
    elif key == 'mz80k':
        for i, text in enumerate(TOKENS1_MZ80K):
            if text:
                table.setdefault(text, bytes([0x80 + i]))
    elif key == 'mz700':
        for i, text in enumerate(TOKENS_MZ700):
            if text:
                table.setdefault(text, bytes([0x80 + i]))
        for i, text in enumerate(ETOKENS1_MZ700):
            if text:
                table.setdefault(text, bytes([0xFE, 0x80 + i]))
        for i, text in enumerate(ETOKENS2_MZ700):
            if text:
                table.setdefault(text, bytes([0xFF, 0x80 + i]))
    else:
        raise ValueError(key)
    return table


def _strip_paren(text):
    return text[:-1] if text.endswith('(') else text


def build_lookup_tables(key):
    """Returns (exact, normalized):
      exact:      token text -> bytes
      normalized: text with any trailing '(' stripped -> (target_text, bytes)

    normalized exists because MZ-80A/MZ-80K bake the opening parenthesis
    into function-style token text (e.g. "SIN("), while MZ-700 encodes the
    bare name ("SIN") and expects a separate literal '(' character
    afterwards. Matching only on exact text would treat these as unrelated
    and needlessly fall back to PRINT for almost every function call when
    converting to/from MZ-700, so exact matches are tried first and
    paren-insensitive matches are the fallback before giving up.
    """
    exact = build_token_encode_table(key)
    normalized = {}
    for text, b in exact.items():
        norm = _strip_paren(text)
        normalized.setdefault(norm, (text, b))
    return exact, normalized


# Some symbols are a tokenised keyword on one dialect but plain ASCII
# punctuation on another (not tokenised at all there). MZ-80A has no "="
# token (only "><", "<>", "=<", "<=", "=>", ">="), unlike MZ-80K/MZ-700
# which both tokenise "=" - on MZ-80A it's just the literal character.
# Keyed by (target_machine_key, source_token_text) -> ASCII byte to emit
# instead of a token.
ASCII_TOKEN_FALLBACK = {
    ('mz80a', '='): ord('='),
}


def resolve_tokens(lines, to_key, report):
    """Resolve every source ('token', text) atom against the target
    dialect, producing ('token_r', target_text, target_bytes) atoms, and
    insert/drop a literal '(' character atom where the two dialects'
    parenthesis conventions differ, so the token stream stays balanced
    for both text and MZF output."""
    exact, normalized = build_lookup_tables(to_key)
    fallback_text = 'PRINT'
    fallback_bytes = exact['PRINT']

    resolved = []
    for lineno, atoms in lines:
        new_atoms = []
        skip_next_open_paren = False
        for atom in atoms:
            if skip_next_open_paren:
                skip_next_open_paren = False
                if atom[0] == 'char' and atom[1] == 0x28:  # '('
                    continue  # already implied by the target token itself

            if atom[0] != 'token':
                new_atoms.append(atom)
                continue

            text = atom[1]

            ascii_fallback = ASCII_TOKEN_FALLBACK.get((to_key, text))
            if ascii_fallback is not None:
                new_atoms.append(('char', ascii_fallback))
                continue

            if text in exact:
                target_text, target_bytes = text, exact[text]
            else:
                norm = _strip_paren(text)
                if norm in normalized:
                    target_text, target_bytes = normalized[norm]
                else:
                    report(text)
                    target_text, target_bytes = fallback_text, fallback_bytes

            new_atoms.append(('token_r', target_text, target_bytes))

            source_has_paren = text.endswith('(')
            target_has_paren = target_text.endswith('(')
            if source_has_paren and not target_has_paren:
                new_atoms.append(('char', 0x28))  # supply the missing '('
            elif target_has_paren and not source_has_paren:
                skip_next_open_paren = True  # drop the now-redundant '('

        resolved.append((lineno, new_atoms))
    return resolved


# ---------------------------------------------------------------------------
# Shared MZF floating point decode (identical format across all 3 machines)
# ---------------------------------------------------------------------------

def decode_float(raw5):
    it = iter(raw5)
    exponent = next(it)
    if exponent & 0x80:
        exponent -= 0x80
    elif exponent != 0:
        exponent = 0x80 - exponent

    fp = 2.0 ** exponent
    count = 1
    mantissa = 0.0
    for _ in range(4):
        b = next(it)
        for j in range(7, 0, -1):
            if b & (1 << j):
                mantissa += 2.0 ** (-count)
            count += 1

    mantissa += 2.0 ** -1
    fp *= mantissa
    if exponent == 0:
        fp = 0.0
    return fp


def fmt_g(value):
    return "{:g}".format(value)


# ---------------------------------------------------------------------------
# Parsing: source machine bytes -> a machine-independent list of lines,
# each a list of "atoms". Everything except tokens is stored as raw bytes
# so it can be passed straight through to any target machine unchanged.
# ---------------------------------------------------------------------------

class ParseError(Exception):
    pass


def parse_program(path, machine):
    lines = []
    with open(path, 'rb') as f:
        def get8():
            b = f.read(1)
            if not b:
                raise ParseError("unexpected end of file")
            return b[0]

        if machine.header_bytes is not None:
            first = f.read(1)
            if not first or first[0] not in machine.header_bytes:
                raise ParseError(
                    f"{path} isn't a {machine.name} MZ BASIC file "
                    f"(expected header byte {sorted(machine.header_bytes)}, "
                    f"got {first[0] if first else 'EOF'})")

        f.seek(0x80, 0)

        while True:
            two = f.read(2)
            if len(two) < 2:
                break
            length = two[0] + (two[1] << 8)
            if length == 0:
                break  # end of program

            lnb = f.read(2)
            if len(lnb) < 2:
                break
            lineno = lnb[0] + (lnb[1] << 8)

            atoms = []
            quote = False
            token = False

            while True:
                b = f.read(1)
                if not b:
                    break
                work = b[0]

                if work == machine.eol_byte:
                    atoms.append(('eol',))
                elif work in (0x0B, 0x0C) and not quote:
                    raw = f.read(2)
                    atoms.append(('lineref', work, raw))
                elif work == 0x11 and not quote:
                    raw = f.read(2)
                    atoms.append(('hexint', raw))
                elif work == 0x15 and not quote:
                    raw = f.read(5)
                    atoms.append(('float', raw))

                if work >= 0x80 and not quote and not token:
                    text, is_rem = machine.decode_token(work, get8)
                    atoms.append(('token', text))
                    if is_rem:
                        token = True
                elif work != 0x00:
                    if work >= 0x80:
                        atoms.append(('char', work))
                    elif work == 0x22:  # "
                        quote = not quote
                        atoms.append(('char', work))
                    elif work >= 0x19:
                        atoms.append(('char', work))
                    if work == 0x3A:  # :
                        token = False

                if work == machine.eol_byte:
                    break

            lines.append((lineno, atoms))
    return lines


# ---------------------------------------------------------------------------
# Emitting: atoms -> text, or atoms -> target-machine tokenised bytes
# ---------------------------------------------------------------------------

def render_char(work):
    if work >= 0x80:
        return SHARP_ASCII[work]
    if work == 0x22:
        return '"'
    if work >= 0x19:
        return chr(work)
    return ''


def emit_text(resolved_lines):
    out = []
    for lineno, atoms in resolved_lines:
        row = [str(lineno), ' ']
        for atom in atoms:
            kind = atom[0]
            if kind == 'token_r':
                row.append(atom[1])
            elif kind == 'char':
                row.append(render_char(atom[1]))
            elif kind == 'lineref':
                _, _, raw = atom
                value = raw[0] + (raw[1] << 8)
                row.append(str(value))
            elif kind == 'hexint':
                raw = atom[1]
                value = raw[0] + (raw[1] << 8)
                row.append(f"${value:X}")
            elif kind == 'float':
                row.append(fmt_g(decode_float(atom[1])))
            elif kind == 'eol':
                row.append('\n')
        out.append(''.join(row))
    return ''.join(out)


def emit_mzf_body(resolved_lines, target):
    out = bytearray()
    for lineno, atoms in resolved_lines:
        body = bytearray()
        for atom in atoms:
            kind = atom[0]
            if kind == 'token_r':
                body += atom[2]
            elif kind == 'char':
                body.append(atom[1])
            elif kind == 'lineref':
                code_byte, _, raw = atom
                body.append(code_byte)
                body += raw
            elif kind == 'hexint':
                body.append(0x11)
                body += atom[1]
            elif kind == 'float':
                body.append(0x15)
                body += atom[1]
            elif kind == 'eol':
                pass  # added explicitly below
        body.append(target.eol_byte)

        length_value = 2 + len(body)  # lineno (2 bytes) + body (incl. EOL)
        out += struct.pack('<H', length_value)
        out += struct.pack('<H', lineno)
        out += body
    out += struct.pack('<H', 0)  # end of program marker
    return bytes(out)


# ---------------------------------------------------------------------------
# MZF file header (see converttomzf.py) - 128 bytes total:
#   1  file type
#  16  filename, space-padded
#   1  0x0D terminator
#   2  data size (LE)
#   2  load address (LE)
#   2  exec address (LE)
# 104  reserved / comment (spaces)
# ---------------------------------------------------------------------------

def build_mzf_header(name, data_len, file_type=0x02, load_addr=0x1200, exec_addr=None):
    if exec_addr is None:
        exec_addr = load_addr
    name_bytes = name.upper().encode('ascii', errors='replace')[:16].ljust(16, b' ')
    header = bytearray()
    header.append(file_type)
    header += name_bytes
    header.append(0x0D)
    header += struct.pack('<H', data_len)
    header += struct.pack('<H', load_addr)
    header += struct.pack('<H', exec_addr)
    header += b' ' * 104
    assert len(header) == 0x80
    return bytes(header)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def auto_int(s):
    return int(s, 0)


def main():
    parser = argparse.ArgumentParser(
        description="Convert a Sharp MZ BASIC .MZF program between MZ-80A, "
                    "MZ-80K, and MZ-700 dialects (or dump it as text).")
    parser.add_argument('infile')
    parser.add_argument('outfile')
    parser.add_argument('--from', dest='from_machine', required=True,
                         choices=sorted(MACHINES), help="source dialect")
    parser.add_argument('--to', dest='to_machine', required=True,
                         choices=sorted(MACHINES), help="target dialect")
    parser.add_argument('--outform', choices=['text', 'mzf'], default='mzf',
                         help="output format (default: mzf)")
    parser.add_argument('--name',
                         help="MZF filename field (default: OUTFILE's "
                              "basename, without extension)")
    parser.add_argument('--load-address', type=auto_int, default=0x1200,
                         help="MZF header load address (default: 0x1200)")
    parser.add_argument('--exec-address', type=auto_int, default=None,
                         help="MZF header exec address (default: same as "
                              "--load-address)")
    parser.add_argument('--file-type', type=auto_int, default=0x02,
                         help="MZF header file-type/attribute byte "
                              "(default: 0x02, BASIC program)")
    parser.add_argument('-q', '--quiet', action='store_true',
                         help="don't report tokens substituted with PRINT")
    args = parser.parse_args()

    from_m = MACHINES[args.from_machine]
    to_m = MACHINES[args.to_machine]

    try:
        lines = parse_program(args.infile, from_m)
    except ParseError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    substitutions = {}

    def report(text):
        substitutions[text] = substitutions.get(text, 0) + 1

    resolved_lines = resolve_tokens(lines, to_m.key, report)

    if args.outform == 'text':
        text = emit_text(resolved_lines)
        with open(args.outfile, 'w', newline='') as f:
            f.write(text)
    else:
        body = emit_mzf_body(resolved_lines, to_m)
        import os
        name = args.name or os.path.splitext(os.path.basename(args.outfile))[0]
        header = build_mzf_header(
            name, len(body),
            file_type=args.file_type,
            load_addr=args.load_address,
            exec_addr=args.exec_address,
        )
        with open(args.outfile, 'wb') as f:
            f.write(header)
            f.write(body)

    if substitutions and not args.quiet:
        print(f"Note: {sum(substitutions.values())} token(s) had no "
              f"{to_m.name} equivalent and were replaced with PRINT:",
              file=sys.stderr)
        for text, count in sorted(substitutions.items(),
                                   key=lambda kv: -kv[1]):
            label = text if text else '(empty/unknown token)'
            print(f"  {label!r}: {count}", file=sys.stderr)


if __name__ == '__main__':
    main()
