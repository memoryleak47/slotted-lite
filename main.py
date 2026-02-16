class Group:
    pass

class Id: pass

class Class:
    def __init__(self, arity: int):
        self.group = Group()
        self.arity = arity
        self.leader = None

class SlottedUF:
    classes: dict[Id, Class]

    def __init__(self):
        self.classes = {}

    def alloc(self, arity: int) -> Id:
        i = Id()
        self.classes[i] = Class(arity)
        return i

    def union(self, x, y):
        pass

    def is_equal(self, x, y):
        pass


suf = SlottedUF()
a = suf.alloc(2)
b = suf.alloc(2)
suf.union(a, b)
print(suf.is_equal(a, b))
