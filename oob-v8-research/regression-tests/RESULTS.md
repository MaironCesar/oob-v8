# Protocolo e resultados

## Execução efetuada

| Comando | Evidência | Resultado |
| --- | --- | --- |
| `python3 -m unittest discover -s regression-tests -p 'test_analyzer.py' -v` | `evidence/logs/analyzer-tests.log` | 4 testes, 0 falhas. O teste da variante alternativa foi observado falhar antes da implementação do reconhecimento de `index`. |
| `python3 -m unittest discover -s regression-tests -p 'test_*.py' -v` | `evidence/logs/python-tests.log` | 8 testes, 0 falhas. Inclui modelo controlado de comprimento/capacidade. |
| `./environment/d8-run regression-tests/safe_arrays.js` | `evidence/logs/d8-safe-arrays.log` | `RESULT PASS`; 26 asserções de semântica de arrays normais. |
| `node -e "global.print=console.log; require('./regression-tests/safe_arrays.js')"` | `evidence/logs/node-safe-arrays.log` | `RESULT PASS`; referência contemporânea, não build V8 7.5. |
| `./environment/d8-run --allow-natives-syntax regression-tests/map_and_capacity.js` | `evidence/logs/d8-map-capacity.log` | Mesmo Map antes/depois de leituras e escrita em índice válido; `length` permaneceu 3 e índice 3 retornou `undefined`. |
| `python3 contribution/analyzer.py ...` | `evidence/logs/invariant-report.json` | Original: 4 `FAIL` estáticos; duas propostas: 4 `PASS_STATIC` cada. Dez pontos estruturais encontrados. |

O primeiro teste de `d8-run --version` falhou com código 132 porque os blobs não estavam ao lado da cópia do executável e porque a flag não é reconhecida. Após copiar os dois blobs, `d8-run -e 'print("ok")'` retornou `ok`. Esse erro não é falha de regressão do V8, mas faz parte do registro experimental.

## Cobertura e lacunas

- Índices válidos e inválidos: testados em arrays normais; o builtin vulnerável `oob()` não foi executado.
- Tipos: Smi, double, objeto, vazio e array com lacuna; testes seguros em `d8` e Node.
- `length` e capacity: relação analisada em fonte. O `d8` baixado não expôs capacidade de backing store por interface de teste confiável; o log de runtime mede somente o comprimento lógico.
- Map: `%HaveSameMap` confirma equivalência observável dos dois arrays durante operações seguras. Não prova ausência de corrupção por `oob()` porque essa função não foi chamada.
- Correção: as duas variantes foram avaliadas pelo analisador e não por execução V8. O workspace inicial não continha código-fonte/build corrigido. Compilar V8 histórico completo e um patch alternativo requer toolchain/dependências do V8 7.5 e não foi realizado; por isso não há alegação de regressão dinâmica corrigida.
- Modelo: `boundary_model.py` usa lista Python para mostrar `length == capacity` e capacidade excedente. No primeiro caso, a leitura vulnerável é recusada pelo próprio Python; no segundo, ela retorna um slot fisicamente presente mas logicamente inválido. As duas validações propostas rejeitam ambos. Isto é experimento de lógica de limites, não execução ou simulação fiel do heap V8.

Um teste de mutação controlada do analisador troca guarda ausente por guarda presente e verifica `FAIL` → `PASS_STATIC`; ele avalia a detecção textual, não a segurança real do binário.
