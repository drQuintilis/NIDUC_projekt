# Define the Galois Field GF(2^8) parameters
# Primitive polynomial for GF(2^8): x^8 + x^4 + x^3 + x^2 + 1
primitive_polynomial = 0x11D  # This is the binary representation of the polynomial

# Precompute the logarithm and exponential tables for GF(2^8)
exp_table = [0] * 256
log_table = [0] * 256

x = 1
for i in range(255):
    exp_table[i] = x
    log_table[x] = i
    x <<= 1
    if x & 0x100:  # If x is greater than 255, reduce it
        x ^= primitive_polynomial

# Define addition in GF(2)
def galois_add(a, b):
    return a ^ b  # XOR for addition in GF(2)

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
        self.n = n  # Length of the codeword
        self.k = k  # Length of the message
        self.t = (n - k) // 2  # Error correction capability
        self.generator_polynomial = self.generate_generator_polynomial()

    @staticmethod
    def galois_multiply(a, b):
        if a == 0 or b == 0:
            return 0
        return exp_table[(log_table[a] + log_table[b]) % 255]

    def multiply_polynomials(self, poly1, poly2):
        """Multiply two polynomials in GF(2)."""
        result = [0] * (len(poly1) + len(poly2) - 1)
        for i, coef1 in enumerate(poly1):
            for j, coef2 in enumerate(poly2):
                result[i + j] ^= self.galois_multiply(coef1, coef2)
        print(f"Multiplying: {poly1} * {poly2} = {result}")  # Debugging line
        return result

    def divide_polynomials(self, dividend, divisor):
        """Divide two polynomials in GF(2) and return the remainder."""
        while len(dividend) >= len(divisor):
            degree_diff = len(dividend) - len(divisor)
            term = [0] * degree_diff + divisor
            dividend = [a ^ b for a, b in zip(dividend, term)]
            while dividend and dividend[-1] == 0:
                dividend.pop()
        print(f"Dividing: {dividend} by {divisor} gives remainder: {dividend}")  # Debugging line
        return dividend

    def generate_generator_polynomial(self):
        """Generate the generator polynomial for the BCH code."""
        g = [1]  # Start with the polynomial 1
        for i in range(1, 2 * self.t + 1, 2):  # Use only odd indices
            if i in self.minimal_polynomials:
                m = self.minimal_polynomials[i]
                g = self.multiply_polynomials(g, m)
        return g

    def encode(self, message):
        """Encode the message using the BCH coding scheme."""
        if len(message) != self.k:
            raise ValueError(f"The message must be exactly {self.k} bits.")

        padded_message = [0] * (self.k - len(message)) + message

        chunks = []
        for i in range(0, len(padded_message), self.k):
            chunk = padded_message[i:i + self.k]
            if len(chunk) < self.k:
                chunk = [0] * (self.k - len(chunk)) + chunk
            chunks.append(chunk)

        codewords = []
        for chunk in chunks:
            x84_m = [0] * 84 + chunk
            print(f"x^84 * m(x): {x84_m}")  # Debugging line

            remainder = self.divide_polynomials(x84_m, self.generator_polynomial)

            codeword = [(a ^ b) for a, b in zip(x84_m, remainder + [0] * (len(x84_m) - len(remainder)))]
            print(f"Codeword: {codeword}")  # Debugging line
            codewords.append(codeword)

        return codewords

# Parameters
n = 255
k = 171

# Create BCHCoder object
bch = BCHCoder(n, k)

# Encode a message of ones
message = [1] * k  # Message to encode
encoded_message = bch.encode(message)
print("Encoded message:", encoded_message)