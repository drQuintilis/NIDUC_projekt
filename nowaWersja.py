import random

class BCHCoder:
    minimal_polynomials = {
        1: [1, 0, 0, 0, 1, 1, 1, 0, 1],  # m1
        3: [1, 0, 1, 1, 1, 0, 1, 1, 1],  # m3
        5: [1, 1, 1, 1, 1, 0, 0, 1, 1],  # m5
        7: [1, 0, 1, 1, 0, 1, 0, 0, 1],  # m7
        9: [1, 1, 0, 1, 1, 1, 1, 0, 1],  # m9
        11: [1, 1, 1, 1, 0, 0, 1, 1, 1],  # m11
        13: [1, 0, 0, 1, 0, 1, 0, 1, 1],
        15: [1, 1, 1, 0, 1, 0, 1, 1, 1],
        17: [1, 0, 0, 1, 1],
        19: [1, 0, 1, 1, 0, 0, 1, 0, 1],
        21: [1, 1, 0, 0, 0, 1, 0, 1, 1],  # 1
    }

    def __init__(self, n, k, t):
        self.n = n  # Długość słowa kodowego (n = 255)
        self.k = k  # Długość wiadomości informacyjnej (k = 171)
        self.t = t  # Zdolność korekcyjna (t = 11)
        self.generator_polynomial = self.generate_generator_polynomial()

    def galois_multiply(self, a, b):
        """Mnożenie w ciele Galois GF(2^8)."""
        if a == 0 or b == 0:
            return 0
        return exp_table[(log_table[a] + log_table[b]) % 255]

    def multiply_polynomials(self, poly1, poly2):
        """Mnoży dwa wielomiany w ciele GF(2)."""
        result = [0] * (len(poly1) + len(poly2) - 1)
        for i, coef1 in enumerate(poly1):
            for j, coef2 in enumerate(poly2):
                result[i + j] ^= self.galois_multiply(coef1, coef2)
        return result

    def compute_remainder(self, dividend, divisor):
        """Oblicza resztę z dzielenia wielomianów w ciele GF(2)."""
        dividend = dividend[:]  # Tworzymy kopię listy dividend

        # Proces dzielenia
        while len(dividend) >= len(divisor):
            # Jeśli najwyższy bit dividend jest 1, to wykonujemy operację XOR
            if dividend[0] == 1:
                for i in range(len(divisor)):
                    dividend[i] ^= divisor[i]  # Operacja XOR (mod 2)

            # Przesuwamy dividend (pozbywamy się wiodących zer)
            dividend.pop(0)

        # Zwracamy resztę, uzupełniając ją do 84 bitów, jeśli potrzeba
        remainder = dividend + [0] * (84 - len(dividend))  # Uzupełniamy do 84 bitów
        return remainder

    def generate_generator_polynomial(self):
        """Generuje wielomian generujący na podstawie funkcji minimalnych."""
        g = [1]
        for i in range(1, 2 * self.t + 1, 2):
            if i in self.minimal_polynomials:
                m = self.minimal_polynomials[i]
                g = self.multiply_polynomials(g, m)
        print("Wielomian generujący:", g)
        return g

    def encode(self, message):
        """Koduje wiadomość wejściową, dodając bity kontrolne."""
        if len(message) != 171:
            raise ValueError(f"Message must be exactly 171 bits.")

        # Przesunięcie o (n - k) pozycji
        padded_message = message + [0] * 84

        # Obliczenie reszty (bitów kontrolnych)
        remainder = self.compute_remainder(padded_message, self.generator_polynomial)

        # Dodanie reszty (bitów kontrolnych) do przesuniętego wielomianu
        for i in range(84):
            padded_message[171 + i] = remainder[i]

        return padded_message

    def validate_codeword(self, codeword):
        """Sprawdza, czy zakodowane słowo kodowe jest poprawne."""
        remainder = self.compute_remainder(codeword, self.generator_polynomial)
        ifCorrect = True
        for i in range(84):
            if remainder[i] != 0:
                ifCorrect = False
        return ifCorrect


# Przygotowanie ciała Galois GF(2^8)
primitive_polynomial = 0x11D  # x^8 + x^4 + x^3 + x^2 + 1
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

# Parametry kodu BCH
n = 255
k = 171
t = 11

# Inicjalizacja kodera BCH
bch = BCHCoder(n, k, t)

# Generowanie losowej wiadomości
message = [random.randint(0, 1) for _ in range(171)]
print("Wiadomość:", message)

# Kodowanie wiadomości
encoded_message = bch.encode(message)
print("Zakodowana wiadomość:", encoded_message)

# Sprawdzenie poprawności słowa kodowego
if bch.validate_codeword(encoded_message):
    print("Słowo kodowe jest poprawne.")
else:
    print("Słowo kodowe jest niepoprawne.")
