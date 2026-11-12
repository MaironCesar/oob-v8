# Inventário e proveniência

## Estado inicial do workspace

Antes de criar este projeto, `find` e `git ls-tree` mostraram apenas `Writeup_oob-v8_Seminario(1).md` como arquivo de trabalho. Os diretórios `.agents`, `.aws` e `.codex` estavam vazios; `.git` continha metadados. Nenhum tarball, `d8`, snapshot, diff ou fonte V8 estava presente no checkout inicial. O commit local era `2b76604` (`Adicionar write-up do seminário oob-v8`). O original foi deixado intacto.

## Materiais públicos obtidos

Baixados do [Browser Dojo](https://github.com/jackfromeast/browser-dojo/tree/main/v8/2019-star-ctf-oob-v8) para `evidence/origins/`: `oob.diff`, `build.sh`, `args.gn`, `d8`, `natives_blob.bin`, `snapshot_blob.bin`, o tarball de 93.747.047 bytes, `solve.js`, `public-writeup.md` e as cinco imagens citadas por este último. O tarball contém 131 entradas sob `Chrome/`, incluindo `Chrome/oob.diff`, `Chrome/Release/chrome` e blobs. Seu diff interno tem SHA-256 idêntico ao diff baixado separadamente. Os hashes de todos os materiais obtidos estão em `evidence/logs/sha256.txt`; a ferramenta calcula hashes dos inputs que analisa em seu JSON.

O `build.sh` público fixa `V8_BASE_COMMIT=6dc88c191f5ecc5389dc26efa3ca0907faef3598`. Os oito cabeçalhos/arquivos C++ em `evidence/origins/v8/` e `v8-version.h` foram obtidos do espelho público [v8/v8 nesse commit](https://github.com/v8/v8/tree/6dc88c191f5ecc5389dc26efa3ca0907faef3598). `v8-version.h:11-14` declara 7.5.0.0. `file d8` identifica ELF 64 bits x86-64. O cabeçalho ELF é lido pela ferramenta.

Os binários e fontes originais em `evidence/origins/` não são modificados. O executável `environment/d8-run` e os blobs adjacentes são cópias para testes; `d8 --version` não é suportado por esse binário, portanto a versão foi confirmada no cabeçalho do commit, não no executável. A ligação binária exata ao commit é atribuída ao script de build público, sem atestação criptográfica independente.
