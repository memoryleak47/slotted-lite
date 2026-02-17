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
            if set(x.args) != set(y.args):
                # redundant slots!

                # Example: if id3[a, b] = id7[a], then id3[a, b] doesn't really depend on b anymore.
                # Reasoning: id3[a, b] = id7[a] = id3[a, c]. Thus id3[a, b] = id3[a, c] for any slot c.
                # Thus, we'll mark b redundant in id3[a, b].
                self.mark_slots_redundant(x, set(x.args) - set(y.args))
                self.mark_slots_redundant(y, set(y.args) - set(x.args))
            else:
                break

        # all redundancies should have been handled now!
        assert(set(x.args) == set(y.args))

        if self.is_equal(x, y): return

        _, (x, y) = reorder((x, y))

        if x.id == y.id:
            # symmetries!
            # Example: if id3[0, 1] = id3[1, 0], we need to store this symmetry [1, 0] in the group of id3!
            self.classes[x.id].group.add(y.args)
        else:
            self.add_uf_edge(x.id, y)

    # Makes x point to y in the unionfind.
    def add_uf_edge(self, x: Id, y: AppliedId):
        self.classes[x].leader = y

        x_arity = self.classes[x].arity
        y_arity = self.classes[y.id].arity

        # y.id inherits the symmetries from x
        identity = tuple(range(x_arity))
        for p in self.classes[x].group.perms:
            # The equation corresponding to this permutation.
            lhs = AppliedId(x, identity)
            rhs = AppliedId(x, p)

            # Tranforming the equation from x to y.id.
            lhs = self.find(lhs)
            rhs = self.find(rhs)

            _, (lhs, rhs) = reorder((lhs, rhs))

            for s in rhs.args:
                assert(s < y_arity)

            self.classes[y.id].group.add(rhs.args)

        # x is now "non-canonical", thus it has no reason to a group.
        # If you want to know the symmetries, check the permutation group of the leader.
        self.classes[x].group = None

    def mark_slots_redundant(self, x: AppliedId, slots: set[Slot]):
        x = self.find(x)

        redundants = set()
        for s in slots:
            if s not in x.args: continue
            s = x.args.index(s)
            redundants.update(self.classes[x.id].group.orbit(s))

        if len(redundants) == 0:
            return

        old_arity = self.classes[x.id].arity
        new_arity = old_arity - len(redundants)
        y = self.alloc(new_arity)
        args = tuple(s for s in range(old_arity) if s not in redundants)
        self.add_uf_edge(x.id, AppliedId(y, args))

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

    def orbit(self, s: Slot) -> set[Slot]:
        orbit = {s}
        for p in self.perms:
            orbit.add(p[s])
        return orbit

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
