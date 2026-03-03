from dataclasses import dataclass, field

@dataclass(frozen=True)
class Slot:
    name: int

    def __repr__(self):
        return f"${self.name}"

    def __lt__(self, other: Slot):
        return self.name < other.name

@dataclass(frozen=True)
class Renaming:
    map: tuple[(Slot, Slot)]

    def __repr__(self):
        return "[" + ", ".join(f"{a} -> {b}" for (a, b) in self.map) + "]"

    def mk(l: iter[(Slot, Slot)]):
        l = sorted(l, key=lambda x: x[0])

        # Both keys and values have no duplicates!
        assert(len(l) == len(set(x[0] for x in l)))
        assert(len(l) == len(set(x[1] for x in l)))

        return Renaming(tuple(l))

    def inverse(self):
        return Renaming.mk([(b, a) for (a, b) in self.map])

    def keys(self):
        return {a for (a, b) in self.map}

    def values(self):
        return {b for (a, b) in self.map}

    def __getitem__(self, key: Slot):
        for a, b in self.map:
            if a == key:
                return b
        raise KeyError(key)

    # applies the `self` renaming onto some object `o`
    def __mul__(self, o):
        if isinstance(o, Renaming):
            # This is effectively a partial compose
            return Renaming.mk([(a, self[b]) for (a, b) in o if b in self.keys()])
        elif isinstance(o, Id):
            return RenamedId(self, o)
        elif isinstance(o, RenamedId):
            return RenamedId(self * o.m, o.id)
        else:
            raise TypeError(o)

    def __iter__(self):
        return iter(self.map)

@dataclass(frozen=True)
class Id:
    i: int

    def __repr__(self):
        return f"id{self.i}"

@dataclass(frozen=True)
class RenamedId:
    m: Renaming
    id: Id

    def __post_init__(self):
        assert(isinstance(self.m, Renaming))
        assert(isinstance(self.id, Id))

    def __repr__(self):
        return f"{self.m} * {self.id}"

# A perm is a renaming, where keys = values.
type Perm = Renaming

@dataclass
class Group:
    perms: set[Renaming]

    def __init__(self, elems: set[Slot]):
        identity = Renaming.mk(list(zip(elems, elems)))
        self.perms = {identity}

    def add(self, p: Perm):
        self.perms.add(p)
        self.complete()

    def complete(self):
        while True:
            cnt = len(self.perms)
            newperms = []
            for p1 in self.perms:
                for p2 in self.perms:
                    newperms.append(p1 * p2)
            self.perms.update(newperms)
            if cnt == len(self.perms):
                break

    def orbit(self, slot: Slot) -> set[Slot]:
        return {p[slot] for p in self.perms}

@dataclass
class Class:
    slots: list[Slot] = field()
    leader: RenamedId = field()
    group: Group = field()

