FROM ubuntu:18.04

RUN mkdir -p /build/v8
WORKDIR /build

RUN apt update && apt install -yq --no-install-recommends \
    git \
    python3.8 \
    python2.7 \
    ca-certificates \
    curl \
    tar \
    xz-utils \
    build-essential \
    lsb-release \
    sudo \
    file \
    ninja-build

# O Ninja precisa de Python 3 para compilar o V8; o Python 3.6 padrão causa erro nesse script
RUN ln -s /usr/bin/python2.7 /usr/bin/python
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1

# Obter depot_tools
RUN git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
ENV PATH=/build/depot_tools:$PATH
RUN gclient

# Baixar o código-fonte do V8
## O comando gclient sync pode apresentar o erro a seguir
## Relacionado a: invalid cross-device link
## Referência: https://groups.google.com/a/chromium.org/g/chromium-dev/c/Sa3_-7tKR0E
ENV GCLIENT_SUPPRESS_GIT_VERSION_WARNING=1
RUN cd /build/v8 && fetch v8 && \
    cd v8 &&\
    ./build/install-build-deps.sh --unsupported &&\
    git checkout {{ V8_BASE_COMMIT }} &&\
    gclient sync -D

WORKDIR /build/v8/v8

# Copiar o arquivo de alterações
COPY ./{{ DIFF_FILE }} /build/
RUN chmod 644 /build/{{ DIFF_FILE }}
RUN git apply /build/{{ DIFF_FILE }}


RUN ./tools/dev/v8gen.py x64.release
## SE O ARQUIVO ARGS.GN FOR FORNECIDO
{{ COPY_ARGS }}
RUN ninja -C out.gn/x64.release d8
