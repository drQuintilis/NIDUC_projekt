import json
import random

import pandas as pd
from progressbar import progressbar

class EncodingError(Exception):
    pass

class MessagesNotMatchError(Exception):
    pass

class MessageUnfixableError(Exception):
    pass

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
        raise MessageUnfixableError("Błędy są niekorygowalne.")

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

def error_generator_random(n, errors_amount):
    errors_array = []
    for i in range(errors_amount):
        while len(errors_array) < i + 1:
            error_position = random.randint(0, n - 1)
            if error_position in errors_array:
                continue
            errors_array.append(error_position)
    return errors_array

def error_generator_burst(n, errors_amount):
    errors_array = []
    error_position = random.randint(0, n - 1)
    for i in range(errors_amount):
        errors_array.append((error_position+i) % n)
    return errors_array

def error_flip(message, position):
    message[position] ^= 1

def error_to_high(message, position):
    message[position] = 1

def error_to_low(message, position):
    message[position] = 0


def decoder_test(bch, errors_amount, error_generator, error_type=error_flip):
    # Generowanie losowej wiadomości
    message = [random.randint(0, 1) for _ in range(k)]
    # Kodowanie wiadomości
    encoded_message = bch.encode(message)
    if not bch.validate_codeword(encoded_message):
        raise EncodingError("Niepoprawny kod.")
    # Symulacja błędu (dodanie jednego błędu na losowej pozycji)
    received_message = encoded_message[:]
    errors_array = error_generator(n, errors_amount)
    for error_position in errors_array:
        error_type(received_message, error_position)
    corrected_codeword = bch.decode_with_error_correction(received_message)
    original_message = bch.recover_original_message(corrected_codeword)
    if message != original_message:
        raise MessagesNotMatchError("Odzyskana wiadomość nie zgadza się z oryginalną.")

def write_to_excel(data, file_name):
    #Zapisywanie tabelę do pliku Excel
    df = pd.DataFrame.from_dict(data)
    df = df.transpose()
    df.to_excel(file_name, index=False, header=True)
    print(f"Tablica została zapisana do {file_name}")


test_suite = [
    # Losowe błędy z odwróceniem bitów
    {
        'name': 'Random errors',
        'error_generator': error_generator_random,
        'error_type': error_flip,
        'error_config': {
            1: 255,   # 50 testów dla 1 błędu
            2:1000,   # 60 testów dla 2 błędów
            3: 1000,
            4: 1000,
            5: 1000,
            6: 1000,
            7:1000,
            8:1000,
            9:1000,
            10:1000,
            11:1000,
            12: 1000, # 100 testów dla 12 błędów
            30: 200, # 200 testów dla 30 błędów
        }
    },
    # Wiązka wysokich błędów
    {
        'name': 'Burst high errors',
        'error_generator': error_generator_burst,
        'error_type': error_to_high,
        'error_config': {
            1:255,
            2: 254,
            3: 253,
            4: 252,
            5: 251,
            6: 250,
            7: 249,
            8: 248,
            9: 247,
            10: 246,
            11: 245,
            12: 244,  # 100 testów dla 12 błędów
            30: 200 # bo nie oczekujemy wysokiej skutecznosci
        }
    },
    # Wiązka niskich błędów
    {
        'name': 'Burst low errors',
        'error_generator': error_generator_burst,
        'error_type': error_to_low,
        'error_config': {
            1:255,
            2: 254,  # 60 testów dla 2 błędów
            3: 253,
            4: 252,
            5: 251,
            6: 250,
            7: 249,
            8: 248,
            9: 247,
            10:246,
            11: 245,
            12: 244,  # 100 testów dla 12 błędów
            30: 200,
        }
    },
    # Odwracanie bitów w wiązkach
    {
        'name': 'Burst flip errors',
        'error_generator': error_generator_burst,
        'error_type': error_flip,
        'error_config': {
            1:255,# 50 testów dla 1 błędu
            2: 254,  # 60 testów dla 2 błędów
            3: 253,
            4: 252,
            5: 251,
            6: 250,
            7: 249,
            8: 248,
            9: 247,
            10: 246,
            11: 245,
            12: 244,  # 100 testów dla 12 błędów
            30: 243,
        }
    },
]

if __name__ == '__main__':
    n = 255
    k = 171
    t = 11

    # Inicjalizacja kodera BCH
    bch_coder = BCHCoder(n, k, t)

    test_info = {}
    for test_case in test_suite:
        for error_count, test_amount in test_case['error_config'].items():
            test_info[f"{test_case['name']} errors: {error_count}"] = {
                'test_case': test_case['name'],
                'errors_amount': error_count,
                'test_amount': test_amount,
                'success': 0,
                'unfixable': 0,
                'fixed_incorrectly': 0,
                'encoding_error': 0,
            }
            for _ in progressbar(range(test_amount), prefix=f"{test_case['name']} amount: {error_count} "):
                try:
                    decoder_test(bch_coder, error_count, test_case['error_generator'], test_case['error_type'])
                except MessagesNotMatchError:
                    test_info[f"{test_case['name']} errors: {error_count}"]['fixed_incorrectly'] += 1
                except EncodingError:
                    test_info[f"{test_case['name']} errors: {error_count}"]['encoding_error'] += 1
                except MessageUnfixableError:
                    test_info[f"{test_case['name']} errors: {error_count}"]['unfixable'] += 1
                else:
                    test_info[f"{test_case['name']} errors: {error_count}"]['success'] += 1

    write_to_excel(test_info, "test_info_nowe.xlsx")
    # print(json.dumps(list(test_info.items()), indent=4))