@dataclass
class SlottedUF:
    classes: dict[Id, Class] = field(default_factory=dict)

    def makeset(self, slots: list[Slot]) -> RenamedId:
        assert(tuple(sorted(slots)) == tuple(slots))
        id = Id(len(self.classes))
        i = RenamedId(Renaming.mk([(a, a) for a in slots]), id)
        self.classes[id] = Class(slots, i, Group(set(slots)))
        return i

    def find(self, x: RenamedId) -> RenamedId:
        assert isinstance(x, RenamedId)

        while True:
            y = x.m * self.classes[x.id].leader
            if x == y: return x

    # Make a point to b
    def move_to(self, a: Id, b: RenamedId):
        assert(a != b.id)

        for perm in self.classes[a].group.perms:
            # a.id :: A
            # b.id :: B
            # perm :: A -> A
            # b.m :: B -> A
            # -> b.m.inverse() * perm * b.m :: B -> B
            self.classes[b.id].group.add(b.m.inverse() * perm * b.m)
        self.classes[a].leader = b

    def shrink_slots(self, a: RenamedId, remaining_slots: set[Slot]):
        a = self.find(a)
        remaining_slots = remaining_slots & a.m.values()

        # a.id :: A
        # a.m :: A -> X
        # remaining_slots :: X

        # remaining :: A
        remaining = {a.m.inverse()[x] for x in remaining_slots}

        # aslots :: A
        aslots = self.classes[a.id].slots

        assert aslots.issuperset(remaining)
        if aslots == remaining: return
        G = self.classes[a.id].group
        losing = set()
        for s in aslots - remaining:
            losing.update(G.orbit(s))
        remaining = remaining - losing
        b = self.makeset(remaining)
        self.move_to(a.id, b)

    def union(self, a: RenamedId, b: RenamedId):
        while True:
            a, b = self.find(a), self.find(b)
            aslots = set(a.m.values())
            bslots = set(b.m.values())
            if aslots != bslots:
                # redundant slots
                self.shrink_slots(a, aslots & bslots)
                self.shrink_slots(b, aslots & bslots)
            else:
                break
        a, b = self.find(a), self.find(b)

        # We'll make a point to b:
        # a.m * a.id = b.m * b.id
        # -> a.id = a.m.inverse() * b.m * b.id
        m_ab = a.m.inverse() * b.m

        if a.id != b.id:
            # make a point to b
            self.move_to(a.id, m_ab * b.id)
        else:
            # add self-symmetry
            self.classes[a.id].group.add(m_ab)

    def is_eq(self, a: RenamedId, b: RenamedId) -> bool:
        a = self.find(a)
        b = self.find(b)
        if a.id != b.id:
            return False

        # a.m * id = b.m * id
        # -> id = a.m.inverse() * b.m * id
        return a.m.inverse() * b.m in self.classes[a.id].group.perms

   ###################
#### Slotted E-Graph ####
   ###################

@dataclass(frozen=True)
class FNode():
    f: str # function symbol
    args: tuple[RenamedId]

@dataclass(frozen=True)
class Var():
    slot: Slot

type Node = FNode | Var
type Shape = Node

@dataclass
class SlottedEGraph():
    uf : SlottedUF = field(default_factory=SlottedUF)
    hashcons : dict[Shape, RenamedId] = field(default_factory=dict)

    # normalize node to its shape
    # n = m * sh
    def shape(self, n: Node) -> (Renaming, Shape):
        if isinstance(n, Var):
            m = Renaming.mk([(Slot(0), n.slot)])
            return m, Var(Slot(0))
        assert(isinstance(n, FNode))

        # TODO impl strong-shape computation

        # canonize args
        n = FNode(n.f, tuple(map(self.find, n.args)))

        # build translation mapping
        d = {}
        for a in n.args:
            for v in a.m.values():
                if v not in d:
                    d[v] = Slot(len(d))
        m = Renaming.mk(d.items())
        # m :: slots(n) -> Shape-slots

        # rename e-node accordingly
        shape = FNode(n.f, tuple(m*a for a in n.args))

        return m.inverse(), shape

    def add_node(self, n : ENode) -> RenamedId:
        m, shape = self.shape(n)
        if shape in self.hashcons:
            return m * self.hashcons[shape]

        id = self.uf.makeset(m.values())
        self.hashcons[shape] = m.inverse() * id
        return id

    def find(self, x: RenamedId) -> RenamedId:
        return self.uf.find(x)

    def union(self, a: RenamedId, b: RenamedId) -> None:
        return self.uf.union(a, b)

    def is_eq(self, a: RenamedId, b: RenamedId) -> bool:
        self.rebuild()
        return self.uf.is_eq(a, b)

    def rebuild(self):
        done = False
        while not done:
            done = True
            hashcons = {}
            for shape, x in self.hashcons.items():
                # shape corresponds to x
                x = self.find(x)
                m, shape2 = self.shape(shape)
                x2 = m*x
                # shape2 corresponds to x2

                if shape2 in hashcons:
                    done = False
                    self.uf.union(hashcons[shape2], x2)
                else:
                    hashcons[shape2] = x2
            self.hashcons = hashcons

