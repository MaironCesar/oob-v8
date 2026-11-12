// Proposta estática alternativa: valida índice informado e ambos os limites.
// Não é patch oficial nem build compilado; pseudocódigo C++ para auditoria.
if (!receiver->IsJSArray()) return undefined;
Handle<JSArray> array = Handle<JSArray>::cast(receiver);
if (!array->HasFastDoubleElements()) return undefined;
FixedDoubleArray elements = FixedDoubleArray::cast(array->elements());
uint32_t index = requested_index;
uint32_t logical_length = static_cast<uint32_t>(array->length()->Number());
if (index >= logical_length || index >= static_cast<uint32_t>(elements.length())) return undefined;
if (read) return elements.get_scalar(index);
else elements.set(index, value->Number());
