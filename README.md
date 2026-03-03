"Naive" implementation of slotted e-graphs
==========================================

This implementation of slotted e-graphs is intended to be readable, instead of efficient.
Most stuff comes from chats with Philip and what we cooked up there: https://github.com/philzook58/slotteduf/

There's two implementations:
- One uses "positional arguments" id2[x, y, z], whereas
- the other uses "nominal arguments" id2[a=x, b=y, c=z].
