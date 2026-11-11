#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Reproducible comparison with the upstream optimized PIN search."""

import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import platform
from statistics import median
from time import perf_counter

import solve_fast as fast


def benchmark(repetitions=3):
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("upstream_fluffy", root / "solution" / "crack.py")
    upstream = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(upstream)
    token = "I6X6vyQzRuH"
    plaintext = b"CTF{benchmark_dos_blocos}"
    pin = 1337
    max_pin = 2000
    ciphertext = upstream.encrypt(pin, token, plaintext)
    original_times = []
    block_times = []
    for _ in range(repetitions):
        with contextlib.redirect_stdout(io.StringIO()):
            start = perf_counter()
            patterns = upstream.find_all_token_patterns(token.encode())
            recovered = upstream.crack(patterns, ciphertext, max_pin=max_pin)
            original_times.append(perf_counter() - start)
        if recovered != plaintext:
            raise AssertionError("O método original não recuperou a mensagem do experimento.")
        # Include table construction; clear the cache to avoid warmed-table bias.
        fast.round_permutation.cache_clear()
        start = perf_counter()
        candidates = fast.find_candidates(fast.decode62(ciphertext), fast.decode62(token), max_pin=max_pin)
        block_times.append(perf_counter() - start)
        if [(c.pin, c.plaintext) for c in candidates] != [(pin, plaintext.decode())]:
            raise AssertionError("O método por blocos divergiu do resultado esperado.")
    original_median = median(original_times)
    block_median = median(block_times)
    return {
        "python": platform.python_version(),
        "system": platform.system(),
        "repetitions": repetitions,
        "scope": f"Um token conhecido; PINs de 1 a 2000; mensagem sintética de {len(plaintext)} bytes.",
        "methodology": "Original encerra no primeiro texto ASCII; blocos percorre todos os PINs e inclui construção das tabelas e recifragem. Saída de diagnóstico do original capturada em memória. Tempos dependem da máquina.",
        "token": token,
        "pin": pin,
        "max_pin": max_pin,
        "ciphertext": ciphertext,
        "plaintext": plaintext.decode(),
        "matching_results": True,
        "original_seconds": [round(value, 6) for value in original_times],
        "blocks_seconds": [round(value, 6) for value in block_times],
        "original_median_seconds": round(original_median, 6),
        "blocks_median_seconds": round(block_median, 6),
        "median_speedup": round(original_median / block_median, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Comparar a busca original com a busca por blocos.")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("Use ao menos uma repetição.")
    report = benchmark(args.repetitions)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Mediana original: {report['original_median_seconds']:.6f} s")
        print(f"Mediana por blocos: {report['blocks_median_seconds']:.6f} s")
        print(f"Razão medida: {report['median_speedup']:.2f}x")
        print(report["scope"])
        print(report["methodology"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
