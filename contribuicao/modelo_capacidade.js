// Modelo didático do índice usado em ArrayOob; não acessa a memória do V8.
function classificarAcesso(comprimento, capacidade) {
  for (const [nome, valor] of [['comprimento', comprimento], ['capacidade', capacidade]]) {
    if (!Number.isSafeInteger(valor)) {
      throw new TypeError(`${nome} deve ser um inteiro seguro`);
    }
    if (valor < 0) {
      throw new RangeError(`${nome} não pode ser negativo`);
    }
  }
  if (capacidade < comprimento) {
    throw new RangeError('a capacidade não pode ser menor que o comprimento');
  }

  const indice = comprimento; // elements.get_scalar(length) / elements.set(length, ...)
  const foraDoComprimento = indice >= comprimento;
  const foraDaCapacidade = indice >= capacidade;
  return {
    indice,
    foraDoComprimento,
    foraDaCapacidade,
    classificacao: foraDaCapacidade
      ? 'fora do armazenamento'
      : 'dentro da capacidade excedente',
  };
}

function construirCenarios() {
  return [
    { comprimento: 3, capacidade: 3 },
    { comprimento: 3, capacidade: 8 },
  ].map(cenario => ({
    ...cenario,
    ...classificarAcesso(cenario.comprimento, cenario.capacidade),
  }));
}

if (require.main === module) {
  console.log('Comprimento | Capacidade | Índice acessado | Resultado');
  for (const cenario of construirCenarios()) {
    console.log(`${cenario.comprimento}           | ${cenario.capacidade}          | ${cenario.indice}              | ${cenario.classificacao}`);
  }
}

module.exports = { classificarAcesso, construirCenarios };
