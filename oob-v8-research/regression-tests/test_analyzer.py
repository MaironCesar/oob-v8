import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("analyzer", ROOT / "contribution" / "analyzer.py")
analyzer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyzer)


class AnalyzerTests(unittest.TestCase):
    def test_boundary_and_type_checks(self):
        vulnerable = """Handle<JSArray> array = Handle<JSArray>::cast(receiver);
FixedDoubleArray elements = FixedDoubleArray::cast(array->elements());
uint32_t length = static_cast<uint32_t>(array->length()->Number());
return elements.get_scalar(length);
elements.set(length, value->Number());"""
        fixed = """if (!receiver->IsJSArray()) return undefined;
Handle<JSArray> array = Handle<JSArray>::cast(receiver);
if (!array->HasFastDoubleElements()) return undefined;
FixedDoubleArray elements = FixedDoubleArray::cast(array->elements());
uint32_t length = static_cast<uint32_t>(array->length()->Number());
if (length >= static_cast<uint32_t>(elements.length())) return undefined;
if (length >= static_cast<uint32_t>(array->length()->Number())) return undefined;
return elements.get_scalar(length);
elements.set(length, value->Number());"""
        a = analyzer.analyze_builtin(vulnerable, "vulnerable.cc")
        b = analyzer.analyze_builtin(fixed, "fixed.cc")
        self.assertEqual(a["boundary"]["status"], "FAIL")
        self.assertEqual(a["logical_boundary"]["status"], "FAIL")
        self.assertEqual(a["receiver"]["status"], "FAIL")
        self.assertEqual(a["elements_kind"]["status"], "FAIL")
        self.assertEqual(b["boundary"]["status"], "PASS_STATIC")
        self.assertEqual(b["logical_boundary"]["status"], "PASS_STATIC")
        self.assertEqual(b["receiver"]["status"], "PASS_STATIC")
        self.assertEqual(b["elements_kind"]["status"], "PASS_STATIC")

    def test_unknown_is_not_pass(self):
        result = analyzer.analyze_builtin("void unrelated() {}", "empty.cc")
        self.assertEqual(result["boundary"]["status"], "UNKNOWN")

    def test_alternative_index_checks_both_limits(self):
        code = """if (!receiver->IsJSArray()) return undefined;
Handle<JSArray> array = Handle<JSArray>::cast(receiver);
if (!array->HasFastDoubleElements()) return undefined;
FixedDoubleArray elements = FixedDoubleArray::cast(array->elements());
if (index >= logical_length || index >= static_cast<uint32_t>(elements.length())) return undefined;
return elements.get_scalar(index);"""
        self.assertEqual(analyzer.analyze_builtin(code, "alternative.cc")["boundary"]["status"], "PASS_STATIC")
        self.assertEqual(analyzer.analyze_builtin(code, "alternative.cc")["logical_boundary"]["status"], "PASS_STATIC")

    def test_version_and_elf(self):
        self.assertEqual(analyzer.detect_commit('V8_BASE_COMMIT="6dc88c191f5ecc5389dc26efa3ca0907faef3598"'),
                         "6dc88c191f5ecc5389dc26efa3ca0907faef3598")
        self.assertEqual(analyzer.detect_elf_arch(b"\x7fELF\x02\x01" + b"\x00"*12 + b"\x3e\x00"), "x86_64")
        self.assertEqual(analyzer.detect_version("#define V8_MAJOR_VERSION 7\n#define V8_MINOR_VERSION 5\n#define V8_BUILD_NUMBER 0\n#define V8_PATCH_LEVEL 0"), "7.5.0.0")


if __name__ == "__main__":
    unittest.main()
