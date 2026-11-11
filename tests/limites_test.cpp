#include "limites.h"

#include <cstdlib>
#include <exception>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {

bool esperarValor(const char* caso, const std::vector<int>& elementos,
                  std::vector<int>::difference_type indice, int esperado) {
    try {
        const int observado = lerElemento(elementos, indice);
        if (observado != esperado) {
            std::cerr << "[FALHA] " << caso << ": esperado " << esperado
                      << ", observado " << observado << ".\n";
            return false;
        }
        std::cout << "[OK] " << caso << ": esperado " << esperado
                  << ", observado " << observado << ".\n";
        return true;
    } catch (const std::exception& erro) {
        std::cerr << "[FALHA] " << caso << ": exceção inesperada: "
                  << erro.what() << ".\n";
    } catch (...) {
        std::cerr << "[FALHA] " << caso << ": exceção desconhecida.\n";
    }
    return false;
}

bool esperarForaDoIntervalo(const char* caso, const std::vector<int>& elementos,
                           std::vector<int>::difference_type indice) {
    try {
        const int observado = lerElemento(elementos, indice);
        std::cerr << "[FALHA] " << caso
                  << ": esperada std::out_of_range, mas retornou "
                  << observado << ".\n";
    } catch (const std::out_of_range&) {
        std::cout << "[OK] " << caso << ": std::out_of_range.\n";
        return true;
    } catch (const std::exception& erro) {
        std::cerr << "[FALHA] " << caso << ": tipo de exceção incorreto: "
                  << erro.what() << ".\n";
    } catch (...) {
        std::cerr << "[FALHA] " << caso << ": exceção desconhecida.\n";
    }
    return false;
}

}  // namespace

int main() {
    const std::vector<int> elementos{10, 20, 30};
    const std::vector<int> vazio;
    constexpr int total = 5;
    int aprovados = 0;

    aprovados += esperarValor("Primeiro índice válido", elementos, 0, 10);
    aprovados += esperarValor("Último índice válido", elementos, 2, 30);
    aprovados += esperarForaDoIntervalo("Índice igual ao tamanho (3)", elementos, 3);
    aprovados += esperarForaDoIntervalo("Índice negativo (-1)", elementos, -1);
    aprovados += esperarForaDoIntervalo("Vetor vazio (índice 0)", vazio, 0);

    std::cout << "Resumo: " << aprovados << '/' << total << " testes aprovados.\n";
    return aprovados == total ? EXIT_SUCCESS : EXIT_FAILURE;
}
