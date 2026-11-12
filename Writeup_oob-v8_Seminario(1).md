# oob-v8 no StarCTF 2019

**Write-up e roteiro de seminário · 9 integrantes · 30 minutos**

O desafio `oob-v8` parte de uma alteração deliberada em uma versão do V8. Uma operação do motor consegue acessar a primeira posição além da região prevista para os elementos de um array. A resolução reunida pelo Browser Dojo usa esse caso para explicar como uma violação de limites pode comprometer dados internos do motor e, no ambiente do desafio, afetar o fluxo de execução. [Browser Dojo, capítulo oob-v8](https://github.com/jackfromeast/browser-dojo/tree/main/v8/2019-star-ctf-oob-v8)

## Origem e créditos

- **Desafio.** `oob-v8`, do StarCTF 2019. O capítulo identifica o artefato como uma versão modificada do V8 7.5.0. [Capítulo do desafio](https://github.com/jackfromeast/browser-dojo/tree/main/v8/2019-star-ctf-oob-v8)
- **Resolução de referência.** O projeto Browser Dojo, publicado na conta GitHub `jackfromeast`, reúne o material e a análise técnica usados neste seminário. [Repositório Browser Dojo](https://github.com/jackfromeast/browser-dojo)
- **Relato anterior.** O README cita Faraz, autor de *Exploiting v8 — StarCTF 2019 oob-v8*, como referência para o caso. [Atribuição no capítulo](https://github.com/jackfromeast/browser-dojo/tree/main/v8/2019-star-ctf-oob-v8)
- **Material do seminário.** A explicação em português, o quadro de limites e o exemplo defensivo de validação foram preparados para a apresentação. A análise do resultado do CTF tem como evidência o relato publicado.

**Crédito para o primeiro slide**

> Estudo da resolução de oob-v8 do StarCTF 2019, reunida pelo projeto Browser Dojo (jackfromeast). O capítulo cita o relato de Faraz como referência.

## O que aproveitar do repositório

| Material de origem | Uso na apresentação |
| --- | --- |
| Identificação do desafio no README | Apresentar o nome, a edição do CTF, a versão histórica do V8 e o caráter intencional da alteração. |
| Explicação da vulnerabilidade no README | Mostrar a diferença entre o último índice válido e a primeira posição fora do limite. Usar o quadro da seção 2. |
| Análise de representação, confusão de tipos e fluxo de controle | Explicar o que torna relevante uma violação de apenas uma posição e qual impacto é descrito na resolução. Usar as seções 3 e 4. |
| Executável do desafio e anexos listados na pasta | Identificar o artefato específico do laboratório ao delimitar o alcance do resultado publicado. |

[Material original do Browser Dojo](https://github.com/jackfromeast/browser-dojo/tree/main/v8/2019-star-ctf-oob-v8)

## 1. Onde entra o V8

O **V8** é um motor que executa JavaScript e WebAssembly. Ele é implementado em C++ e integra projetos como Chrome e Node.js. Quando o programa manipula um array em JavaScript, o motor mantém uma representação interna dos elementos e implementa as operações que o programa pode realizar. [Documentação do V8](https://v8.dev/)

Uma operação de leitura tem significado na linguagem. O acesso nativo à memória usado para implementar essa operação precisa respeitar os limites da região de armazenamento. Essa diferença entre o comportamento visível em JavaScript e o trabalho interno do motor é o ponto de partida do desafio.

## 2. Qual é a falha do desafio

Em um vetor denso com três elementos, a contagem começa em zero. O comprimento é `3`, o último índice válido é `2` e o primeiro índice fora da faixa é `3`.

| Posição solicitada | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- |
| Valor no vetor didático | 10 | 20 | 30 | Fora da faixa |
| Acesso a elemento existente | Válido | Válido | Válido | Inválido |

Para acessar um elemento de um vetor denso de comprimento `n`, o índice deve ser inteiro e satisfazer `0 ≤ índice < n`. Se `n = 0`, a faixa válida é vazia. Com o teste `índice ≤ n`, a função aceitaria uma posição a mais no limite superior. Esse é um exemplo de erro de uma unidade, chamado **off-by-one**. O quadro representa apenas a faixa de índices do vetor didático.

No CTF, o problema ocorre no acesso interno do motor. A alteração descrita no README permite operar em uma posição além da área pretendida para os elementos. Esse tipo de violação é chamado **out-of-bounds**, ou **OOB**. O acesso normal de JavaScript obedece à semântica da linguagem. Por exemplo, acrescentar um elemento a um array comum pode aumentar seu comprimento de forma definida. A alteração do desafio toca a região de memória além do limite da operação. [Browser Dojo, capítulo oob-v8](https://github.com/jackfromeast/browser-dojo/tree/main/v8/2019-star-ctf-oob-v8) · [MDN, Array.length](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/length)

## 3. Por que uma posição pode importar

O efeito depende do tipo de operação e dos dados que ocupam a região acessada. Uma posição de um vetor corresponde a um elemento, cujo tamanho em bytes depende da representação usada.

| Operação fora dos limites | O que pode acontecer | Propriedade afetada |
| --- | --- | --- |
| Leitura | Dados de outra região podem ficar visíveis ao código que fez a leitura. | Confidencialidade |
| Escrita | Dados internos podem ser alterados. O processo pode passar a operar com um estado incorreto ou encerrar. | Integridade e disponibilidade |

[MITRE, CWE-125](https://cwe.mitre.org/data/definitions/125.html) · [MITRE, CWE-787](https://cwe.mitre.org/data/definitions/787.html)

O motor usa informações sobre a representação dos elementos para decidir como tratá-los. A documentação do V8, por exemplo, explica que o motor distingue categorias de elementos de arrays para escolher operações adequadas a cada categoria. A resolução discute **confusão de tipos**, uma situação em que um dado é interpretado como se tivesse uma representação diferente da real. Uma maneira de explicar a ideia é lembrar que o significado de um padrão de bits depende do formato usado para interpretá-lo. [V8, Elements kinds](https://v8.dev/blog/elements-kinds) · [Browser Dojo, capítulo oob-v8](https://github.com/jackfromeast/browser-dojo/tree/main/v8/2019-star-ctf-oob-v8)

## 4. O que a resolução publicada descreve

O Browser Dojo mostra por que a análise vai além de identificar o primeiro índice inválido. O artigo relaciona a perda do limite à possibilidade de corromper o estado do motor e discute um alcance de leitura e escrita maior que o da operação inicial. Em seguida, descreve dois desfechos de **desvio do fluxo de controle**, isto é, uma mudança indevida nas instruções que o processo executa. Um envolve o ambiente nativo do processo e o outro discute o ambiente de execução de WebAssembly. [Browser Dojo, capítulo oob-v8](https://github.com/jackfromeast/browser-dojo/tree/main/v8/2019-star-ctf-oob-v8)

A evidência usada aqui para descrever esse desfecho é a análise publicada do executável modificado do desafio. O alcance da conclusão apresentada no seminário é esse processo. Para a parte prática, a seção seguinte verifica a regra de limites com um exemplo independente em JavaScript.

## 5. Demonstração para o seminário

No exemplo, a operação recebe um vetor denso e só lê um elemento se o índice estiver na faixa. Projete a função e peça ao público para prever os resultados de `2` e `3` antes de mostrar a tabela. O caso `2` confirma que o último elemento válido continua acessível. O caso `3` exercita o primeiro índice que a função deve recusar.

```javascript
function lerElemento(vetor, indice) {
  if (!Number.isInteger(indice) || indice < 0 || indice >= vetor.length) {
    throw new RangeError("Índice fora da faixa")
  }
  return vetor[indice]
}

const vetor = [10, 20, 30]
const casos = [
  { nome: "Primeiro índice", dados: vetor, indice: 0 },
  { nome: "Último índice", dados: vetor, indice: 2 },
  { nome: "Primeiro após o fim", dados: vetor, indice: 3 },
  { nome: "Índice negativo", dados: vetor, indice: -1 },
  { nome: "Índice fracionário", dados: vetor, indice: 1.5 },
  { nome: "Vetor vazio", dados: [], indice: 0 },
]

for (const { nome, dados, indice } of casos) {
  try {
    console.log(nome, "→", lerElemento(dados, indice))
  } catch (erro) {
    console.log(nome, "→", erro.message)
  }
}
```

| Caso | Resultado verificado |
| --- | --- |
| Primeiro índice, `0` | `10` |
| Último índice, `2` | `30` |
| Primeiro após o fim, `3` | Índice fora da faixa |
| Índice negativo, `-1` | Índice fora da faixa |
| Índice fracionário, `1.5` | Índice fora da faixa |
| Índice `0` em vetor vazio | Índice fora da faixa |

Em código nativo que manipula buffers, a checagem deve proteger a leitura ou escrita usando os limites reais da região autorizada. Testes de regressão devem cobrir as duas operações no último índice válido, no primeiro inválido e em uma região vazia. Ferramentas de instrumentação, como AddressSanitizer, ajudam a detectar acessos fora dos limites durante os testes do código nativo. [MITRE, CWE-787](https://cwe.mitre.org/data/definitions/787.html) · [Clang, AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html)

## Roteiro de 30 minutos

Cada integrante tem **3 minutos**, incluindo a passagem de fala. Os **3 minutos finais** ficam reservados para perguntas ou para discutir os casos de teste se as perguntas forem feitas fora do tempo.

| Tempo | Integrante | Slide | Ponto a apresentar |
| --- | --- | --- | --- |
| 00:00–03:00 | 1 | O caso e a fonte | Desafio, contexto histórico, pergunta de abertura e créditos. |
| 03:00–06:00 | 2 | O que o V8 faz | Como uma operação JavaScript depende do motor. |
| 06:00–09:00 | 3 | O último índice válido | Quadro de três elementos e a condição de limite. |
| 09:00–12:00 | 4 | Onde o desafio rompe o limite | Alteração deliberada do motor e definição de OOB. |
| 12:00–15:00 | 5 | O efeito de ler e escrever fora | Confidencialidade, integridade e disponibilidade. |
| 15:00–18:00 | 6 | A interpretação dos dados | Representação interna e confusão de tipos. |
| 18:00–21:00 | 7 | O impacto descrito na solução | Desvio de fluxo, as duas variantes em nível conceitual e o alcance da evidência. |
| 21:00–24:00 | 8 | Demonstração | Previsão do público e verificação dos casos de fronteira. |
| 24:00–27:00 | 9 | Prevenção e fechamento | Invariante, regressão e referência do trabalho. |
| 27:00–30:00 | Grupo | Perguntas | O integrante responsável pelo tema responde. |

### Falas e transições

**1 · O caso e a fonte.** Abra com “Se um vetor tem três elementos, o que deveria acontecer ao pedir o quarto?”. Identifique o `oob-v8` como um desafio do StarCTF 2019 e mostre os créditos. Diga que o objeto de estudo é um V8 alterado para o CTF. Passe a fala com “Para localizar a falha, precisamos distinguir o código JavaScript do motor que o executa”.

**2 · O que o V8 faz.** Mostre `[10, 20, 30]`. Na linguagem, ele é um array com três valores. No motor, é um objeto que precisa de armazenamento e de informações sobre como lidar com seus elementos. Explique que o desafio envolve uma operação nessa implementação interna. Passe a fala com “Agora vamos determinar quais posições a operação deveria alcançar”.

**3 · O último índice válido.** Peça para a turma localizar os valores `10` e `30` no quadro. Mostre que `3` é o comprimento e `2` é o índice do último elemento. Compare visualmente `índice < 3` e `índice ≤ 3`. Passe a fala com “Com a faixa definida, podemos localizar exatamente onde a operação do desafio sai dela”.

**4 · Onde o desafio rompe o limite.** Aponte a célula da posição `3` no quadro. A operação inserida no desafio trabalha uma posição além da área prevista. Nomeie o erro como OOB e explique que a posição do quadro representa um acesso do motor. Passe a fala com “A consequência muda conforme essa operação lê ou escreve”.

**5 · O efeito de ler e escrever fora.** Use a tabela da seção 3. Dê um exemplo abstrato de leitura que revela um dado que a operação não deveria enxergar e de escrita que altera um dado usado pelo próprio processo. Se perguntarem sobre tamanho, explique que uma posição é uma unidade de elemento. Passe a fala com “No motor, os dados também descrevem como outros valores devem ser interpretados”.

**6 · A interpretação dos dados.** Defina representação como o formato com que um valor é armazenado. Explique que o motor usa informações sobre o tipo dos elementos para escolher como tratá-los. Chame de confusão de tipos a interpretação incompatível com o formato real. Passe a fala com “A resolução publicada investiga o que acontece quando essa integridade deixa de valer”.

**7 · O impacto descrito na solução.** Explique o que significa desviar o fluxo de controle com a pergunta “Quem determina qual instrução o processo executa a seguir?”. Cite as duas variantes discutidas no README, uma no ambiente nativo e outra no ambiente WebAssembly, e o desfecho que elas têm em comum no artefato do desafio. Atribua esse resultado ao relato publicado. Passe a fala com “Vamos mostrar a propriedade de segurança que impediria o primeiro acesso fora da faixa”.

**8 · Demonstração.** Compare `2` com `3` e execute o exemplo JavaScript. Depois peça à turma para explicar por que o vetor vazio recusa até o índice `0`. Se o tempo apertar, use os resultados da tabela e mostre só a condição de guarda. Passe a fala com “Esses casos podem virar testes de regressão da regra de acesso”.

**9 · Prevenção e fechamento.** Retome a pergunta inicial. No vetor com três elementos, a quarta posição deve ser recusada por uma operação que acessa elementos existentes. Relacione isso aos testes de leitura e escrita e à instrumentação durante o desenvolvimento. Encerre creditando o Browser Dojo e Faraz e identifique a demonstração de validação como a parte prática deste seminário.

## Perguntas para o ensaio

**Uma posição a mais quer dizer um byte a mais?** A posição identifica um elemento. A quantidade de bytes depende do formato usado para armazená-lo.

**Por que acrescentar um valor a um array JavaScript pode funcionar?** Um array comum pode crescer de acordo com as regras da linguagem. O acesso do CTF ocorre no código interno do motor e ultrapassa o limite da região prevista para a operação. [MDN, Array.length](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/length)

**Por que o material cita V8 7.5.0?** É a versão histórica que o Browser Dojo identifica como base do artefato. A análise se refere à alteração introduzida para o desafio. [Browser Dojo, capítulo oob-v8](https://github.com/jackfromeast/browser-dojo/tree/main/v8/2019-star-ctf-oob-v8)

**O que foi verificado na preparação?** A estrutura e as afirmações do relato foram examinadas na referência. Os seis casos da demonstração de validação foram executados com JavaScript comum.

**Qual caso de teste revela um erro de uma posição no limite superior?** Com `n` elementos, compare os resultados de `n − 1` e `n`. O primeiro deve ser aceito para `n > 0`. O segundo deve ser recusado em qualquer comprimento.
