from dataclasses import dataclass, field

@dataclass(frozen=True)
class Slot:
    name: int

    def __repr__(self):
        return f"${self.name}"

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
        return [a for (a, b) in self.map]

    def values(self):
        return [b for (a, b) in self.map]

    def __getitem__(self, key: Slot):
        for a, b in self.map:
            if a == key:
                return b
        raise KeyError(key)

    # applies the `self` renaming onto some object `o`
    def __mul__(self, o):
        if isinstance(o, Renaming):
            # This is effectively a partial compose
            return Renaming.mk([(a, self[b]) for (a, b) in other if b in self.keys()])
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
        assert(sorted(slots) == slots)
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

        for perm in self.classes[a.id].group.perms:
            # a.id :: A
            # b.id :: B
            # perm :: A -> A
            # b.m :: B -> A
            # -> b.m.inverse() * perm * b.m :: B -> B
            self.classes[b.id].group.add(b.m.inverse() * perm * b.m)
        self.classes[a.id].leader = b

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
            aslots = set(a.renaming.values())
            bslots = set(b.renaming.values())
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
