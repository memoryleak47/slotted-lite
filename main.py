from dataclasses import dataclass

@dataclass(frozen=True)
class Id:
    i: int

    def __repr__(self):
        return "id" + str(self.i)

# slots are integers
type Slot = int

class Class:
    def __init__(self, arity: int):
        self.group = Group(arity)
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

# Reorders the slots a bunch of AppliedIds, so that they are lexicographically minimal.
# This means that the first id will always have (0, 1, 2, ...) as arguments.
# Eg. (id2[4, 2, 1], id5[0, 1, 3, 4]) would reorder to
#     (id2[0, 1, 2], id5[3, 2, 4, 0]
# The ids themselves stay unchanged.
def reorder(app_ids: tuple(AppliedId)) -> (dict[Slot, Slot], tuple(AppliedId)):
    d = {}
    out = []
    for a in app_ids:
        args = []
        for s in a.args:
            if s not in d:
                d[s] = len(d)
            args.append(d[s])
        args = tuple(args)
        out.append(AppliedId(a.id, args))
    return (d, tuple(out))

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
            # if id7[0, 1, 2] -> id3[2, 1] is a leader edge, then we want to simplify
            #    id7[a, b, c] -> id3[c, b]
            args = tuple(x.args[a] for a in l.args)
            x = AppliedId(l.id, args)

    def union(self, x: AppliedId, y: AppliedId):
        while True:
            x = self.find(x)
            y = self.find(y)
            if set(x.args) == set(y.args):
                break
            else:
                # redundant slots!
                for s in set(x.args) - set(y.args):
                    self.mark_slot_redundant(x, s)
                for s in set(y.args) - set(x.args):
                    self.mark_slot_redundant(y, s)

        # all redundancies should be handled now!
        assert(set(x.args) == set(y.args))

        if x == y: return

        _, (x, y) = reorder((x, y))

        if x.id == y.id:
            # symmetries!
            self.classes[x.id].group.add(y.args)
        else:
            self.classes[x.id].leader = y

    def mark_slot_redundant(self, x: AppliedId, s: Slot):
        x = self.find(x)
        if s not in x.args: return

        s = x.args.index(s)

        old_arity = self.classes[x.id].arity
        y = self.alloc(old_arity - 1)
        args = tuple(a for a in range(old_arity) if a != s)
        self.classes[x.id].leader = AppliedId(y, args)

    def is_equal(self, x: AppliedId, y: AppliedId) -> bool:
        x = self.find(x)
        y = self.find(y)
        if x.id != y.id:
            return False
        _, (x, y) = reorder((x, y))
        return self.classes[x.id].group.contains(y.args)

# a group permutation.
# Required to express equations like id0[0, 1] = id0[1, 0].
type Perm = tuple(Slot)

def compose(x: Perm, y: Perm) -> Perm:
    return tuple(x[y[i]] for i in range(len(x)))

# The most naive implementation of a permutation group: A set of permutations that is closed under composition.
class Group:
    def __init__(self, arity: int):
        identity_perm = tuple(range(arity))
        self.perms = {identity_perm}

    def add(self, x: Perm):
        self.perms.add(x)
        self.complete()

    def complete(self):
        while True:
            n = len(self.perms)
            new = set()
            for x in self.perms:
                for y in self.perms:
                    new.add(compose(x, y))
            self.perms.update(new)
            if n == len(self.perms):
                break

    def contains(self, x: Perm) -> bool:
        return x in self.perms

def test1():
    suf = SlottedUF()
    a = AppliedId(suf.alloc(2), (2, 3))
    b = AppliedId(suf.alloc(2), (2, 3))
    print(a)
    assert(not suf.is_equal(a, b))
    suf.union(a, b)
    assert(suf.is_equal(a, b))

def test2():
    suf = SlottedUF()
    a = AppliedId(suf.alloc(2), (2, 3))
    b = AppliedId(suf.alloc(2), (2, 4))
    assert(not suf.is_equal(a, b))
    suf.union(a, b)
    assert(suf.find(a).args == (2,))
    assert(suf.find(b).args == (2,))

def test3():
    g = Group(4)
    g.add((1, 2, 3, 0))
    assert(g.contains((2, 3, 0, 1)))
    assert(len(g.perms) == 4)

test1()
test2()
test3()
