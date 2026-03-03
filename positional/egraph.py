from suf import *

# The uninterpreted function e-node.
@dataclass(frozen=True)
class FnNode:
    f: str
    args: tuple[AppliedId]

# The variable e-node.
@dataclass(frozen=True)
class VarNode:
    s: Slot

class EGraph:
    def __init__(self):
        self.hashcons = {}
        self.suf = SlottedUF()

    def add(self, n: FnNode) -> AppliedId:
        # "find" child ids.
        n = Node(n.f, tuple(self.suf.find(a) for a in n.args))

        # shape computation
        d, args = reorder(n.args)
        n = Node(n.f, args)

        # TODO actually use d.
        if n in self.hashcons:
            return self.hashcons[n]
        else:
            k = len(d)
            i = AppliedId(self.suf.alloc(k), tuple(range(k)))
            self.hashcons[n] = i
            return i

    def union(self, x: AppliedId, y: AppliedId):
        self.suf.union(x, y)
        self.rebuild()

    def rebuild(self):
        pass # TODO: something like this.
        """
        h = {}
        for (n, i) in self.hashcons.items():
            # canonicalize shape.
            n = Node(n.f, tuple(self.suf.find(a) for a in n.args))
            d, args = reorder(n.args)
            n = Node(n.f, args)

            # canonicalize applied id
            i = self.suf.find(i)

            if n in h:
                self.union(h[n], i)
            else:
                h[n] = i
        self.hashcons = h
        """
