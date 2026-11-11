# oob-v8 — análise defensiva para seminário

**Disciplina:** Segurança Cibernética. **Equipe:** nove integrantes, com falas distribuídas em [docs/roteiro.md](docs/roteiro.md). **Objeto de estudo:** o desafio histórico **oob-v8 / OOB do StarCTF 2019 (\*CTF 2019)**, categoria Pwn, creditado aos organizadores Sixstars.

O objetivo é explicar a falha conceitual de acesso fora dos limites e uma validação que a evita em um modelo didático. A análise documental considera o [patch oficial `pwn-OOB/oob.diff`](https://github.com/sixstars/starctf2019/blob/master/pwn-OOB/oob.diff); a evidência executável deste repositório vem exclusivamente da função C++ e dos cinco testes locais.

## Comece a apresentação aqui

1. Apresente o objetivo acima e siga as seções de contexto, limites e impacto deste README.
2. Abra o [roteiro das nove falas](docs/roteiro.md), que indica o trecho ou comando para cada integrante.
3. Mostre [src/limites.h](src/limites.h) e [src/limites.cpp](src/limites.cpp), destacando a ordem das verificações.
4. Execute os comandos de [Compilação e execução](#compilação-e-execução) e compare a saída com a tabela de [Resultados observados](#resultados-observados).
5. Encerre com o escopo da demonstração e as perguntas de banca do roteiro.

## Contexto: CTF Pwn, V8 e d8

Um CTF é uma competição com desafios e objetivos definidos. Na categoria Pwn, o estudo costuma envolver falhas em programas e seus efeitos sobre memória e execução. Neste seminário, o foco é identificar a condição insegura e explicar sua prevenção.

O **V8** é um motor de JavaScript e WebAssembly, de código aberto e escrito em C++, usado, por exemplo, no Chrome e no Node.js. Um motor implementa a execução dessas linguagens dentro de uma aplicação hospedeira. Veja a [apresentação oficial do V8](https://v8.dev/).

O **`d8`** é o shell de desenvolvimento do V8, que permite executar JavaScript e investigar o motor. Ele é uma aplicação que hospeda o V8 e oferece funções próprias. Seu nome “shell” não significa que seja um interpretador de comandos do sistema operacional. A documentação [Using d8](https://v8.dev/docs/d8) descreve seu uso.

O caso estudado é uma versão histórica do motor modificada para o desafio. A análise é delimitada ao V8 e ao processo do shell `d8`. Um problema nesse processo não demonstra, por si só, acesso a outros processos, escape de sandbox de navegador ou comprometimento do sistema operacional.

## Maps, elementos indexados e contexto histórico

Um **`Map` interno**, também chamado de Hidden Class, reúne metadados sobre a estrutura de um objeto. Esses metadados permitem ao motor reconhecer formatos e orientar acessos e otimizações. Esse `Map` interno é diferente da coleção JavaScript `Map` usada por programas. A documentação [Maps (Hidden Classes) in V8](https://v8.dev/docs/hidden-classes) explica essa estrutura.

Propriedades nomeadas e elementos indexados têm armazenamento e tratamento distintos no motor. Os elementos representam propriedades acessadas por índices de array; seu armazenamento pode ter representações diferentes, inclusive densas ou em dicionário. O formato dos elementos também faz parte das informações usadas para interpretar os objetos. `Map` e armazenamento de elementos têm papéis distintos, como explica [Fast properties in V8](https://v8.dev/blog/fast-properties), publicado em 2017.

Essas descrições ajudam a entender o desafio de 2019, mas os detalhes físicos dependem de versão, arquitetura e configuração. O artigo [Pointer Compression in V8](https://v8.dev/blog/pointer-compression), publicado em março de 2020, documenta mudanças na representação de valores e referências. Por ser posterior ao desafio, ele serve de contexto sobre a evolução do motor. Não se assume que layouts, tamanhos de ponteiros, posições de campos ou proteções atuais sejam iguais aos da versão histórica. O vetor C++ deste projeto não reproduz os `Map`s ou o heap do V8.

## Regra de limites e causa conceitual do OOB

Para uma sequência com `tamanho` elementos, a condição de acesso é:

```text
0 <= índice < tamanho
```

No vetor `{10, 20, 30}`, de tamanho `3`, os índices válidos são `0`, `1` e `2`. O índice `3` é a primeira posição após o último elemento. Um índice negativo está antes do começo. Um vetor vazio não tem índice válido, nem mesmo `0`. O tamanho lógico é a referência para esse contrato; eventual capacidade reservada não cria elementos adicionais válidos.

No [patch oficial](https://github.com/sixstars/starctf2019/blob/master/pwn-OOB/oob.diff), o builtin adicionado obtém o comprimento do array em `length` e usa esse valor para selecionar a posição na leitura ou na escrita internas. Isso seleciona `índice == tamanho`, fora do intervalo lógico. A variável `len` verifica quantidade de argumentos; esse teste de aridade não valida o limite do acesso. Essa é a condição conceitual analisada. Quais dados físicos seriam atingidos depende da organização da memória naquela execução.

Em termos de prevenção, o acesso só deve ocorrer após a validação dos dois limites. Aceitar `índice <= tamanho`, esquecer o limite inferior ou converter um negativo para um tipo sem sinal antes de verificá-lo compromete essa lógica. No modelo entregue, a correção é ilustrada pela rejeição antecipada de índices inválidos.

## Consequências conceituais e alcance

Uma **leitura fora dos limites** pode expor dados que não pertencem à sequência ou causar uma falha do processo, conforme a classe [CWE-125](https://cwe.mitre.org/data/definitions/125.html). Uma **escrita fora dos limites** pode alterar dados ou metadados de memória e provocar corrupção, comportamento inesperado ou encerramento do processo, conforme [CWE-787](https://cwe.mitre.org/data/definitions/787.html).

Metadados como os `Map`s são relevantes porque orientam a interpretação dos objetos pelo motor; sua corrupção pode invalidar essas interpretações. Não há garantia de que toda posição fora de um array contenha um `Map`. As consequências dependem do código e da disposição da memória. A demonstração deste projeto realiza somente leituras validadas e rejeições por exceção; vazamento e corrupção são discutidos conceitualmente.

## Proposta de correção no modelo C++17

A função [lerElemento](src/limites.cpp) recebe `const std::vector<int>&` e um índice do tipo `std::vector<int>::difference_type`, um inteiro com sinal. Ela devolve o valor por cópia e usa apenas a biblioteca padrão.

O trecho central, na mesma ordem do código, é:

```cpp
if (indice < 0) {
    throw std::out_of_range("Indice negativo");
}

const auto posicao = static_cast<std::vector<int>::size_type>(indice);

if (posicao >= elementos.size()) {
    throw std::out_of_range("Indice maior ou igual ao tamanho");
}

return elementos[posicao];
```

Primeiro se rejeita o negativo; só então se converte para o tipo sem sinal do tamanho do vetor. A segunda verificação exige que a posição seja estritamente menor que `size()`, inclusive para o vetor vazio. O operador `[]` de `std::vector` não faz essa checagem por conta própria: neste código, seu uso fica condicionado às duas verificações anteriores. As duas rejeições lançam `std::out_of_range` antes do acesso.

Essa é uma ilustração de validação de limites em uma função própria. Uma correção real do motor precisaria respeitar as representações e os contratos do V8 e passar pelos testes específicos daquela versão.

## Arquivos

| Arquivo | Papel no seminário |
| --- | --- |
| `README.md` | Contexto, análise, reprodução e resultados |
| `src/limites.h` | Declaração e contrato de `lerElemento` |
| `src/limites.cpp` | Verificação inferior, conversão, verificação superior e leitura |
| `tests/limites_test.cpp` | Cinco casos e código de saída do executor de testes |
| `docs/roteiro.md` | Nove falas e perguntas de banca |
| `.gitignore` | Exclui `/build/` do versionamento |

## Compilação e execução

**Pré-requisitos:** terminal com shell compatível com os comandos abaixo e um compilador C++ com suporte a C++17 e à biblioteca padrão. Nenhuma biblioteca externa ou instalação do V8 é necessária.

Depois de obter o repositório, entre na sua raiz, onde estão `README.md`, `src/` e `tests/`, e execute:

```bash
mkdir -p build
c++ -std=c++17 -Wall -Wextra -Wpedantic -I src src/limites.cpp tests/limites_test.cpp -o build/testes_limites
./build/testes_limites
```

O programa imprime cada caso e retorna `0` se todos passarem. Se algum valor divergir, faltar a exceção esperada ou surgir outro tipo de exceção, registra `[FALHA]` e termina com código diferente de zero. As verificações não dependem de `assert`.

## Resultados observados

Execução realizada em **11 de novembro de 2026**, em **Linux x86_64**, com **`c++ (Debian 14.2.0-19) 14.2.0`**, usando os comandos acima. A criação da pasta e a compilação terminaram sem mensagens; o compilador não emitiu avisos. A execução dos testes terminou com código de saída **`0`** e produziu exatamente:

```text
[OK] Primeiro índice válido: esperado 10, observado 10.
[OK] Último índice válido: esperado 30, observado 30.
[OK] Índice igual ao tamanho (3): std::out_of_range.
[OK] Índice negativo (-1): std::out_of_range.
[OK] Vetor vazio (índice 0): std::out_of_range.
Resumo: 5/5 testes aprovados.
```

| Caso | Vetor | Índice | Resultado esperado | Resultado observado |
| --- | --- | ---: | --- | --- |
| Primeiro válido | `{10, 20, 30}` | `0` | `10` | `10` — passou |
| Último válido | `{10, 20, 30}` | `2` | `30` | `30` — passou |
| Igual ao tamanho | `{10, 20, 30}` | `3` | `std::out_of_range` | Exceção do tipo esperado — passou |
| Negativo | `{10, 20, 30}` | `-1` | `std::out_of_range` | Exceção do tipo esperado — passou |
| Vetor vazio | `{}` | `0` | `std::out_of_range` | Exceção do tipo esperado — passou |

## Escopo da demonstração

Os resultados são evidência do comportamento de **`lerElemento` nos cinco casos testados**: dois valores corretos e três rejeições com o tipo de exceção previsto. Eles não constituem prova exaustiva para todas as entradas, nem validação de uma correção do V8.

O trabalho executável fica restrito ao modelo C++17 e aos testes do seminário. Não foi compilado ou executado um motor vulnerável, o shell `d8` ou um exploit. Não se demonstram acesso a memória arbitrária, vazamento, corrupção, execução de código ou escape de sandbox. O desafio original é a fonte histórica da análise; o experimento local demonstra a checagem de limites no modelo.

## Referências

Fontes consultadas em 11 de novembro de 2026. Os conceitos são apresentados em português, em redação própria.

- **Sixstars / StarCTF 2019:** [repositório oficial](https://github.com/sixstars/starctf2019) e [patch do desafio OOB](https://github.com/sixstars/starctf2019/blob/master/pwn-OOB/oob.diff). Arquivo analisado: `pwn-OOB/oob.diff`, blob Git `f277a8a79f612622c6cfa45bd362dd68fb2078d1`.
- **V8:** [What is V8?](https://v8.dev/) — papel do motor.
- **V8:** [Using d8](https://v8.dev/docs/d8) — shell de desenvolvimento.
- **V8:** [Fast properties in V8](https://v8.dev/blog/fast-properties) — propriedades e elementos, publicado em 2017.
- **V8:** [Maps (Hidden Classes) in V8](https://v8.dev/docs/hidden-classes) — metadados de estrutura de objetos.
- **V8:** [Pointer Compression in V8](https://v8.dev/blog/pointer-compression) — evolução de representações de memória, publicado em 2020.
- **MITRE:** [CWE-125: Out-of-bounds Read](https://cwe.mitre.org/data/definitions/125.html) — consequências de leitura fora dos limites.
- **MITRE:** [CWE-787: Out-of-bounds Write](https://cwe.mitre.org/data/definitions/787.html) — consequências de escrita fora dos limites.
