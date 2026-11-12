"""Modelo didático de limites; não representa layout nem execução do V8."""


class ArrayModel:
    def __init__(self, storage, logical_length, map_kind):
        if not isinstance(logical_length, int) or logical_length < 0 or logical_length > len(storage):
            raise ValueError("logical length must fit storage")
        self.storage = list(storage)
        self.logical_length = logical_length
        self.map_kind = map_kind

    def vulnerable_read(self):
        return self.storage[self.logical_length]

    def corrected_read(self):
        index = self.logical_length
        if self.map_kind != "double" or index >= self.logical_length or index >= len(self.storage):
            return False, None
        return True, self.storage[index]

    def alternative_read(self, index):
        if self.map_kind != "double" or type(index) is not int or index < 0:
            return False, None
        if index >= self.logical_length or index >= len(self.storage):
            return False, None
        return True, self.storage[index]
