# Copyright (c) 2012-2021 Oscar Riveros [https://twitter.com/maxtuno], All Rights Reserved.

import subprocess


class Encoder:
    def __init__(self, bit_depth, cnf_path):
        self.bit_depth = 4 * bit_depth
        self.number_of_variables = 0
        self.number_of_clauses = 0
        self.cnf_path = cnf_path
        self.cnf_file = open(self.cnf_path, 'w+')
        self.variables = []
        self.cbns = {
            0: '0000',
            1: '0001',
            2: '1100',
            3: '1101'
        }
        self.render = False

    def make_variable(self):
        self.number_of_variables += 1
        return self.number_of_variables

    def make_block(self):
        return [self.make_variable() for _ in range(self.bit_depth)]

    def make_clauses(self, clauses):
        for clause in clauses:
            print(' '.join(map(str, clause)) + ' 0', file=self.cnf_file)
            self.number_of_clauses += 1

    def make_constant(self, value):
        aux = abs(value)
        base_4 = []
        while aux:
            base_4.append((aux % 4))
            aux //= 4
        base_minus_4 = []
        for i in range(len(base_4)):
            if (len(base_4) - 1 - i) % 2 == 1:
                base_minus_4.append(-base_4[len(base_4) - 1 - i])
            else:
                base_minus_4.append(+base_4[len(base_4) - 1 - i])
        normalized = (self.bit_depth - len(base_minus_4)) * [0] + base_minus_4
        while sum([i < 0 or i == 4 for i in normalized]) != 0:
            for i in range(len(normalized)):
                if normalized[i] < 0:
                    normalized[i] += 4
                    normalized[i - 1] += 1
            for i in range(len(normalized)):
                if normalized[i] == 4:
                    normalized[i] = 0
                    normalized[i - 1] -= 1
        for i in range(len(normalized)):
            if normalized[i] != 0:
                normalized = normalized[i:]
                break
        binary = []
        for i in normalized:
            binary += [int(bit) for bit in self.cbns[i]]
        binary = (self.bit_depth - len(binary)) * [0] + binary
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
        for a, b in zip(self.block, other.block):
            self.encoder.apply_not(a, b)
        return self

    def __add__(self, other):
        output = Unit(self.encoder)
        seq = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
        x = self.encoder.make_variable()
        y = self.encoder.make_variable()
        z = self.encoder.make_variable()
        w = self.encoder.make_variable()
        self.encoder.make_clauses([[x], [y], [z], [w]])
        for i in range(self.encoder.bit_depth):
            self.encoder.apply_full_adder(seq[0] * self.block[i], seq[1] * other.block[i], x, seq[2] * output.block[i], x)
            self.encoder.apply_full_adder(seq[3] * self.block[i], seq[4] * other.block[i], y, seq[5] * output.block[i], y)
            self.encoder.apply_full_adder(seq[6] * self.block[i], seq[7] * other.block[i], z, seq[8] * output.block[i], z)
            self.encoder.apply_full_adder(seq[9] * self.block[i], seq[10] * other.block[i], w, seq[11] * output.block[i], w)
        return output

    def __sub__(self, other):
        output = Unit(self.encoder)
        seq = [1, -1, 1, 1, -1, 1, 1, -1, 1, 1, -1, 1]
        x = self.encoder.make_variable()
        y = self.encoder.make_variable()
        z = self.encoder.make_variable()
        w = self.encoder.make_variable()
        self.encoder.make_clauses([[x], [y], [z], [w]])
        for i in range(self.encoder.bit_depth):
            self.encoder.apply_full_adder(seq[0] * self.block[i], seq[1] * other.block[i], x, seq[2] * output.block[i], x)
            self.encoder.apply_full_adder(seq[3] * self.block[i], seq[4] * other.block[i], y, seq[5] * output.block[i], y)
            self.encoder.apply_full_adder(seq[6] * self.block[i], seq[7] * other.block[i], z, seq[8] * output.block[i], z)
            self.encoder.apply_full_adder(seq[9] * self.block[i], seq[10] * other.block[i], w, seq[11] * output.block[i], w)
        return output

    def __repr__(self):
        return str(self.value)


def cbns(binary):
    x = 0
    for i in range(len(binary)):
        x += binary[len(binary) - 1 - i] * complex(-1, 1) ** i
    return x


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
                    arg.value = cbns(binary)
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
