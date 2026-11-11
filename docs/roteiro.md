# Roteiro do seminário — nove integrantes

**Ponto de partida:** [README.md](../README.md), seção “Comece a apresentação aqui”. As designações Integrante 1 a Integrante 9 identificam a ordem das falas; os nomes pessoais não foram fornecidos. Tempo sugerido: aproximadamente um minuto por fala, com até dois minutos para a demonstração da fala 8, seguido das perguntas.

Mantenham o README, a função e os testes abertos. Executem os comandos na raiz do projeto. Os resultados apresentados pertencem ao modelo C++.

## 1. Integrante 1 — contexto e objetivo de um CTF Pwn

**Fala:** “Nosso objeto de estudo é o desafio oob-v8, também chamado OOB, do StarCTF 2019, creditado aos organizadores Sixstars. Em um CTF, há desafios e objetivos definidos; a categoria Pwn costuma estudar falhas em programas e memória. Nosso objetivo é explicar uma condição de acesso fora dos limites e mostrar como rejeitá-la em um modelo didático. A demonstração será uma função C++17 com cinco testes.”

**Mostrar:** início do [README.md](../README.md) e seção “Contexto: CTF Pwn, V8 e d8”. Apontar o crédito e o link do patch oficial.

## 2. Integrante 2 — V8 e d8

**Fala:** “V8 é um motor de JavaScript e WebAssembly escrito em C++, usado dentro de aplicações como Chrome e Node.js. O d8 é seu shell de desenvolvimento: ele hospeda o motor e permite executar JavaScript e investigá-lo. Shell, aqui, não significa um terminal de comandos do sistema. Delimitamos o caso histórico ao motor e ao processo do d8; nenhum deles será executado na demonstração.”

