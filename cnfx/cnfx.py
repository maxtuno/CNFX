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
        return x

    def make_variable(self):
        self.number_of_variables += 1
        return self.number_of_variables

    def make_block(self):
        return [self.make_variable() for _ in range(4 * (self.bit_depth + self.float_dot))]

    def make_clauses(self, clauses):
        for clause in clauses:
            print(' '.join(map(str, clause)) + ' 0', file=self.cnf_file)
            self.number_of_clauses += 1

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
        for a, b in zip(self.block, other.block):
            self.encoder.apply_copy(a, b)
        return self

    def __ne__(self, other):
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
            self.encoder.make_clauses([[x, z]])
        return self

    def __add__(self, other):
        output = Unit(self.encoder)
        x = self.encoder.make_variable()
        self.encoder.make_clauses([[x]])
        for i in range(4 * (self.encoder.bit_depth + self.encoder.float_dot)):
            self.encoder.apply_full_adder(-self.block[i], -other.block[i], x, -output.block[i], x)
        return output

    def __sub__(self, other):
        output = Unit(self.encoder)
        x = self.encoder.make_variable()
        self.encoder.make_clauses([[x]])
        for i in range(4 * (self.encoder.bit_depth + self.encoder.float_dot)):
            self.encoder.apply_full_adder(+self.block[i], -other.block[i], x, +output.block[i], x)
        return output

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
