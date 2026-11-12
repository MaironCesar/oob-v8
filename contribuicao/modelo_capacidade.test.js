const test = require('node:test');
const assert = require('node:assert/strict');
const { classificarAcesso, construirCenarios } = require('./modelo_capacidade');

test('comprimento igual à capacidade alcança o primeiro índice após o armazenamento', () => {
  assert.deepEqual(classificarAcesso(3, 3), {
    indice: 3,
    foraDoComprimento: true,
    foraDaCapacidade: true,
    classificacao: 'fora do armazenamento',
  });
});

test('capacidade excedente mantém o índice no armazenamento, mas fora do comprimento', () => {
  assert.deepEqual(classificarAcesso(3, 8), {
    indice: 3,
    foraDoComprimento: true,
    foraDaCapacidade: false,
    classificacao: 'dentro da capacidade excedente',
  });
});

test('o caso vazio também acessa o primeiro índice fora do armazenamento', () => {
  assert.equal(classificarAcesso(0, 0).classificacao, 'fora do armazenamento');
});

test('rejeita capacidade menor que o comprimento e valores não inteiros', () => {
  assert.throws(() => classificarAcesso(4, 3), RangeError);
  assert.throws(() => classificarAcesso(1.5, 3), TypeError);
  assert.throws(() => classificarAcesso(-1, 3), RangeError);
});

test('cenários padrão incluem ambas as situações de memória', () => {
  assert.deepEqual(construirCenarios().map(c => c.classificacao), [
    'fora do armazenamento',
    'dentro da capacidade excedente',
  ]);
});
