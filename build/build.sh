#!/bin/bash

### =============== Início das variáveis =============== ###

DOCKER_IMAGE="starctf-2019-oob-v8"
DIFF_FILE="oob.diff"
ARGS_FILE="args.gn"
V8_BASE_COMMIT="6dc88c191f5ecc5389dc26efa3ca0907faef3598"
V8_RELEASE_DIR="/build/v8/v8/out.gn/x64.release"
OUTPUT_FILES="d8,snapshot_blob.bin,natives_blob.bin"

### =============== Fim das variáveis =============== ###


SCRIPT_DIR="$(dirname "$(realpath "$0")")"
CHALLENGE_DIR="$SCRIPT_DIR/../challenge"
TEMPLATE_FILE="$SCRIPT_DIR/build.template.Dockerfile"
DOCKER_FILE="$SCRIPT_DIR/build.Dockerfile"
cd "$SCRIPT_DIR" || exit 1

if [ ! -d "$CHALLENGE_DIR" ]; then
    echo "Criando diretório do desafio em $CHALLENGE_DIR"
    mkdir -p "$CHALLENGE_DIR"
fi

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Arquivo de modelo $TEMPLATE_FILE não existe!"
    exit 1
fi

echo "[+] Gerando Dockerfile a partir do modelo..."

if [ -f "$ARGS_FILE" ]; then
    COPY_ARGS="COPY ./$ARGS_FILE /build/v8/v8/out.gn/x64.release/\nRUN chmod 644 /build/v8/v8/out.gn/x64.release/$ARGS_FILE"
else
    COPY_ARGS="RUN chmod 644 out.gn/x64.release/args.gn"
fi

sed -e "s/{{ V8_BASE_COMMIT }}/$V8_BASE_COMMIT/g" \
    -e "s/{{ DIFF_FILE }}/$DIFF_FILE/g" \
    -e "s|{{ COPY_ARGS }}|$COPY_ARGS|g" \
    "$TEMPLATE_FILE" > "$DOCKER_FILE"

echo "[+] Construindo imagem Docker com build.Dockerfile..."
sudo docker build -t $DOCKER_IMAGE -f build.Dockerfile .


IFS=',' read -r -a FILE_ARRAY <<< "$OUTPUT_FILES"

TEST_FILES=""
COPY_FILES=""
for FILE in "${FILE_ARRAY[@]}"; do
    TEST_FILES="$TEST_FILES test -f $V8_RELEASE_DIR/$FILE &&"
    COPY_FILES="$COPY_FILES $V8_RELEASE_DIR/$FILE"
done

TEST_FILES=${TEST_FILES%"&&"}

echo "[+] Executando o contêiner Docker para compilar o V8 e copiar os arquivos..."
sudo docker run --rm -v "$CHALLENGE_DIR:/challenge" $DOCKER_IMAGE bash -c " \
    $TEST_FILES && \
    cp $COPY_FILES /challenge/ \
" && echo "Arquivos copiados para $CHALLENGE_DIR" || echo "[!] Erro: um ou mais arquivos necessários estão ausentes."

echo "[+] Removendo imagem Docker $DOCKER_IMAGE..."
sudo docker rmi $DOCKER_IMAGE

echo "Compilação e cópia concluídas."
