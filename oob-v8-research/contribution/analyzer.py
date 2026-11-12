#!/usr/bin/env python3
"""Auditoria estática conservadora do builtin ArrayOob histórico."""
import argparse
import hashlib
import json
import pathlib
import re
import struct


def detect_commit(text):
    match = re.search(r'V8_BASE_COMMIT=["\']?([0-9a-f]{40})', text)
    return match.group(1) if match else None


def detect_version(text):
    values = []
    for key in ("MAJOR_VERSION", "MINOR_VERSION", "BUILD_NUMBER", "PATCH_LEVEL"):
        match = re.search(r'^#define V8_' + key + r'\s+(\d+)', text, re.M)
        if not match: return None
        values.append(match.group(1))
    return ".".join(values)


def detect_elf_arch(data):
    if len(data) < 20 or data[:4] != b"\x7fELF":
        return None
    endian = "<" if data[5] == 1 else ">" if data[5] == 2 else None
    if endian is None:
        return None
    machine = struct.unpack(endian + "H", data[18:20])[0]
    return {3: "x86", 62: "x86_64", 183: "aarch64"}.get(machine, f"ELF-machine-{machine}")


def item(prop, source, method, expected, observed, evidence, status):
    return dict(property=prop, source=source, method=method, expected=expected,
                observed=observed, evidence=evidence, status=status,
                conclusion={"FAIL": "Invariante não demonstrado no fluxo analisado",
                            "PASS_STATIC": "Guarda observada estaticamente; runtime não verificado",
                            "UNKNOWN": "Evidência insuficiente"}[status])


def analyze_builtin(source, path):
    lines = source.splitlines()
    accesses = [(i, line, match.group(1)) for i, line in enumerate(lines, 1)
                if (match := re.search(r'elements\.(?:get_scalar|set)\s*\(\s*(length|index)\b', line))]
    cast_receiver = next((i for i, line in enumerate(lines, 1) if 'Handle<JSArray>::cast(receiver)' in line), None)
    cast_elements = next((i for i, line in enumerate(lines, 1) if 'FixedDoubleArray::cast(array->elements())' in line), None)
    receiver_guard = next((i for i, line in enumerate(lines, 1) if re.search(r'!\s*receiver->IsJSArray\s*\(', line)), None)
    kind_guard = next((i for i, line in enumerate(lines, 1) if re.search(r'!\s*array->HasFastDoubleElements\s*\(', line)), None)
    def bound_guard_for(variable, target):
        return next((i for i, line in enumerate(lines, 1) if i < target and
                     re.search(r'\b' + variable + r'\s*>=\s*(?:static_cast<[^>]+>\s*\()?\s*elements\.length\s*\(', line)), None)
    def logical_guard_for(variable, target):
        pattern = (r'\blength\s*>=\s*(?:static_cast<[^>]+>\s*\()?\s*array->length\s*\('
                   if variable == "length" else r'\bindex\s*>=\s*logical_length\b')
        return next((i for i, line in enumerate(lines, 1) if i < target and re.search(pattern, line)), None)
    def classification(guard, target):
        if target is None: return "UNKNOWN"
        return "PASS_STATIC" if guard is not None and guard < target else "FAIL"
    first_access = accesses[0][0] if accesses else None
    guarded = bool(accesses) and all(bound_guard_for(var, i) is not None for i, _, var in accesses)
    logical_guarded = bool(accesses) and all(logical_guard_for(var, i) is not None for i, _, var in accesses)
    boundary_status = "UNKNOWN" if not accesses else "PASS_STATIC" if guarded else "FAIL"
    return {
        "boundary": item("index < backing length", path, "busca textual de guarda anterior a cada get_scalar/set", "guarda antes de cada acesso", "presente" if guarded else "ausente", [f"{i}: {v.strip()}" for i, v, _ in accesses], boundary_status),
        "logical_boundary": item("index < JSArray.length", path, "busca textual de guarda lógica anterior a cada acesso", "índice abaixo do comprimento lógico", "presente" if logical_guarded else "ausente", [f"{i}: {v.strip()}" for i, v, _ in accesses], "UNKNOWN" if not accesses else "PASS_STATIC" if logical_guarded else "FAIL"),
        "receiver": item("receiver é JSArray", path, "guarda antes do cast", "verificação de tipo antes do cast", "guarda em linha " + str(receiver_guard) if receiver_guard else "ausente", [f"{cast_receiver}: {lines[cast_receiver-1].strip()}"] if cast_receiver else [], classification(receiver_guard, cast_receiver)),
        "elements_kind": item("backing store é FixedDoubleArray", path, "guarda antes do cast", "Elements Kind double antes do cast", "guarda em linha " + str(kind_guard) if kind_guard else "ausente", [f"{cast_elements}: {lines[cast_elements-1].strip()}"] if cast_elements else [], classification(kind_guard, cast_elements)),
    }


