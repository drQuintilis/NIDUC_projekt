class BCHCoder:
    # ... (previous code remains unchanged)

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
        # Ensure dividend is at least as long as divisor
        while len(dividend) >= len(divisor):
            degree_diff = len(dividend) - len(divisor)
            term = [0] * degree_diff + divisor
            dividend = [a ^ b for a, b in zip(dividend, term)]
            while dividend and dividend[-1] == 0:
                dividend.pop()
        print(f"Dividing: {dividend} by {divisor} gives remainder: {dividend}")  # Debugging line
        return dividend

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
            print(f"x^84 * m(x): {x84_m}")  # Debugging line

            # Divide by generator polynomial to get the remainder
            remainder = self.divide_polynomials(x84_m, self.generator_polynomial)

            # Form the final codeword c(x) = x^84 * m(x) + r(x)
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