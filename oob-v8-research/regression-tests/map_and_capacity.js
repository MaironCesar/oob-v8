// Executar somente em d8 com --allow-natives-syntax. Sem chamada a oob().
var a = [1.1, 2.2, 3.3];
var peer = [4.4, 5.5, 6.6];
var before = %HaveSameMap(a, peer);
var logicalBefore = a.length;
var beyond = a[a.length];
a[1] = 7.7;
var after = %HaveSameMap(a, peer);
print('same_map_before=' + before);
print('same_map_after=' + after);
print('logical_length_before=' + logicalBefore);
print('logical_length_after=' + a.length);
print('first_invalid_undefined=' + (beyond === undefined));
if (!before || !after || logicalBefore !== a.length || beyond !== undefined) {
  throw new Error('safe invariant regression');
}
// O DebugPrint documenta backing-store length e ElementsKind observados.
%DebugPrint(a);
print('RESULT PASS');
