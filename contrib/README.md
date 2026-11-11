# Contribuição adicional: buscar os PINs por blocos de permutações

Esta pasta acrescenta uma implementação e uma análise ao material original do Google CTF. A cifra e a observação de que o token se repete a cada 16 rodadas já aparecem na [resolução original](../solution/README.md). A contribuição aqui é transformar um bloco inteiro de rodadas em tabelas de consulta, implementar a busca com essas tabelas e conferir sua compatibilidade com o programa original.

## O desafio em linguagem simples

Um CTF é uma competição de desafios de segurança. Neste desafio, o objetivo é recuperar três mensagens de um aplicativo Android escrito em Flutter. Juntas, elas formam uma flag, o texto que comprova a resolução.

O aplicativo cifra cada mensagem usando dois valores:

1. Um PIN entre 1 e 9999. O número do PIN também determina quantas rodadas de cifragem são aplicadas.
2. Um token calculado a partir do horário em segundos: `Base62(SHA1("gctf25_" + timestamp)[:8])`.

As datas dos segredos revelam o minuto. Considerando o fuso `Europe/Zurich`, usado na solução original, sobram somente 60 horários candidatos para cada mensagem. O token parece aleatório, mas pode ser reproduzido para cada um desses segundos.

Base62 é uma codificação de bytes em letras e números; ela não acrescenta uma camada de segurança. O problema principal também não é uma quebra de SHA-1: é o pequeno conjunto de horários possíveis usado como entrada do hash.

## O que esta implementação acrescenta

Em cada rodada, cada byte da mensagem passa por uma soma e uma rotação de bits. Ao final, os bytes mudam de posição. Um byte não é combinado com outro byte da mensagem. Portanto, para uma posição inicial conhecida, um conjunto de rodadas equivale a:

- Uma posição final conhecida.
- Uma permutação dos 256 valores possíveis daquele byte.

Em vez de refazer as operações de todas as rodadas durante a busca, `solve_fast.py` calcula essa permutação uma vez e guarda sua inversa. Cada consulta à tabela desfaz um bloco inteiro.

Para tokens de 8 bytes, o estado do token e a sequência das rotações se repetem após 16 rodadas. Escrevemos então:

```text
PIN = 16 × q + r, com 0 ≤ r < 16
PIN % 8 = r % 8

mensagem cifrada = prefixo_de_r_rodadas(bloco_de_16_rodadas^q(mensagem))
```

Para cada resto `r`, o programa desfaz as `r` rodadas finais uma vez. Em seguida, aplica repetidamente a tabela inversa do bloco, testando os PINs `r`, `r + 16`, `r + 32` e assim por diante. O PIN zero é descartado. Como `r` fixa `PIN % 8`, a sequência do token usada nesse grupo também fica determinada.

A movimentação dos bytes é incluída nas tabelas. Isso permite trabalhar com mensagens cujo comprimento não é múltiplo de 16. O programa percorre os 9999 PINs de cada token, aceita candidatos com caracteres ASCII imprimíveis e confirma cada candidato por recifragem. Ele retorna todos os candidatos encontrados, para não tratar uma mensagem curta e ambígua como uma resposta única.

Um cuidado adicional: a codificação Base62 pode descartar bytes zero no início do token. Para tokens menores, usamos um período seguro igual a `mmc(16, tamanho_do_token)`. Há testes específicos para esse caso; ele também aparece em um dos horários candidatos da busca do terceiro segredo.

## Como reproduzir

Execute a partir da raiz do repositório. É necessário Python 3.9 ou superior e a base de fusos horários do sistema; se o Python não encontrar `Europe/Zurich`, instale o pacote `tzdata` no ambiente Python.

