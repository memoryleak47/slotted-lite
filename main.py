from dataclasses import dataclass

class Group:
    pass

@dataclass(frozen=True)
class Id:
    i: int

    def __repr__(self):
        return "id" + str(self.i)

# slots are integers
type Slot = int

class Class:
    def __init__(self, arity: int):
        self.group = Group()
        self.arity = arity
        self.leader = None

@dataclass(frozen=True)
class AppliedId:
    id: Id
    args: tuple[Slot]

    def __repr__(self):
        if self.args:
            return str(self.id) + "[" + ", ".join(map(str, self.args)) + "]"
        else:
            return str(self.id)

class SlottedUF:
    classes: dict[Id, Class]

    def __init__(self):
        self.classes = {}

    def alloc(self, arity: int) -> Id:
        i = Id(len(self.classes))
        self.classes[i] = Class(arity)
        return i

    def find(self, x: AppliedId) -> AppliedId:
        while True:
            l = self.classes[x.id].leader
            if l == None:
                return x
            x = AppliedId(l.id, tuple(x.args[a] for a in l.args))

    def union(self, x, y):
        x = self.find(x)
        y = self.find(y)

        if x == y: return
        assert(set(x.args) == set(y.args))

        y_arity = self.classes[y.id].arity
        out = list(range(y_arity))
        for i in range(y_arity):
            aa = y.args[i]
            aa = x.args.index(aa)
            out[i] = aa
        out = tuple(out)
        self.classes[x.id].leader = AppliedId(y.id, out)

    def is_equal(self, x, y):
        x = self.find(x)
        y = self.find(y)
        # TODO handle symmetries
        return x == y

suf = SlottedUF()
a = AppliedId(suf.alloc(2), (2, 3))
b = AppliedId(suf.alloc(2), (2, 3))
print(a)
print(suf.is_equal(a, b))
suf.union(a, b)
print(suf.is_equal(a, b))
