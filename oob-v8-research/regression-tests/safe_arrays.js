(function () {
  var cases = [
    {name: 'smi', value: [1, 2, 3], expected: 3},
    {name: 'double', value: [1.1, 2.2, 3.3], expected: 3.3},
    {name: 'object', value: [{x: 1}, {x: 2}], expected: null},
    {name: 'empty', value: [], expected: null},
    {name: 'holey', value: [1, , 3], expected: 3}
  ];
  var failed = 0;
  function check(name, actual, expected) {
    if (actual !== expected) { print('FAIL ' + name + ' got=' + actual); failed++; }
    else print('PASS ' + name);
  }
  cases.forEach(function (c) {
    var a = c.value;
    var n = a.length;
    check(c.name + ': length stable', a.length, n);
    check(c.name + ': first invalid', a[n], undefined);
    check(c.name + ': negative index', a[-1], undefined);
    if (n) check(c.name + ': last valid', c.name === 'object' ? a[n - 1].x : a[n - 1],
                 c.name === 'object' ? 2 : c.expected);
    if (c.name === 'holey') check('hole retained', 1 in a, false);
    if (c.name === 'object') check('object retained', a[0].x, 1);
    check(c.name + ': length after reads', a.length, n);
  });
  if (failed) throw new Error(failed + ' assertions failed');
  print('RESULT PASS');
})();
