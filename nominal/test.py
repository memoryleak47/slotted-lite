from slotted_egraph import *

s = lambda slot: eg.add_node(Var(Slot(slot)))
f = lambda x, y: eg.add_node(FNode("f", (x, y)))
g = lambda x, y: eg.add_node(FNode("g", (x, y)))
a = lambda: eg.add_node(FNode("a", ()))

def test1():
    eg.union(g(s(0), s(1)), f(a(), s(0)))
    assert(eg.is_equal(g(s(24), s(5)), f(a(), s(24))))
    assert(eg.is_equal(g(s(24), s(5)), g(s(24), s(72))))

def test2():
    assert(not eg.is_equal(g(s(24), s(5)), f(a(), s(24))))

def test3():
    eg.union(f(s(0), s(1)), f(s(1), s(0)))
    eg.union(a(), g(s(0), f(s(0), s(1))))
    assert(eg.is_equal(a(), g(s(7), f(s(12), s(7)))))

tests = [test1, test2, test3]
for t in tests:
    eg = SlottedEGraph()
    t()
