# OOB-V8 (*CTF 2019): pesquisa defensiva

Projeto reproduzível de auditoria estática e regressão segura. O checkout original na raiz foi preservado. Arquivos de terceiros estão em `evidence/origins/`; código e documentos próprios ficam nas demais pastas.

## Executar

```bash
cd oob-v8-research
python3 -m unittest discover -s regression-tests -p 'test_*.py' -v
python3 contribution/analyzer.py --diff evidence/origins/oob.diff \
  --build-script evidence/origins/build.sh --binary evidence/origins/d8 \
  --version-header evidence/origins/v8-version.h \
  --source-root evidence/origins/v8 \
  --corrected source-analysis/corrected_proposal.cc \
  --alternative source-analysis/alternative_proposal.cc \
  --output evidence/logs/invariant-report.json
./environment/d8-run regression-tests/safe_arrays.js
./environment/d8-run --allow-natives-syntax regression-tests/map_and_capacity.js
```

`d8-run` é cópia executável do binário de origem; os blobs correspondentes ficam em `environment/`. O teste normal pode também rodar em Node com `node -e "global.print=console.log; require('./regression-tests/safe_arrays.js')"`.

## Leitura

- [Inventário e proveniência](environment/INVENTORY.md)
- [Análise de código-fonte](source-analysis/ANALYSIS.md)
- [Método da ferramenta](contribution/README.md)
- [Protocolo e resultados dos testes](regression-tests/RESULTS.md)
- [Writeup completo](writeup/WRITEUP.md)

O relatório JSON distingue observação estática (`PASS_STATIC`), ausência de guarda (`FAIL`) e evidência insuficiente (`UNKNOWN`). Os arquivos `corrected_proposal.cc` e `alternative_proposal.cc` são propostas documentais; não são builds compilados. Não há validação dinâmica de uma correção nativa neste projeto.
