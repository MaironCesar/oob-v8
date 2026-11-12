import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location("model", pathlib.Path(__file__).with_name("boundary_model.py"))
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


class BoundaryModelTests(unittest.TestCase):
    def test_equal_length_and_capacity(self):
        a = model.ArrayModel([1.1, 2.2, 3.3], 3, "double")
        with self.assertRaises(IndexError):
            a.vulnerable_read()
        self.assertEqual(a.corrected_read(), (False, None))
        self.assertEqual(a.alternative_read(2), (True, 3.3))
        self.assertEqual(a.alternative_read(3), (False, None))
        self.assertEqual(a.map_kind, "double")

    def test_spare_capacity_is_still_logically_invalid(self):
        a = model.ArrayModel([1.1, 2.2, 3.3, 0.0], 3, "double")
        self.assertEqual(a.vulnerable_read(), 0.0)
        self.assertEqual(a.corrected_read(), (False, None))
        self.assertEqual(a.alternative_read(3), (False, None))

    def test_invalid_indices_and_kind(self):
        a = model.ArrayModel([1.1], 1, "double")
        for index in (-1, 1, 1.5, "0"):
            self.assertEqual(a.alternative_read(index), (False, None))
        b = model.ArrayModel([object()], 1, "object")
        self.assertEqual(b.corrected_read(), (False, None))
        self.assertEqual(b.alternative_read(0), (False, None))

    def test_invalid_model_state(self):
        with self.assertRaises(ValueError):
            model.ArrayModel([1], 2, "double")


if __name__ == "__main__":
    unittest.main()