def extract_added_builtin(diff):
    section = diff.split("diff --git a/src/builtins/builtins-array.cc", 1)[-1].split("diff --git", 1)[0]
    return "\n".join(line[1:] for line in section.splitlines() if line.startswith("+") and not line.startswith("+++"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


SOURCE_CHECKS = [
    ("JSArray length <= backing length", "src/objects/js-array.h", r'length <= elements\.length\(\)', "invariante documentado para modo rápido"),
    ("JSArray length", "src/objects/js-array.h", r'DECL_ACCESSORS\(length, Object\)', "length separado do armazenamento"),
    ("FixedArrayBase storage length", "src/objects/fixed-array.h", r'class FixedArrayBase : public HeapObject', "backing store com comprimento próprio"),
    ("FixedDoubleArray double slots", "src/objects/fixed-array.h", r'kHeaderSize \+ length \* kDoubleSize', "tamanho em slots double"),
    ("FixedDoubleArray debug assertion", "src/objects/fixed-array-inl.h", r'DCHECK\(index >= 0 && index < this->length\(\)\)', "DCHECK de limite na leitura"),
    ("FixedDoubleArray write path", "src/objects/fixed-array-inl.h", r'void FixedDoubleArray::set\(int index, double value\)', "setter separado da validação do chamador"),
    ("Map field", "src/objects/heap-object.h", r'V\(kMapOffset, kTaggedSize\)', "ponteiro Map no cabeçalho"),
    ("Map ElementsKind bits", "src/objects/map.h", r'V\(ElementsKindBits, ElementsKind, 5, _\)', "ElementsKind codificado em Map"),
    ("double ElementsKind", "src/elements-kind.h", r'PACKED_DOUBLE_ELEMENTS,', "ElementsKind double declarado"),
    ("JSObject elements field", "src/objects/js-objects.h", r'V\(kElementsOffset, kTaggedSize\)', "ponteiro para armazenamento de elementos"),
]


def audit_sources(root):
    findings = []
    for property_name, rel, pattern, expected in SOURCE_CHECKS:
        path = root / rel
        if not path.is_file():
            findings.append(item(property_name, str(path), "regex literal no código-fonte", expected, "arquivo ausente", [], "UNKNOWN"))
            continue
        matches = [(i, line.strip()) for i, line in enumerate(path.read_text().splitlines(), 1) if re.search(pattern, line)]
        finding = item(property_name, str(path), "regex no código-fonte versionado", expected,
                       "declaração encontrada" if matches else "declaração não encontrada",
                       [f"{i}: {line}" for i, line in matches[:3]], "PASS_STATIC" if matches else "UNKNOWN")
        if matches: finding["conclusion"] = "Declaração encontrada no commit; sem inferência de segurança dinâmica"
        findings.append(finding)
    return findings


def metadata_finding(prop, source, method, expected, observed, evidence):
    return dict(property=prop, source=str(source) if source else None, method=method,
                expected=expected, observed=observed, evidence=evidence,
                status="OBSERVED" if observed is not None else "UNKNOWN",
                conclusion="Identificação atribuída à fonte indicada" if observed is not None else "Não identificado")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff", type=pathlib.Path, required=True)
    parser.add_argument("--build-script", type=pathlib.Path)
    parser.add_argument("--binary", type=pathlib.Path)
    parser.add_argument("--corrected", type=pathlib.Path)
    parser.add_argument("--alternative", type=pathlib.Path)
    parser.add_argument("--source-root", type=pathlib.Path)
    parser.add_argument("--version-header", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    inputs = {"diff": args.diff}
    if args.build_script: inputs["build_script"] = args.build_script
    if args.binary: inputs["binary"] = args.binary
    if args.corrected: inputs["corrected"] = args.corrected
    if args.alternative: inputs["alternative"] = args.alternative
    if args.version_header: inputs["version_header"] = args.version_header
    if args.source_root:
        for _, rel, _, _ in SOURCE_CHECKS:
            path = args.source_root / rel
            if path.is_file(): inputs[rel] = path
    cases = {"original_vulnerable": analyze_builtin(extract_added_builtin(args.diff.read_text()), str(args.diff))}
    for name, path in (("corrected_proposal", args.corrected), ("alternative_proposal", args.alternative)):
        if path: cases[name] = analyze_builtin(path.read_text(), str(path))
    version = detect_version(args.version_header.read_text()) if args.version_header else None
    commit = detect_commit(args.build_script.read_text()) if args.build_script else None
    arch = detect_elf_arch(args.binary.read_bytes()[:20]) if args.binary else None
    changed = re.findall(r'^diff --git a/(\S+) b/', args.diff.read_text(), re.M)
    report = {"schema": 1, "method": "static textual checks; not a proof of control flow or memory safety",
              "version": version, "commit": commit, "architecture": arch,
              "inputs_sha256": {name: sha256(path) for name, path in inputs.items()}, "cases": cases,
              "source_findings": audit_sources(args.source_root) if args.source_root else [],
              "changed_paths": changed,
              "metadata_findings": [
                  metadata_finding("V8 version", args.version_header, "parse V8_* macros", "four numeric components", version, ["V8_MAJOR_VERSION", "V8_MINOR_VERSION", "V8_BUILD_NUMBER", "V8_PATCH_LEVEL"] if version else []),
                  metadata_finding("V8 base commit", args.build_script, "parse V8_BASE_COMMIT", "40 hex characters", commit, ["V8_BASE_COMMIT"] if commit else []),
                  metadata_finding("binary architecture", args.binary, "parse ELF e_machine", "known architecture or ELF machine", arch, ["ELF header bytes 0..19"] if arch else []),
                  metadata_finding("modified source paths", args.diff, "parse diff --git headers", "list of changed paths", changed, changed),
              ]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "statuses": {k: {p: r["status"] for p, r in v.items()} for k, v in cases.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
