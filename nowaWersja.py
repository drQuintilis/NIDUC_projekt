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
        21: [1, 1, 0, 0, 0, 1, 0, 1, 1],
    }

    def __init__(self, n, k, t):
        self.n = n
        self.k = k
        self.t = t
        self.generator_polynomial = self.generate_generator_polynomial()

    def multiply_polynomials(self, poly1, poly2):
        result = [0] * (len(poly1) + len(poly2) - 1)
        for i, coef1 in enumerate(poly1):
            for j, coef2 in enumerate(poly2):
                result[i + j] ^= coef1 & coef2  # XOR (mod 2)
        return result

    def compute_remainder(self, dividend, divisor):
        dividend = dividend[:]
        while len(dividend) >= len(divisor):
            if dividend[0] == 1:
                for i in range(len(divisor)):
                    dividend[i] ^= divisor[i]
            dividend.pop(0)
        return dividend

    def generate_generator_polynomial(self):
        g = [1]
        for i in range(1, 2 * self.t + 1, 2):
            if i in self.minimal_polynomials:
                m = self.minimal_polynomials[i]
                g = self.multiply_polynomials(g, m)
        print("Wielomian generujący:", g)
        return g

    def encode(self, message):
        if len(message) != self.k:
            raise ValueError(f"Message must be exactly {self.k} bits.")
        padded_message = message + [0] * (self.n - self.k)
        remainder = self.compute_remainder(padded_message, self.generator_polynomial)
        encoded_message = message + remainder
        return encoded_message

    def validate_codeword(self, codeword):
        remainder = self.compute_remainder(codeword, self.generator_polynomial)
        return all(bit == 0 for bit in remainder)

    def highlight_errors(self, codeword, error_positions):
        """Funkcja pomocnicza do kolorowania błędnych pozycji na czerwono."""
        colored_codeword = ""
        for i in range(len(codeword)):
            if i in error_positions:
                colored_codeword += f"\033[91m{codeword[i]}\033[0m"  # Czerwony kolor dla błędu
            else:
                colored_codeword += str(codeword[i])
            if i < len(codeword) - 1:
                colored_codeword += ', '  # Dodanie przecinka między bitami
        return colored_codeword

    def decode_with_error_correction(self, received_codeword):
        shifts = 0
        max_shifts = len(received_codeword)  # Zabezpieczenie przed nieskończonym przesuwaniem

        while shifts < max_shifts:
            # Oblicz syndrom
            syndrome = self.compute_remainder(received_codeword, self.generator_polynomial)
            weight = sum(syndrome)  # Waga syndromu (liczba jedynek)

            # Jeśli waga syndromu <= t, dokonaj korekcji
            if weight <= self.t:
                print("Waga syndromu <= t. Rozpoczynam korekcję.")
                print("Przesunięcie:", shifts)
                for i in range(len(syndrome)):
                    received_codeword[-len(syndrome) + i] ^= syndrome[i]  # Odejmowanie syndromu (XOR)

                # Przywróć pierwotną postać przez przesunięcie w lewo
                for _ in range(shifts):
                    received_codeword = received_codeword[1:] + [received_codeword[0]]
                return received_codeword

            # Waga syndromu > t, przesuwamy w prawo
            received_codeword = [received_codeword[-1]] + received_codeword[:-1]
            shifts += 1

        # Jeśli nie można poprawić, zgłoś błąd
        raise ValueError("Błędy są niekorygowalne.")

    def recover_original_message(self, decoded_codeword):
        """
        Odnajduje pierwotną wiadomość przez dzielenie poprawionego kodu przez wielomian generujący.

        Argumenty:
            decoded_codeword (list[int]): Poprawiony wektor kodowy BCH (n bitów).

        Zwraca:
            list[int]: Pierwotna wiadomość (k bitów).
        """
        if len(decoded_codeword) != self.n:
            raise ValueError(f"Poprawiony kod musi mieć dokładnie {self.n} bitów.")

        # Podziel kod przez wielomian generujący
        remainder = self.compute_remainder(decoded_codeword, self.generator_polynomial)
        if any(remainder):
            raise ValueError("Kod nie jest wielokrotnością wielomianu generującego.")

        # Wyciągnij pierwsze k bitów jako oryginalną wiadomość
        original_message = decoded_codeword[:self.k]
        return original_message



n = 255
k = 171
t = 11

# Inicjalizacja kodera BCH
bch = BCHCoder(n, k, t)

# Generowanie losowej wiadomości
message = [random.randint(0, 1) for _ in range(k)]
print("Wiadomość:", message)

# Kodowanie wiadomości
encoded_message = bch.encode(message)
print("Zakodowana wiadomość:", encoded_message)
if bch.validate_codeword(encoded_message):
    print("Słowo kodowe jest poprawne.")
else:
    print("Słowo kodowe jest niepoprawne.")
# Symulacja błędu (dodanie jednego błędu na losowej pozycji)
received_message = encoded_message[:]
error_position = random.randint(0, n - 1)
received_message[error_position] ^= 1
print(f"Odebrana wiadomość z błędem na pozycji {error_position}:")
highlighted_received_message = bch.highlight_errors(received_message, [error_position])
print("                     [", highlighted_received_message, "]")

# Dekodowanie wiadomości z korekcją błędów
try:
    corrected_codeword = bch.decode_with_error_correction(received_message)
    print("Poprawiony kod:      ", corrected_codeword)

    # Odzyskiwanie pierwotnej wiadomości
    original_message = bch.recover_original_message(corrected_codeword)
    print("Oryginalna wiadomość:", original_message)

    # Porównanie z pierwotną wiadomością
    if message == original_message:
        print("Odzyskano pierwotną wiadomość poprawnie!")
    else:
        print("Odzyskana wiadomość nie zgadza się z oryginalną.")
except ValueError as e:
    print("Błąd dekodowania:", e)
