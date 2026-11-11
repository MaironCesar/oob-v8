#ifndef OOB_V8_LIMITES_H
#define OOB_V8_LIMITES_H

#include <vector>

// difference_type é um tipo inteiro com sinal.
// Retorna o elemento se 0 <= indice < elementos.size().
// Lança std::out_of_range para qualquer índice fora desse intervalo.
int lerElemento(const std::vector<int>& elementos,
                std::vector<int>::difference_type indice);

#endif
