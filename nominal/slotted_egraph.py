from uf import *
from dataclasses import dataclass, field

@dataclass(frozen=True)
class AppNode():
    op: str
    children: tuple[RenamedId, ...]

    @property
    def slots(self) -> set[Slot]:
        return set.union(*[child.slots() for child in self.children])
    
    def apply_rename(self, R: Renaming) -> "AppNode":
        return AppNode(
            self.op,
            tuple(R * child for child in self.children)
        )

@dataclass(frozen=True)
class Var():
    name: Slot

type ENode = AppNode | Var
type Shape = ENode

@dataclass
class EGraph():
    uf : SlottedUF = field(default_factory=SlottedUF)
    memo : dict[Shape, RenamedId] = field(default_factory=dict)

    def shape_of_enode(self, n : ENode) -> tuple[Renaming, Shape]:
        # normalize enode to shape
        # n = m*s
        match n:
            case AppNode(op, children):                        
                eids = [self.find(c) for c in n.children]
                renaming = {}
                for eid in eids:
                    for s in eid.slots():
                        if s not in renaming:
                            renaming[s] = Slot(len(renaming))
                R = Renaming.of_list(renaming.items())
                return R.rev(), n.apply_rename(R)
            case Var(name):
                R = Renaming.of_list([(name, Slot(0))])
                return R.rev(), Var(Slot(0))
            case _:
                raise NotImplementedError()

    def add_enode(self, n : ENode) -> RenamedId:
        m, shape = self.shape_of_enode(n)
        i = self.memo.get(shape)
        if i is not None:
            return m * self.find(i)
        else:
            id = self.uf.makeset_slots(renaming.slots())
            self.memo[shape] = id
            return id

    def find(self, id : RenamedId) -> RenamedId:
        return self.uf.find(id)

    def union(self, a : RenamedId, b : RenamedId) -> None:
        # update memo here?
        return self.uf.union(a, b)

    def is_eq(self, a : RenamedId, b : RenamedId) -> bool:
        return self.uf.is_eq(a, b)

    def rebuild(self):
        done = False
        while not done:
            done = True
            new_memo : dict[Shape, RenamedId] = {}
            for shape, eid in self.memo.items():
                rep = self.find(eid)
                r2, shape2 = self.shape_of_enode(shape)
                if shape2 in new_memo:
                    existing = new_memo[shape2]
                    done = False
                    self.uf.union(r2 * rep, existing)
                else:
                    new_memo[shape2] = r2 * rep
            self.memo = new_memo
