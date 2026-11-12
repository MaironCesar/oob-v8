// Proposta estática: preserva a interface histórica, recusa o índice lógico length.
// Não é patch oficial nem build compilado.
if (!receiver->IsJSArray()) return undefined;
Handle<JSArray> array = Handle<JSArray>::cast(receiver);
if (!array->HasFastDoubleElements()) return undefined;
FixedDoubleArray elements = FixedDoubleArray::cast(array->elements());
uint32_t length = static_cast<uint32_t>(array->length()->Number());
if (length >= static_cast<uint32_t>(elements.length())) return undefined;
// Para o método original, length é sempre o primeiro índice lógico inválido.
if (length >= static_cast<uint32_t>(array->length()->Number())) return undefined;
if (read) return elements.get_scalar(length);
else elements.set(length, value->Number());
