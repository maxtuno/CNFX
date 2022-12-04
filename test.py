import cnfx

enc = cnfx.Encoder(bit_depth=3, cnf_path='test.cnf')

c = cnfx.Unit(enc, value=3)
x = cnfx.Unit(enc)
y = cnfx.Unit(enc)
z = cnfx.Unit(enc)
w = cnfx.Unit(enc)
u = cnfx.Unit(enc)
v = cnfx.Unit(enc)

assert x + y - z == w - u - v + c

while cnfx.satisfy(encoder=enc, solver='kissat'):
    print(c.value, x.value, y.value, z.value, w.value, w.value, v.value,
          x.value + y.value - z.value == w.value - u.value - v.value + c.value)