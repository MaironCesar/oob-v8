# Fluffy — Google CTF 2025

Material de estudo do desafio de engenharia reversa **Fluffy**, com a resolução publicada no repositório Google CTF e uma implementação adicional para demonstrar uma otimização da busca.

## Origem e licença

- Fonte: [google/google-ctf — 2025/quals/rev-fluffy](https://github.com/google/google-ctf/tree/1655538e8c8b41451d39f670ef15a5af22979ca9/2025/quals/rev-fluffy).
- Versão copiada: `1655538e8c8b41451d39f670ef15a5af22979ca9`.
- Licença do material original: [Apache License 2.0](LICENSE).
- Os arquivos originais foram preservados sem alterações, incluindo os avisos de autoria. O README desta página e a pasta `contrib/` são acréscimos deste repositório, também disponibilizados sob Apache 2.0.

A resolução existente é atribuída aos autores do projeto Google CTF. A contribuição adicional aproveita as regras da cifra e a periodicidade descritas nessa resolução; os detalhes da implementação nova estão documentados em [contrib/README.md](contrib/README.md).

## Conteúdo

| Caminho | Conteúdo |
| --- | --- |
| [solution/README.md](solution/README.md) | Resolução original completa, em inglês, com imagens e exemplos. |
| [solution/crack.py](solution/crack.py) | Script original de recuperação dos segredos. |
| [attachments/fluffy.apk](attachments/fluffy.apk) | Aplicativo Android distribuído no desafio. |
| [src/](src/) | Código-fonte publicado do aplicativo Flutter/Dart. |
| [metadata.yaml](metadata.yaml) | Descrição e metadados publicados do desafio. |
| [contrib/README.md](contrib/README.md) | Explicação em português, justificativa da otimização e roteiro de apresentação. |
| [contrib/solve_fast.py](contrib/solve_fast.py) | Novo solucionador por composição de permutações de bytes. |
| [contrib/test_solve_fast.py](contrib/test_solve_fast.py) | Testes de compatibilidade com o código original. |
| [contrib/benchmark.py](contrib/benchmark.py) | Comparação reproduzível dos dois métodos. |

## Demonstração

Na pasta raiz do repositório, com Python 3.9 ou superior e a base de fusos horários disponível:

```bash
python3 contrib/solve_fast.py --all
python3 -m unittest discover -s contrib -p 'test_*.py' -v
python3 contrib/benchmark.py
```

O solucionador usa a biblioteca padrão do Python. Ele recebe as datas e os textos cifrados publicados, procura os segundos e os PINs e confirma cada resultado cifrando a mensagem recuperada novamente. Não depende de instalar o APK nem de ler a flag em `metadata.yaml`.

Os resultados de uma execução estão em [contrib/resultado.json](contrib/resultado.json), e a medição comparativa está em [contrib/benchmark.json](contrib/benchmark.json). Os tempos variam conforme a máquina.
