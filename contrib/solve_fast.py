#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Solve Fluffy by composing one period of rounds into byte permutations.

Additional implementation for this repository. The cipher and its 16-round
token periodicity are documented in the upstream Google CTF solution.
Only Python's standard library is required (Python 3.9 or newer).
"""

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime
from functools import lru_cache
import hashlib
import json
from math import lcm
from time import perf_counter
from zoneinfo import ZoneInfo


ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
PRINTABLE = bytes(range(32, 127))
IDENTITY = bytes(range(256))
CHALLENGES = (
    ("04/08/2023 13:37", "fmMf7mIMbHcPoQmLGx1CO0XVGBmhjTaYhB0"),
    ("07/09/2024 18:52", "5O6WRgCajs3QSTyohnu2hldds18mjkx"),
    ("03/03/2025 22:07", "fgv99dOvazsvEESh7DPKbb3k0I3RW"),
)


def rol8(value, shift):
    shift %= 8
    return ((value << shift) | (value >> (8 - shift))) & 255


def ror8(value, shift):
    return rol8(value, -shift)


def encode62(data):
    value = int.from_bytes(data, "big")
    result = ""
    while value:
        value, digit = divmod(value, 62)
        result = ALPHABET[digit] + result
    return result


def decode62(text):
    if not text or any(char not in ALPHABET for char in text):
        raise ValueError("A entrada Base62 deve ser não vazia e usar o alfabeto da cifra.")
    value = 0
    for char in text:
        value = value * 62 + ALPHABET.index(char)
    return value.to_bytes((value.bit_length() + 7) // 8, "big")


def token_at(timestamp):
    return encode62(hashlib.sha1(f"gctf25_{timestamp}".encode()).digest()[:8])


def token_schedule(token, pin_mod, rounds):
    if not token:
        raise ValueError("O token decodificado não pode ser vazio.")
    dynamic = token
    states = []
    for index in range(rounds):
        states.append(dynamic)
        dynamic = dynamic[1:] + dynamic[:1]
        shift = (pin_mod ^ ((index & 3) + 1)) % 8
        dynamic = bytes(ror8(value, shift) for value in dynamic)
    return states


def encrypt_bytes(plaintext, pin, token):
    """Independent forward implementation, used to confirm each candidate."""
    if not 1 <= pin <= 9999 or not plaintext:
        raise ValueError("É necessário um PIN entre 1 e 9999 e uma mensagem não vazia.")
    state = plaintext
    for dynamic in token_schedule(token, pin % 8, pin):
        state = bytes(
            rol8((value + dynamic[pos % len(dynamic)]) & 255, pos % 8)
            for pos, value in enumerate(state)
        )
        state = state[-1:] + state[:-1]
    return state


@lru_cache(maxsize=2048)
def round_permutation(token_byte, rotation):
    return bytes(rol8((value + token_byte) & 255, rotation) for value in range(256))


def inverse_block(schedule, length):
    """Return (source position, inverse substitution) for every output byte.

    Rounds never mix two message bytes. A block moves a byte to a known position
    and applies a permutation to its value, so all 256 inputs can be tabulated.
    bytes.translate composes those permutations in C, outside the PIN loop.
    """
    tables = []
    for start in range(length):
        forward = IDENTITY
        for index, dynamic in enumerate(schedule):
            pos = (start + index) % length
            forward = forward.translate(round_permutation(dynamic[pos % len(dynamic)], pos % 8))
        inverse = bytearray(256)
        for original, encrypted in enumerate(forward):
            inverse[encrypted] = original
        tables.append(((start + len(schedule)) % length, bytes(inverse)))
    return tuple(tables)


def undo_prefix(ciphertext, schedule, rounds):
    state = ciphertext
    for index in range(rounds - 1, -1, -1):
        state = state[1:] + state[:1]
        dynamic = schedule[index]
        state = bytes(
            (ror8(value, pos % 8) - dynamic[pos % len(dynamic)]) & 255
            for pos, value in enumerate(state)
        )
    return state


@dataclass(frozen=True)
class Candidate:
    pin: int
    plaintext: str
    reencryption_verified: bool = True


def find_candidates(ciphertext, token, max_pin=9999, prefix=b""):
    """Check every allowed PIN for one known token, returning printable results.

    PIN = period*q + residue. For a fixed residue the PIN modulo 8 is fixed,
    hence its round schedule is fixed. Undo the residue once and then reuse
    the inverse block q times, checking one candidate after each application.
    """
    if not 1 <= max_pin <= 9999 or not ciphertext or not token:
        raise ValueError("Informe ciphertext e token não vazios e max_pin entre 1 e 9999.")
    # Base62 discards leading zero bytes. Shorter tokens need a longer block.
    period = lcm(16, len(token))
    blocks = {}
    schedules = {}
    candidates = []
    for residue in range(min(period, max_pin + 1)):
        pin_mod = residue % 8
        if pin_mod not in blocks:
            schedule = token_schedule(token, pin_mod, period)
            schedules[pin_mod] = schedule
            blocks[pin_mod] = inverse_block(schedule, len(ciphertext))
        state = undo_prefix(ciphertext, schedules[pin_mod], residue)
        block = blocks[pin_mod]
        for pin in range(residue, max_pin + 1, period):
            if pin and state.startswith(prefix) and not state.translate(None, PRINTABLE):
                if encrypt_bytes(state, pin, token) == ciphertext:
                    candidates.append(Candidate(pin, state.decode("ascii")))
            if pin + period <= max_pin:
                state = bytes(table[state[source]] for source, table in block)
    return sorted(candidates, key=lambda item: item.pin)


def solve(time_text, ciphertext, timezone="Europe/Zurich", max_pin=9999, prefix=b""):
    start = perf_counter()
    minute = datetime.strptime(time_text, "%d/%m/%Y %H:%M").replace(tzinfo=ZoneInfo(timezone))
    timestamp = int(minute.timestamp())
    encrypted = decode62(ciphertext)
    results = []
    periods = set()
    for second in range(60):
        token_text = token_at(timestamp + second)
        token = decode62(token_text)
        periods.add(lcm(16, len(token)))
        for candidate in find_candidates(encrypted, token, max_pin, prefix):
            results.append({"second": second, "token": token_text, **asdict(candidate)})
    return {
        "time": time_text,
        "timezone": timezone,
        "ciphertext": ciphertext,
        "tokens_checked": 60,
        "pin_candidates_checked": 60 * max_pin,
        "block_periods": sorted(periods),
        "elapsed_seconds": round(perf_counter() - start, 6),
        "candidates": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Solucionador adicional de Fluffy por blocos de permutações.")
    parser.add_argument("--all", action="store_true", help="Resolver os três segredos publicados (padrão).")
    parser.add_argument("--time", help="Data e minuto no formato dia/mês/ano hora:minuto.")
    parser.add_argument("--ciphertext", help="Segredo cifrado em Base62.")
    parser.add_argument("--timezone", default="Europe/Zurich")
    parser.add_argument("--max-pin", type=int, default=9999)
    parser.add_argument("--prefix", default="", help="Prefixo ASCII conhecido, opcional.")
    parser.add_argument("--json", action="store_true", help="Emitir um relatório JSON.")
    args = parser.parse_args()
    if bool(args.time) != bool(args.ciphertext):
        parser.error("--time e --ciphertext devem ser informados juntos.")
    if args.all and args.time:
        parser.error("Escolha --all ou um segredo informado manualmente.")
    if not 1 <= args.max_pin <= 9999:
        parser.error("--max-pin deve estar entre 1 e 9999.")
    try:
        prefix = args.prefix.encode("ascii")
    except UnicodeEncodeError:
        parser.error("--prefix deve conter apenas caracteres ASCII.")
    specifications = ((args.time, args.ciphertext),) if args.time else CHALLENGES
    start = perf_counter()
    results = [solve(date, text, args.timezone, args.max_pin, prefix) for date, text in specifications]
    unique = all(len(result["candidates"]) == 1 for result in results)
    flag = "".join(result["candidates"][0]["plaintext"] for result in results) if unique and not args.time else None
    report = {
        "method": "composicao_de_permutacoes_por_blocos",
        "max_pin": args.max_pin,
        "results": results,
        "flag": flag,
        "total_seconds": round(perf_counter() - start, 6),
    }
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for index, result in enumerate(results, 1):
            print(f"Segredo {index}: {len(result['candidates'])} candidato(s), {result['elapsed_seconds']:.3f} s")
            for candidate in result["candidates"]:
                print(f"  segundo={candidate['second']:02}, PIN={candidate['pin']:04}, token={candidate['token']}")
                print(f"  texto={candidate['plaintext']!r}; recifragem conferida")
        if flag:
            print(f"Flag: {flag}")
        print(f"Tempo total: {report['total_seconds']:.3f} s")
    return 0 if unique else 1


if __name__ == "__main__":
    raise SystemExit(main())
