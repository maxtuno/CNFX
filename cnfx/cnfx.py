# Copyright (c) 2012-2021 Oscar Riveros [https://twitter.com/maxtuno], All Rights Reserved.

import subprocess


class Encoder:
    def __init__(self, bit_depth, cnf_path):
        self.bit_depth = 4 * bit_depth
        self.float_dot = self.bit_depth
        self.number_of_variables = 0
        self.number_of_clauses = 0
        self.cnf_path = cnf_path
        self.cnf_file = open(self.cnf_path, 'w+')
        self.variables = []
        self.cbns_encoder = {
            0: '0000',
            1: '0001',
            2: '1100',
            3: '1101'
        }
        self.render = False

    @staticmethod
    def cbns(binary):
        x = 0
        for i in range(len(binary)):
            x += binary[i] * complex(-1, 1) ** (len(binary) // 2 - i - 1)
        # print(x, binary)
        return x

    def make_variable(self):
        self.number_of_variables += 1
        return self.number_of_variables

    def make_block(self):
        return [self.make_variable() for _ in range(4 * (self.bit_depth + self.float_dot))]

    def make_clause(self, clause):
        print(' '.join(map(str, clause)) + ' 0', file=self.cnf_file)
        self.number_of_clauses += 1

    def make_clauses(self, clauses):
        for clause in clauses:
            self.make_clause(clause)

    def make_constant(self, value):
        aux_integer = int(value)
        aux_float = float(value - aux_integer)
        base_4_integer = []
        for _ in range(self.bit_depth):
            base_4_integer.append(aux_integer % 4)
            aux_integer //= 4
        base_4_float = []
        for _ in range(self.float_dot):
            aux_float *= 4
            bit = int(aux_float)
            base_4_float.append(bit)
            aux_float -= bit
        base_4_float.reverse()
        base_4 = base_4_float + base_4_integer
        base_minus_4 = []
        for i in range(len(base_4)):
            if (len(base_4) - 1 - i) % 2 == 1:
                base_minus_4.append(-base_4[len(base_4) - 1 - i])
            else:
                base_minus_4.append(+base_4[len(base_4) - 1 - i])
        normalized = base_minus_4
        while sum([i < 0 or i == 4 for i in normalized]) != 0:
            for i in range(len(normalized)):
                if normalized[i] < 0:
                    normalized[i] += 4
                    normalized[i - 1] += 1
            for i in range(len(normalized)):
                if normalized[i] == 4:
                    normalized[i] = 0
                    normalized[i - 1] -= 1
        normalized = (self.bit_depth + self.float_dot - len(normalized)) * [0] + normalized
        binary = []
        for i in normalized:
            binary += [int(bit) for bit in self.cbns_encoder[i]]
        block = []
        for bit in binary:
            block.append(self.make_variable())
            if bit == 0:
                self.make_clauses([[-block[-1]]])
            else:
                self.make_clauses([[+block[-1]]])
        return block

    def apply_not(self, a, b):
        self.make_clauses([[a, b],
                           [-a, -b]])

    def apply_copy(self, a, b):
        self.make_clauses([[a, -b],
                           [-a, b]])

    def apply_and(self, a, b, c):
        self.make_clauses([[a, b, -c],
                           [a, -b, -c],
                           [-a, b, -c],
                           [-a, -b, c]])

    def apply_nand(self, a, b, c):
        self.make_clauses([[a, b, c],
                           [a, -b, c],
                           [-a, b, c],
                           [-a, -b, -c]])

    def apply_or(self, a, b, c):
        self.make_clauses([[a, b, -c],
                           [a, -b, c],
                           [-a, b, c],
                           [-a, -b, c]])

    def apply_nor(self, a, b, c):
        self.make_clauses([[a, b, c],
                           [a, -b, -c],
                           [-a, b, -c],
                           [-a, -b, -c]])

    def apply_xor(self, a, b, c):
        self.make_clauses([[a, b, -c],
                           [a, -b, c],
                           [-a, b, c],
                           [-a, -b, -c]])

    def apply_xnor(self, a, b, c):
        self.make_clauses([[a, b, c],
                           [a, -b, -c],
                           [-a, b, -c],
                           [-a, -b, c]])

    def apply_half_adder(self, a, b, s, c):
        self.apply_xor(a, b, s)
        self.apply_and(a, b, c)

    def apply_full_adder(self, a, b, ci, s, co):
        x = self.make_variable()
        y = self.make_variable()
        z = self.make_variable()
        self.apply_half_adder(a, b, x, y)
        self.apply_half_adder(ci, x, s, z)
        self.apply_or(y, z, co)

    def apply_multiplier(self, a0, a1, b0, b1, c0, c1, c2, c3):
        s1 = self.make_variable()
        s2 = self.make_variable()
        s3 = self.make_variable()
        s4 = self.make_variable()
        self.apply_and(a0, b0, c0)
        self.apply_and(a1, b0, s1)
        self.apply_and(a0, b1, s2)
        self.apply_and(a1, b1, s3)
        self.apply_half_adder(s1, s2, c1, s4)
        self.apply_half_adder(s3, s4, c2, c3)

    def binary_or(self, ab, ol=None):
        if ol is None:
            ol = self.make_variable()
        a, b = ab
        self.make_clause([a, b, -ol])
        self.make_clause([-a, b, ol])
        self.make_clause([a, -b, ol])
        self.make_clause([-a, -b, ol])
        return ol

    def binary_and(self, ab, ol=None):
        if ol is None:
            ol = self.make_variable()
        a, b = ab
        self.make_clause([a, b, -ol])
        self.make_clause([-a, b, -ol])
        self.make_clause([a, -b, -ol])
        self.make_clause([-a, -b, ol])
        return ol

    def or_gate(self, il, ol=None):
        if ol is None:
            ol = self.make_variable()
        fc = list(il)
        fc.append(-ol)
        self.make_clause(fc)
        for lit in il:
            self.make_clause([-lit, ol])
        return ol

    def and_gate(self, il, ol=None):
        if ol is None:
            ol = self.make_variable()
        fc = [-b for b in il]
        fc.append(ol)
        self.make_clause(fc)
        for lit in il:
            self.make_clause([lit, -ol])
        return ol

    def binary_xor_gate(self, il, ol=None):
        if ol is None:
            ol = self.make_variable()
        l1, l2 = il[0], il[1]
        self.make_clause([l1, l2, -ol])
        self.make_clause([-l1, -l2, -ol])
        self.make_clause([l1, -l2, ol])
        self.make_clause([-l1, l2, ol])
        return ol

    def binary_xnor_gate(self, il, ol=None):
        if ol is None:
            ol = self.make_variable()
        l1, l2 = il[0], il[1]
        self.make_clause([l1, l2, ol])
        self.make_clause([-l1, -l2, ol])
        self.make_clause([l1, -l2, -ol])
        self.make_clause([-l1, l2, -ol])
        return ol

    def binary_mux_gate(self, il, ol=None):
        if ol is None:
            ol = self.make_variable()
        sel, lhs, rhs = il[0], il[1], il[2]
        self.make_clause([sel, lhs, -ol])
        self.make_clause([sel, -lhs, ol])
        self.make_clause([-sel, rhs, -ol])
        self.make_clause([-sel, -rhs, ol])
        return ol

    def fas_gate(self, il, ol=None):
        if ol is None:
            ol = self.make_variable()
        lhs, rhs, c_in = il
        self.make_clause([lhs, rhs, c_in, -ol])
        self.make_clause([lhs, -rhs, -c_in, -ol])
        self.make_clause([lhs, -rhs, c_in, ol])
        self.make_clause([lhs, rhs, -c_in, ol])
        self.make_clause([-lhs, rhs, c_in, ol])
        self.make_clause([-lhs, -rhs, -c_in, ol])
        self.make_clause([-lhs, -rhs, c_in, -ol])
        self.make_clause([-lhs, rhs, -c_in, -ol])
        return ol

    def fac_gate(self, il, ol=None):
        if ol is None:
            ol = self.make_variable()
        lhs, rhs, c_in = il
        self.make_clause([lhs, rhs, -ol])
        self.make_clause([lhs, c_in, -ol])
        self.make_clause([lhs, -rhs, -c_in, ol])
        self.make_clause([-lhs, rhs, c_in, -ol])
        self.make_clause([-lhs, -rhs, ol])
        self.make_clause([-lhs, -c_in, ol])
        return ol

    @staticmethod
    def gate_vector(bge, lhs_il, rhs_il, ol=None):
        if ol is None:
            ol = [None] * len(lhs_il)
        return [bge((lhs, rhs), ol) for lhs, rhs, ol in zip(lhs_il, rhs_il, ol)]

    def bv_and_gate(self, lhs_il, rhs_il, ol=None):
        ol = self.gate_vector(self.binary_and, lhs_il, rhs_il, ol)
        return ol

    def bv_or_gate(self, lhs_il, rhs_il, ol=None):
        return self.gate_vector(self.binary_or, lhs_il, rhs_il, ol)

    def bv_xor_gate(self, lhs_il, rhs_il, ol=None):
        return self.gate_vector(self.binary_xor_gate, lhs_il, rhs_il, ol)

    def bv_xnor_gate(self, lhs_il, rhs_il, ol=None):
        return self.gate_vector(self.binary_xnor_gate, lhs_il, rhs_il, ol)

    def bv_rca_gate(self, lhs_il, rhs_il, carry_in_lit=None, ol=None, carry_out_lit=None):
        wt = min(len(lhs_il), len(rhs_il))
        if wt == 0:
            return []
        if ol is None:
            ol = [self.make_variable() for _ in range(0, wt)]
        ol = [o if o is not None else self.make_variable() for o in ol]
        crr = [self.make_variable() for _ in range(0, wt - 1)]
        crr.append(carry_out_lit)
        if carry_in_lit is not None:
            adi = (lhs_il[0], rhs_il[0], carry_in_lit)
            self.fas_gate(adi, ol[0])
            if crr[0] is not None:
                self.fac_gate(adi, crr[0])
        else:
            adi = (lhs_il[0], rhs_il[0])
            self.binary_xor_gate(adi, ol[0])
            if crr[0] is not None:
                self.and_gate(adi, crr[0])
        for i in range(1, wt):
            adi = (lhs_il[i], rhs_il[i], crr[i - 1])
            self.fas_gate(adi, ol[i])
            if crr[i] is not None:
                self.fac_gate(adi, crr[i])
        return ol

    def bv_pm_gate(self, lhs_il, rhs_il, ol=None, ow_lit=None):
        wt = len(lhs_il)
        if wt == 0:
            return []

        def __cfl(n):
            return [self.make_variable() for _ in range(0, n)]

        if ol is None:
            ol = __cfl(wt)
        else:
            ol = list(
                map(lambda l: self.make_variable() if l is None else l, ol))
        pp = [[ol[0]] + __cfl(wt - 1)]
        l_lhs = lhs_il[0]
        self.bv_and_gate(rhs_il, [l_lhs] * wt, pp[0])
        if ow_lit is not None:
            pp += [self.bv_and_gate(rhs_il, [l] * wt) for l in lhs_il[1:]]
        else:
            pp += [self.bv_and_gate(rhs_il[0:wt - i], [lhs_il[i]] * (wt - i)) for i in range(1, wt)]
        partial_sums = [([ol[i]] + __cfl(wt - i - 1)) for i in range(1, wt)]
        csc = __cfl(wt - 1) if ow_lit is not None else [None] * (wt - 1)
        cps = pp[0][1:wt]
        for i in range(1, wt):
            cpp = pp[i][0:wt - i]
            psa = partial_sums[i - 1]
            assert len(cps) == wt - i
            self.bv_rca_gate(lhs_il=cps, rhs_il=cpp, ol=psa, carry_out_lit=csc[i - 1])
            cps = psa[1:]
        if ow_lit is not None:
            ow = csc[:]
            for i in range(1, wt):
                ow += pp[i][wt - i:wt]
            self.or_gate(ow, ow_lit)
        return ol


class Unit:
    def __init__(self, encoder, value=None):
        self.value = value
        self.encoder = encoder
        if self.value is not None:
            self.block = self.encoder.make_constant(self.value)
        else:
            self.block = self.encoder.make_block()
        encoder.variables.append(self)

    def __eq__(self, other):
        if not isinstance(other, Unit):
            other = Unit(self.encoder, value=other)
        z = self.encoder.make_variable()
        self.encoder.make_clauses([[z]])
        xs = []
        for a, b in zip(self.block, other.block):
            x = self.encoder.make_variable()
            xs.append(x)
            self.encoder.apply_xnor(a, b, x)
        xs.append(z)
        self.encoder.make_clauses([xs])
        for x in xs:
            self.encoder.make_clauses([[x, -z]])
        return self

    def __ne__(self, other):
        if not isinstance(other, Unit):
            other = Unit(self.encoder, value=other)
        z = self.encoder.make_variable()
        self.encoder.make_clauses([[z]])
        xs = []
        for a, b in zip(self.block, other.block):
            x = self.encoder.make_variable()
            xs.append(x)
            self.encoder.apply_xor(a, b, x)
        xs.append(-z)
        self.encoder.make_clauses([xs])
        for x in xs:
            self.encoder.make_clauses([[-x, z]])
        return self

    def __add__(self, other):
        if not isinstance(other, Unit):
            other = Unit(self.encoder, value=other)
        output = Unit(self.encoder)
        x = self.encoder.make_variable()
        self.encoder.make_clauses([[x]])
        for i in range(4 * (self.encoder.bit_depth + self.encoder.float_dot)):
            self.encoder.apply_full_adder(-self.block[i], -other.block[i], x, -output.block[i], x)
        return output

    def __sub__(self, other):
        if not isinstance(other, Unit):
            other = Unit(self.encoder, value=other)
        output = Unit(self.encoder)
        x = self.encoder.make_variable()
        self.encoder.make_clauses([[x]])
        for i in range(4 * (self.encoder.bit_depth + self.encoder.float_dot)):
            self.encoder.apply_full_adder(+self.block[i], -other.block[i], x, +output.block[i], x)
        return output

    def __rsub__(self, other):
        if not isinstance(other, Unit):
            other = Unit(self.encoder, value=other)
        return other.__sub__(self)

    def __mul__(self, other):
        if not isinstance(other, Unit):
            other = Unit(self.encoder, value=other)
        output = Unit(self.encoder)
        x = self.encoder.make_variable()
        self.encoder.make_clauses([[-x]])
        a0, a1 = self.block[len(self.block) // 2:], self.block[:len(self.block) // 2]
        b0, b1 = other.block[len(self.block) // 2:], other.block[:len(self.block) // 2]
        c0, c1 = output.block[len(self.block) // 2 + 1:], output.block[:len(self.block) // 2 + 1]
        self.encoder.bv_pm_gate(a0 + a1, b0 + b1, c0 + c1, x)
        return output

    def __rmul__(self, other):
        return self.__mul__(other)

    def __and__(self, other):
        if not isinstance(other, Unit):
            other = Unit(self.encoder, value=other)
        output = Unit(self.encoder)
        for a, b, c in zip(self.block, other.block, output.block):
            self.encoder.apply_and(a, b, c)
        return output

    def __or__(self, other):
        if not isinstance(other, Unit):
            other = Unit(self.encoder, value=other)
        output = Unit(self.encoder)
        for a, b, c in zip(self.block, other.block, output.block):
            self.encoder.apply_or(a, b, c)
        return output

    def __xor__(self, other):
        if not isinstance(other, Unit):
            other = Unit(self.encoder, value=other)
        output = Unit(self.encoder)
        for a, b, c in zip(self.block, other.block, output.block):
            self.encoder.apply_xor(a, b, c)
        return output

    def __lshift__(self, other):
        if other == 0:
            return self
        output = Unit(self.encoder)
        for i in range(len(output.block)):
            self.encoder.apply_copy(self.block[i], output.block[i - other])
        return output

    def __rshift__(self, other):
        if other == 0:
            return self
        output = Unit(self.encoder)
        for i in range(len(output.block)):
            self.encoder.apply_copy(self.block[i], output.block[(i + other) % len(output.block)])
        return output

    def __radd__(self, other):
        return self + other

    def __repr__(self):
        return str(self.value)


def satisfy(encoder, solver, params='', log=False):
    key = encoder.cnf_path[:encoder.cnf_path.index('.')]
    if not encoder.render:
        encoder.render = True
        encoder.cnf_file = open(encoder.cnf_path, 'r+')
        header = 'p cnf {} {}'.format(encoder.number_of_variables, encoder.number_of_clauses)
        content = encoder.cnf_file.read()
        encoder.cnf_file.seek(0, 0)
        encoder.cnf_file.write(header.rstrip('\r\n') + '\n' + content)
        encoder.cnf_file.close()
    with open('{}.mod'.format(key), 'w', encoding="utf8", errors='ignore') as file:
        proc = subprocess.Popen('{0} {1}.cnf {2}'.format(solver, key, params), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for stdout_line in iter(proc.stdout.readline, ''):
            if not stdout_line:
                break
            try:
                line = stdout_line.decode()
                file.write(line)
                if log:
                    print(line, end='')
            except:
                pass
        proc.stdout.close()
    with open('{}.mod'.format(key), 'r') as mod:
        lines = ''
        for line in mod.readlines():
            if line.startswith('v '):
                lines += line.strip('v ').strip('\n') + ' '
        if len(lines) > 0:
            model = list(map(int, lines.strip(' ').split(' ')))
            for arg in encoder.variables:
                if isinstance(arg, Unit):
                    binary = [int(int(model[abs(bit) - 1]) > 0) for bit in arg.block]
                    arg.value = arg.encoder.cbns(binary)
            with open(encoder.cnf_path, 'a') as file:
                file.write(' '.join([str(-int(literal)) for literal in model]) + '\n')
                encoder.number_of_clauses += 1
            encoder.cnf_file = open(encoder.cnf_path, 'r+')
            header = 'p cnf {} {}'.format(encoder.number_of_variables, encoder.number_of_clauses)
            content = encoder.cnf_file.read()
            encoder.cnf_file.seek(0, 0)
            encoder.cnf_file.write(header.rstrip('\r\n') + '\n' + content[content.index('\n'):])
            encoder.cnf_file.close()
            return True
    return False
