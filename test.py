import cnfx

enc = cnfx.Encoder(bit_depth=3, cnf_path='test.cnf')

_0 = cnfx.Unit(enc, value=0)
_1 = cnfx.Unit(enc, value=1)
_3 = cnfx.Unit(enc, value=3)
x = cnfx.Unit(enc)
y = cnfx.Unit(enc)
z = cnfx.Unit(enc)
w = cnfx.Unit(enc)
u = cnfx.Unit(enc)
v = cnfx.Unit(enc)

assert x + y - z == w - u - v + _3
assert x - v != _0
assert z + u == _1

while cnfx.satisfy(encoder=enc, solver='kissat'):
    print(x.value, y.value, z.value, w.value, w.value, v.value,
          x.value + y.value - z.value == w.value - u.value - v.value + 3,
          x.value - v.value != 0,
          z.value + u.value == 1)