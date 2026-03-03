from slotted_egraph import *

s = lambda slot: eg.add_node(Var(slot))

eg = SlottedEGraph()
f = lambda x, y: eg.add_node(FNode("f", (x, y)))
g = lambda x, y: eg.add_node(FNode("g", (x, y)))
a = lambda _: eg.add_node(FNode("a", ()))

def test1():
    eg.union(g(s(0), s(1)), f(a(()), s(0)))

tests = [test1]
for t in tests:
    t()
