#include "limites.h"

#include <stdexcept>

int lerElemento(const std::vector<int>& elementos,
                std::vector<int>::difference_type indice) {
    // 1. Rejeitar negativos antes de converter para um tipo sem sinal.
    if (indice < 0) {
        throw std::out_of_range("Indice negativo");
    }

    // 2. Converter somente depois de validar o limite inferior.
    const auto posicao = static_cast<std::vector<int>::size_type>(indice);

    // 3. Rejeitar também a posição igual ao tamanho, inclusive no vetor vazio.
    if (posicao >= elementos.size()) {
        throw std::out_of_range("Indice maior ou igual ao tamanho");
    }

    // 4. Acessar apenas após comprovar os dois limites.
    return elementos[posicao];
}
