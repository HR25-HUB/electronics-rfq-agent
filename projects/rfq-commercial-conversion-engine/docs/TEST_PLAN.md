# Test plan

## Golden cases

- GC01 explicit full approval → KT37/KT38
- GC02 price objection → KT33/new quote
- GC03 partial quantity → KT33/new quote
- GC04 payment terms → KT34/new quote
- GC05 rejection → X02/LOST

## Critical negative cases

- silence → never KT37
- conditional approval → never KT37
- old/quoted approval text → never KT37
- wrong quote version → KT37/KT38 blocked
- qty/price/currency mismatch → KT38 blocked
- duplicate order command → same order
- 1C unavailable → KT38 remains valid
