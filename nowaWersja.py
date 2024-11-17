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
    def __init__(self, n, k, minimal_polynomials):
        self.n = n  # Length of the codeword
        self.k = k  # Length of the message
        self.t = (n - k) // 2  # Error correction capability
        self.minimal_polynomials = minimal_polynomials
        self.generator_polynomial = self.generate_generator_polynomial()

    def multiply_polynomials(self, poly1, poly2):
        """Multiply two polynomials in GF(2)."""
        result = [0] * (len(poly1) + len(poly2) - 1)
        for i, coef1 in enumerate(poly1):
            for j, coef2 in enumerate(poly2):
                result[i + j] ^= galois_multiply(coef1, coef2)
        return result

    def divide_polynomials(self, dividend, divisor):
        """Divide two polynomials in GF(2) and return the remainder."""
        # Ensure dividend is at least as long as divisor
        while len(dividend) >= len(divisor):
            # Find the degree of the leading term
            degree_diff = len(dividend) - len(divisor)
            # Create a term to subtract
            term = [0] * degree_diff + divisor
            # Subtract (XOR) the divisor from the dividend
            dividend = [a ^ b for a, b in zip(dividend, term)]
            # Remove leading zeros
            while dividend and dividend[-1] == 0:
                dividend.pop()
        return dividend

    def generate_generator_polynomial(self):
        """Generate the generator polynomial as the product of minimal polynomials."""
        generator_poly = [1]  # Initial polynomial: 1
        for i in range(1, 2 * self.t + 1, 2):  # Use m1, m3, ..., m21
            if i in self.minimal_polynomials:  # Check for existence of key
                generator_poly = self.multiply_polynomials(generator_poly, self.minimal_polynomials[i])
        return generator_poly

    def encode(self, message):
        """Encode the message using the BCH coding scheme."""
        if len(message) != self.k:
            raise ValueError(f"The message must be exactly {self.k} bits.")

        # Pad the message to the left with zeros to make it 171 bits
        padded_message = [0] * (self.k - len(message)) + message

        # Split the padded message into chunks of 171 bits
        chunks = []
        for i in range(0, len(padded_message), self.k):
            chunk = padded_message[i:i + self.k]
            if len(chunk) < self.k:
                chunk = [0] * (self.k - len(chunk)) + chunk  # Pad with zeros on the left
            chunks.append(chunk)

        codewords = []
        for chunk in chunks:
            # Multiply by x^84
            x84_m = [0] * 84 + chunk  # x^84 * m(x)

            # Divide by generator polynomial to get the remainder
            remainder = self.divide_polynomials(x84_m, self.generator_polynomial)

            # Form the final codeword c(x) = x^84 * m(x) + r(x)
            codeword = [(a ^ b) for a, b in zip(x84_m, remainder + [0] * (len(x84_m) - len(remainder)))]
            codewords.append(codeword)

        return codewords

# Parameters
n = 255
k = 171

# Create BCHCoder object
bch = BCHCoder(n, k, minimal_polynomials)

# Encode a message of ones
message = [1] * k  # Message to encode
encoded_message = bch.encode(message)
print("Encoded message:", encoded_message)

