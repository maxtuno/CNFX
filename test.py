import math
import cnfx

enc = cnfx.Encoder(bit_depth=1, cnf_path='test.cnf')

_0 = cnfx.Unit(enc, value=0)
_e = cnfx.Unit(enc, value=math.e)
_pi = cnfx.Unit(enc, value=math.pi)
x = cnfx.Unit(enc)
y = cnfx.Unit(enc)
z = cnfx.Unit(enc)
w = cnfx.Unit(enc)
u = cnfx.Unit(enc)
v = cnfx.Unit(enc)

assert x + y - z == w - u - v + _e
assert x - v != _0
assert z + u == _pi
assert x * v == z

while cnfx.satisfy(encoder=enc, solver='kissat'):
    print(x.value, y.value, z.value, w.value, w.value, v.value,
          x.value + y.value - z.value == w.value - u.value - v.value + _e.value,
          x.value - v.value != _0.value,
          z.value + u.value == _pi.value,
          x.value * v.value == z.value)