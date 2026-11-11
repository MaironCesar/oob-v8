# SPDX-License-Identifier: Apache-2.0
"""Compatibility checks against the unmodified upstream implementation."""

import contextlib
from datetime import datetime
import importlib.util
import io
from pathlib import Path
import unittest
from zoneinfo import ZoneInfo

import solve_fast as fast


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("upstream_fluffy", ROOT / "solution" / "crack.py")
upstream = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upstream)


class BlockSolverTests(unittest.TestCase):
    def test_encoding_and_token_generation_match_upstream(self):
        for data in (b"\x01", b"\x00abcdefg", b"12345678", b"CTF{base62}"):
            encoded = fast.encode62(data)
            self.assertEqual(encoded, upstream.base62_encode(data))
            self.assertEqual(fast.decode62(encoded), upstream.base62_decode(encoded))
        for timestamp in (1691149047, 1725727951, 1741036068):
            self.assertEqual(fast.token_at(timestamp), upstream.generate_token(timestamp).decode())

    def test_forward_cipher_matches_upstream_for_different_lengths(self):
        token = b"12345678"
        for length in (1, 7, 8, 16, 23, 24, 26, 32):
            for pin in (1, 7, 15, 16, 17, 31, 32, 255):
                plaintext = bytes((37 + 17 * pos) % 256 for pos in range(length))
                with self.subTest(length=length, pin=pin):
                    actual = fast.encode62(fast.encrypt_bytes(plaintext, pin, token))
                    self.assertEqual(actual, upstream.encrypt(pin, fast.encode62(token), plaintext))

    def test_token_schedule_repeats_for_all_pin_classes(self):
        for token in (b"\x01", b"abc", b"abcdefg", b"12345678"):
            period = fast.lcm(16, len(token))
            for pin_mod in range(8):
                states = fast.token_schedule(token, pin_mod, period + 1)
                self.assertEqual(states[0], states[period])

    def test_pin_recovery_at_block_boundaries(self):
        token = b"12345678"
        plaintext = b"CTF{demonstracao_de_blocos}"
        for pin in (1, 7, 8, 15, 16, 17, 31, 32, 63, 64, 255):
            cipher = upstream.encrypt(pin, fast.encode62(token), plaintext)
            candidates = fast.find_candidates(fast.decode62(cipher), token, max_pin=255)
            with self.subTest(pin=pin):
                self.assertEqual([(c.pin, c.plaintext) for c in candidates], [(pin, plaintext.decode())])

    def test_short_tokens_after_base62_discards_zero_bytes(self):
        plaintext = b"CTF{token_com_zero_inicial}"
        for token in (b"\x01", b"abc", b"abcdefg"):
            for pin in (16, 31, 112, 113):
                cipher = upstream.encrypt(pin, fast.encode62(b"\x00" + token), plaintext)
                candidates = fast.find_candidates(fast.decode62(cipher), token, max_pin=128)
                with self.subTest(token_length=len(token), pin=pin):
                    self.assertEqual([(c.pin, c.plaintext) for c in candidates], [(pin, plaintext.decode())])

    def test_published_secrets_decrypt_and_reencrypt_with_upstream(self):
        fixtures = (
            ("I6X6vyQzRuH", 8126, b"CTF{Ok4y_h4v3_u_0ptim1zed_"),
            ("BMiZFI8Xr3Q", 5178, b"brUt3_f0rcE_0R_y0u_jUst"),
            ("KZ95PpF1RFq", 7490, b"_uSeD_a_l0t_0f_c0Res?}"),
        )
        for (_, cipher), (token, pin, plaintext) in zip(fast.CHALLENGES, fixtures):
            with self.subTest(pin=pin):
                self.assertEqual(upstream.decrypt(pin, token, cipher), plaintext)
                self.assertEqual(upstream.encrypt(pin, token, plaintext), cipher)
                self.assertEqual(fast.encode62(fast.encrypt_bytes(plaintext, pin, fast.decode62(token))), cipher)

    def test_complete_minute_search_without_known_pin_or_second(self):
        date = "04/08/2023 13:37"
        timestamp = int(datetime.strptime(date, "%d/%m/%Y %H:%M").replace(tzinfo=ZoneInfo("Europe/Zurich")).timestamp())
        token = upstream.generate_token(timestamp + 27).decode()
        plaintext = b"CTF{busca_do_segundo_e_pin}"
        cipher = upstream.encrypt(37, token, plaintext)
        result = fast.solve(date, cipher, max_pin=64)
        self.assertEqual(result["tokens_checked"], 60)
        self.assertEqual(result["pin_candidates_checked"], 3840)
        self.assertEqual(len(result["candidates"]), 1)
        candidate = result["candidates"][0]
        self.assertEqual((candidate["second"], candidate["pin"], candidate["plaintext"]), (27, 37, plaintext.decode()))

    def test_results_match_original_optimized_search(self):
        token = "I6X6vyQzRuH"
        plaintext = b"CTF{comparacao_dos_metodos}"
        cipher = upstream.encrypt(137, token, plaintext)
        with contextlib.redirect_stdout(io.StringIO()):
            original_result = upstream.crack(upstream.find_all_token_patterns(token.encode()), cipher, max_pin=256)
        candidates = fast.find_candidates(fast.decode62(cipher), fast.decode62(token), max_pin=256)
        self.assertEqual(original_result, plaintext)
        self.assertEqual([(c.pin, c.plaintext) for c in candidates], [(137, plaintext.decode())])


if __name__ == "__main__":
    unittest.main()