```bash
# Recuperar os três segredos, sem informar PIN ou segundo.
python3 contrib/solve_fast.py --all

# Resolver somente o primeiro segredo.
python3 contrib/solve_fast.py --time '04/08/2023 13:37' --ciphertext fmMf7mIMbHcPoQmLGx1CO0XVGBmhjTaYhB0

# Gerar um relatório e executar as verificações.
python3 contrib/solve_fast.py --all --json
python3 -m unittest discover -s contrib -p 'test_*.py' -v
python3 contrib/benchmark.py --json
```

O solucionador não importa `solution/crack.py`, não lê `metadata.yaml` e não recebe os PINs ou os segundos corretos. A importação do código original ocorre somente nos testes e no benchmark, para comparação. As constantes do solucionador contêm apenas as datas e os textos cifrados publicados.

## Resultados e verificação

A execução registrada em [resultado.json](resultado.json) testou 60 tokens e 599940 combinações de segundo/PIN por segredo. Encontrou um candidato único para cada um:

| Segredo | Segundo | PIN | Mensagem recuperada |
| --- | --- | --- | --- |
| 1 | 27 | 8126 | `CTF{Ok4y_h4v3_u_0ptim1zed_` |
| 2 | 31 | 5178 | `brUt3_f0rcE_0R_y0u_jUst` |
| 3 | 48 | 7490 | `_uSeD_a_l0t_0f_c0Res?}` |

O relatório contém o tempo medido e a confirmação da recifragem. Os oito testes também comparam a cifra com a implementação original, verificam as três respostas publicadas, testam limites entre blocos, comprimentos de mensagem diferentes e tokens menores. Há ainda um exemplo gerado pelo código original cuja busca recupera o segundo e o PIN sem receber esses valores como entrada.

O [benchmark.json](benchmark.json) compara a busca otimizada original com a nova implementação em três repetições de um experimento controlado: mesmo token conhecido, mesma mensagem sintética e PINs até 2000. O método original encerra ao encontrar o primeiro texto imprimível; o novo verifica todos os PINs desse intervalo. A medição nova inclui a criação das tabelas e a recifragem. A saída de diagnóstico do original é capturada em memória para evitar medir a impressão no terminal.

Essa comparação mede a busca de PIN para um token conhecido; ela não é uma medição da busca completa dos três segredos. O relatório completo mede essa outra operação separadamente. Os tempos e a razão entre eles dependem do equipamento e da versão do Python.

## Roteiro curto para apresentar

1. Mostre o aplicativo e explique que a flag está dividida em três mensagens cifradas.
2. Mostre `token_at()` e explique por que um minuto conhecido gera apenas 60 tokens candidatos.
3. Cite a descoberta da periodicidade de 16 rodadas na resolução original.
4. Apresente a contribuição adicional: `inverse_block()` substitui várias rodadas por uma consulta por byte, e `find_candidates()` reaproveita o trabalho para PINs com o mesmo resto.
5. Execute `python3 contrib/solve_fast.py --all` e mostre as três mensagens, os PINs e a confirmação da recifragem.
6. Mostre os testes e o benchmark, explicando exatamente o que cada medição compara.

Uma forma de descrever o trabalho é: **“A partir da resolução publicada do Google CTF, acrescentamos uma implementação por blocos de permutações, com validação contra o código original e um experimento de desempenho reproduzível.”**

## Escopo e créditos

Esta contribuição atua na etapa de recuperação dos segredos depois de conhecido o algoritmo. Ela não automatiza a engenharia reversa do APK. A seleção por ASCII é adequada às mensagens deste desafio e pode produzir vários candidatos para entradas diferentes. Recifrar confirma a consistência de um candidato com o token e o PIN; por si só, isso não prova que uma mensagem ambígua seja a pretendida.

Os arquivos em `solution/`, `src/`, `attachments/` e `metadata.yaml` pertencem ao material de origem e foram mantidos sem alterações. Esta pasta é uma contribuição de implementação e documentação, desenvolvida com auxílio de IA, e não uma reivindicação de descoberta original da cifra ou de sua periodicidade. A licença é [Apache 2.0](../LICENSE).