**Mostrar:** seção de contexto do [README.md](../README.md) e referência oficial [Using d8](https://v8.dev/docs/d8).

## 3. Integrante 3 — regra dos índices

**Fala:** “Para tamanho n, a regra é zero menor ou igual ao índice e índice estritamente menor que n. Em dez, vinte, trinta, há três elementos, nas posições zero, um e dois. A posição três já está fora. Negativos também são inválidos. No vetor vazio, nem zero é válido. Capacidade de memória reservada não cria elementos: o contrato usa o tamanho lógico.”

**Mostrar:** seção “Regra de limites e causa conceitual do OOB” do [README.md](../README.md), com a expressão `0 <= índice < tamanho` e os exemplos.

## 4. Integrante 4 — mapas e elementos

**Fala:** “O Map interno do V8, ou Hidden Class, guarda metadados sobre a estrutura de um objeto. É diferente da coleção Map da linguagem JavaScript. Os elementos indexados têm armazenamento e tratamento distintos das propriedades nomeadas. Esses conceitos ajudam a entender como o motor interpreta seus objetos. A representação física depende da versão e da compilação; não transferimos automaticamente detalhes atuais para o desafio de 2019.”

**Mostrar:** seção “Maps, elementos indexados e contexto histórico” do [README.md](../README.md). Apontar as referências de 2017 e 2020, destacando que a segunda é posterior ao desafio.

## 5. Integrante 5 — causa conceitual do OOB

**Fala:** “A análise do patch oficial mostra uma operação adicionada que escolhe como posição o próprio comprimento do array. Para n elementos, n é o primeiro índice fora do intervalo lógico. O patch também verifica quantidade de argumentos, mas verificar aridade não garante que a posição acessada seja válida. O princípio defensivo é validar o intervalo antes do acesso. Nosso modelo ilustra esse princípio em uma função própria.”

**Mostrar:** parágrafo sobre o patch na seção “Regra de limites e causa conceitual do OOB” do [README.md](../README.md) e o caminho oficial `pwn-OOB/oob.diff` nas referências. A análise é textual; não há comando para executar o patch.

## 6. Integrante 6 — impacto e escopo

**Fala:** “Ler fora do limite pode expor dados ou causar uma falha. Escrever fora dele pode corromper dados e metadados. Um Map é relevante porque orienta a interpretação de um objeto, mas não podemos afirmar que todo acesso fora do limite atinge um Map. O efeito depende da memória naquela execução. Esses impactos são conceituais nesta apresentação; os testes locais não demonstram vazamento, corrupção ou alcance além do processo.”

**Mostrar:** “Consequências conceituais e alcance” e “Escopo da demonstração” no [README.md](../README.md), com as referências CWE-125 e CWE-787.

## 7. Integrante 7 — leitura da função corrigida

**Fala:** “lerElemento recebe um vetor constante por referência e um índice com sinal. A primeira condição rejeita negativos. Depois disso, convertemos para o tipo sem sinal do vetor. A segunda condição rejeita posições maiores ou iguais ao tamanho, inclusive no vetor vazio. Só então usamos o operador de acesso e retornamos o valor. As rejeições lançam std::out_of_range antes da leitura. Esse código ilustra uma correção de limites no modelo; ele não é um patch do V8.”

**Mostrar:** declaração em [src/limites.h](../src/limites.h) e função inteira em [src/limites.cpp](../src/limites.cpp). Percorrer os quatro comentários numerados: rejeição, conversão, limite superior e acesso.

## 8. Integrante 8 — execução dos testes

**Fala:** “Verificamos os dois extremos válidos: zero retorna dez e dois retorna trinta. Os índices três e menos um, além de zero no vetor vazio, precisam lançar especificamente std::out_of_range. Os testes tratam valor diferente, ausência de exceção e tipo incorreto como falha. O executável retorna zero apenas quando todos passam. Vamos compilar e comparar a saída ao registro do README.”

**Mostrar:** cinco chamadas e retorno de `main` em [tests/limites_test.cpp](../tests/limites_test.cpp). Em seguida, executar na raiz:

```bash
mkdir -p build
c++ -std=c++17 -Wall -Wextra -Wpedantic -I src src/limites.cpp tests/limites_test.cpp -o build/testes_limites
./build/testes_limites
```

**Conferir:** cinco linhas `[OK]` e `Resumo: 5/5 testes aprovados.` Comparar cada caso à tabela de “Resultados observados” no [README.md](../README.md). Se a execução divergir, apresentar a divergência em vez de chamá-la de sucesso.

## 9. Integrante 9 — conclusão e perguntas

**Fala:** “O ponto central é validar zero menor ou igual ao índice e índice menor que o tamanho antes de acessar. O modelo retornou os dois valores esperados e rejeitou três entradas inválidas. Essa evidência cobre os cinco casos do nosso código; não prova todas as entradas nem uma correção do motor histórico. O StarCTF forneceu o caso de estudo, e a documentação oficial sustentou os conceitos. Encerramos com perguntas sobre limites, metadados e alcance da demonstração.”

**Mostrar:** tabela, “Escopo da demonstração” e “Referências” no [README.md](../README.md). Abrir as perguntas abaixo.

## Perguntas curtas de banca

| Pergunta | Resposta esperada |
| --- | --- |
| Por que `i == tamanho` é inválido? | Porque os índices vão de `0` a `tamanho - 1`; `tamanho` é a primeira posição após o último elemento. |
| E se o vetor estiver vazio? | Nenhum índice é válido; `0 >= size()` provoca a exceção. |
| Por que rejeitar negativos antes da conversão? | O tipo de tamanho é sem sinal; a conversão não preserva o significado de um índice negativo. |
| O que é um `Map` do V8? | Metadados internos sobre a estrutura de um objeto, também chamados de Hidden Class; é diferente da coleção JavaScript `Map`. |
| Uma posição fora do array sempre contém um `Map`? | Não. O conteúdo depende da versão, das alocações e da disposição da memória. |
| Qual é o alcance de uma falha no `d8`? | A análise se limita ao motor e ao processo que o hospeda. Alcance a outros processos, escape de sandbox ou comprometimento do sistema exigiriam evidências próprias. |
| O que os testes demonstram? | O comportamento da função C++ nos cinco casos: dois valores corretos e três exceções do tipo previsto. |
| Eles provam uma correção do V8? | Não. O motor não foi compilado, executado ou modificado nesta demonstração. |
