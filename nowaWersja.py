import random

primitive_polynomial = 0x11D  # x^8 + x^4 + x^3 + x^2 + 1


addition_table = [[a ^ b for b in range(256)] for a in range(256)]
multiplication_table = [[0] * 256 for _ in range(256)]
exp_table = [0] * 256
log_table = [0] * 256


x = 1
for i in range(255):
    exp_table[i] = x
    log_table[x] = i
    x <<= 1
    if x & 0x100:
        x ^= primitive_polynomial
exp_table[255] = exp_table[0]


for a in range(256):
    for b in range(256):
        if a == 0 or b == 0:
            multiplication_table[a][b] = 0
        else:
            multiplication_table[a][b] = exp_table[(log_table[a] + log_table[b]) % 255]



def galois_add(a, b):
    return addition_table[a][b]



def galois_multiply(a, b):
    return multiplication_table[a][b]



class BCHCoder:
    minimal_polynomials = {
        0: [1, 1],  # m0
        1: [1, 0, 0, 0, 1, 1, 1, 0, 1],  # m1
        3: [1, 0, 1, 1, 1, 0, 1, 1, 1],  # m3
        5: [1, 1, 1, 1, 1, 0, 0, 1, 1],  # m5
        7: [1, 0, 1, 1, 0, 1, 0, 0, 1],  # m7
        9: [1, 1, 0, 1, 1, 1, 1, 0, 1],  # m9
        11: [1, 1, 1, 1, 0, 0, 1, 1, 1],  # m11
        13: [1, 0, 0, 1, 0, 1, 0, 1, 1],  # m13
        15: [1, 1, 1, 0, 1, 0, 1, 1, 1],  # m15
        17: [1, 0, 0, 1, 1],  # m17
        19: [1, 0, 1, 1, 0, 0, 1, 0, 1],  # m19
        21: [1, 1, 0, 0, 0, 1, 0, 1, 1],  # m21
    }

    def __init__(self, n, k):
        self.n = n
        self.k = k
        self.t = 11
        self.generator_polynomial = self.generate_generator_polynomial()

    def multiply_polynomials(self, poly1, poly2):
        result = [0] * (len(poly1) + len(poly2) - 1)
        for i, coef1 in enumerate(poly1):
            for j, coef2 in enumerate(poly2):
                result[i + j] ^= galois_multiply(coef1, coef2)
        return result

    def divide_polynomials(self, dividend, divisor):
        dividend = dividend[:]
        while len(dividend) >= len(divisor):
            degree_diff = len(dividend) - len(divisor)
            factor = dividend[-1]
            for i in range(len(divisor)):
                dividend[i + degree_diff] ^= galois_multiply(factor, divisor[i])
            while dividend and dividend[-1] == 0:
                dividend.pop()
        return dividend

    def generate_generator_polynomial(self):
        g = [1]
        for i in range(1, 2 * self.t + 1, 2):
            if i in self.minimal_polynomials:
                m = self.minimal_polynomials[i]
                g = self.multiply_polynomials(g, m)
        print("Wielomian generujacy:",g)
        return g

    def pad_and_split_message(self, message):
        last_k_bits = message[-self.k:]
        remaining_bits = message[:-self.k]
        padded_remaining_bits = [0] * (self.k - len(remaining_bits)) + remaining_bits
        return padded_remaining_bits, last_k_bits

    def encode(self, message):
        if len(message) != self.n:
            raise ValueError(f"The message must be exactly {self.n} bits.")

        part1, part2 = self.pad_and_split_message(message)
#czy to ma być tutaj dodawane, czy w sumie w którym momencie???????
        x84_m = part1 + part2
        remainder = self.divide_polynomials(x84_m, self.generator_polynomial)

        codeword = x84_m + [0] * (self.n - len(x84_m))
        for i in range(len(remainder)):
            codeword[i] ^= remainder[i]
        return codeword


n = 255
k = 171

bch = BCHCoder(n, k)


message = [random.randint(0, 1) for _ in range(n)]
print("Slowo kodowe:", message)

encoded_message = bch.encode(message)
print("Zakodowane:", encoded_message)
