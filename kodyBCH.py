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

def highlight_errors(codeword, error_positions):
    return ''.join(f"\033[91m{bit}\033[0m" if i in error_positions else str(bit) for i, bit in enumerate(codeword))

def poly_to_int(poly):
    """Konwertuje wielomian z listy na liczbę całkowitą."""
    return int(''.join(map(str, poly)), 2)

def int_to_poly(num, length):
    """Konwertuje liczbę całkowitą na wielomian w postaci listy zer i jedynek."""
    return list(map(int, bin(num)[2:].zfill(length)))

def gf_mul(x, y, prim=0x11d, field_size=8):
    """
    Mnożenie w GF(2^m) przy m=8 i prymitywnym wielomianie 0x11d dla operacji podobnych do AES.
    0x11d odpowiada x^8 + x^4 + x^3 + x + 1.
    """
    r = 0
    for i in range(field_size):
        if y & 1:
            r ^= x
        hbs = x & 0x80
        x <<= 1
        if hbs:
            x ^= prim
        x &= 0xFF
        y >>= 1
    return r

def gf_add(a, b):
    return a ^ b

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
        self.m = n - k
        self.t = t
        self.generator_polynomial = self.generate_generator_polynomial()
        self.log_table, self.antilog_table = self.build_tables()

    def build_tables(self, prim=0x11d):
        # Budowanie tabel wykładników i logarytmów
        # α = 0x02 w wybranej reprezentacji (można zmieniać w zależności od konwencji)
        alpha = 0x02
        log_table = [0] * 256
        antilog_table = [0] * 512
        x = 1
        for i in range(255):
            antilog_table[i] = x
            log_table[x] = i
            x = gf_mul(x, alpha, prim=prim)
        for i in range(255, 512):
            antilog_table[i] = antilog_table[i - 255]
        return log_table, antilog_table

    def gf_pow(self, alpha_power):
        """
        Zwraca element pola odpowiadający α^(alpha_power).
        Ponieważ α^255 = 1 i cykl się powtarza.
        """
        return self.antilog_table[alpha_power % 255]

    def gf_inv(self, a):
        """
        Zwraca element multiplikatywnie odwrotny do 'a' w GF(2^8),
        używając tabel logarytmów i antilogarytmów.
        """
        if a == 0:
            raise ZeroDivisionError("Nie ma odwrotnego do 0 w GF(2^8).")

        # Obliczamy indeks w tabeli logarytmów
        a_log = self.log_table[a]  # log(a)

        # Wzór a^-1 = α^(255 - log(a)), ale trzeba wziąć modulo 255
        exponent = 255 - a_log

        # Jeśli wykładnik == 255, to wykładnik % 255 = 0
        exponent %= 255

        # Zwracamy odpowiedni element z tabeli antilogarytmów
        return self.antilog_table[exponent]

    # obliczenie syndromów (podstawiamy alfa w x)
    def poly_evaluate(self, poly, alpha_power):
        value = 0
        for i, coef in enumerate(poly):
            if coef == 1:
                power = (len(poly) - 1 - i) * alpha_power % 255
                value ^= self.gf_pow(power)
        return value

    def calculate_syndromes(self, received_codeword):
        syndromes = []
        for i in range(1, 2 * self.t):
            syndromes.append(self.poly_evaluate(received_codeword, i))
        return syndromes

    def berlekamp_massey(self, syndromes):
        """
        syndromy: lista liczb całkowitych (0..255), długości 2t (na przykład, 2*11=22),
        każdy element to wartość syndromu S_i w GF(2^8).
        Zwraca (Lambda, L), gdzie Lambda to lista współczynników wielomianu
        lokatorów błędów (od najmniejszego do największego), L to jego stopień.
        """
        L = 0
        m = 1
        b = 1  # ostatnia niezerowa niespójność
        Lambda = [1] + [0] * (len(syndromes))  # Wielomian Lambda(x), długość z zapasem
        B = [1] + [0] * (len(syndromes))  # Pomocniczy wielomian B(x)

        for i in range(len(syndromes)):
            # 1) Obliczamy discrepancy = S_i + sum_{j=1..L} (Lambda_j * S_{i-j})
            # W GF(2^8) dodawanie = XOR
            delta = syndromes[i]
            for j in range(1, L + 1):
                if Lambda[j] != 0 and (i - j) >= 0:
                    delta = gf_add(delta, gf_mul(Lambda[j], syndromes[i - j]))

            # 2) Jeśli discrepancy == 0, nic nie robimy, po prostu m++
            if delta != 0:
                # 3) Tymczasowa kopia Lambda, aby zaktualizować B w razie potrzeby
                T = Lambda[:]

                # Lambda = Lambda + delta/b * x^m * B
                inv_b = self.gf_inv(b)  # b^-1
                factor = gf_mul(delta, inv_b)
                # Przesuwamy B(x) o m pozycji
                for k in range(len(syndromes) - m):
                    if B[k] != 0:
                        # Dodajemy factor * B[k] na pozycję k+m
                        Lambda[k + m] = gf_add(Lambda[k + m],
                                               gf_mul(factor, B[k]))

                if 2 * L <= i:
                    L_new = i + 1 - L
                    L = L_new
                    B = T
                    b = delta
                    m = 1
                else:
                    m += 1
            else:
                m += 1

        # Teraz mamy wielomian Lambda o wymaganej długości L+1
        # Przycinamy "ogon" niepotrzebnych zer
        Lambda = Lambda[:L + 1]
        return Lambda, L

    def chien_search(self, Lambda):
        """
        Szukamy korzeni wielomianu lokatorów błędów Lambda(x) w GF(2^8).
        Lambda: lista współczynników (Lambda[0], Lambda[1], ..., Lambda[L])
        gdzie Lambda[j] jest elementem GF(2^8) w zakresie [0..255].
        Zwraca listę indeksów pozycji, w których wykryto błąd.
        """
        # stopień wielomianu
        error_positions = []

        # Przeglądamy i od 0 do n-1 (n=255 dla BCH(255, k))
        for i in range(self.n):
            # Obliczamy Lambda(alpha^i):
            # val = sum_{j=0..L} [ Lambda[j] * alpha^(i*j) ]
            val = 0
            for j in range(len(Lambda)):
                if Lambda[j] != 0:  # jeśli 0, mnożenie i tak da 0
                # (i*j) % 255 ponieważ alpha^255 = 1
                    power = (i * j) % 255
                    val = gf_add(val, gf_mul(Lambda[j], self.gf_pow(power)))

            if val == 0:
                error_positions.append(i-1)

        return error_positions

    def decode_with_full_correction(self, received_codeword):
        syndromes = self.calculate_syndromes(received_codeword)
        Lambda, L = self.berlekamp_massey(syndromes)
        error_positions = self.chien_search(Lambda)
        if len(error_positions) > self.t:
            raise MessageUnfixableError("Błędy są niekorygowalne.")
        corrected_codeword = received_codeword[:]
        for error_position in error_positions:
            corrected_codeword[error_position] ^= 1
        syndromes = self.calculate_syndromes(corrected_codeword)
        if any(syndromes):
            raise MessageUnfixableError("Błędy są niekorygowalne.")
        # Wyciągnij pierwsze k bitów jako oryginalną wiadomość
        original_message = corrected_codeword[:self.k]
        return original_message

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

    def display_results(self, original_message, encoded_message, received_message, corrected_simple, corrected_full,
                        success_simple, success_full, error_positions):
        print("\n========== WYNIKI TESTU ==========")
        print("Oryginalna wiadomość:         ", ''.join(map(str, original_message)))
        print("Wielomian generujący:         ", ''.join(map(str, self.generator_polynomial)))
        print("Zakodowane słowo kodowe:      ", ''.join(map(str, encoded_message)))
        print("Słowo z błędami:              ", highlight_errors(received_message, error_positions))
        print("Prosta korekcja:              ", ''.join(map(str, corrected_simple)))
        print("Czy dekoder uproszczony zadziałał?", success_simple)
        print("Pełna korekcja:               ", ''.join(map(str, corrected_full)))
        print("Czy dekoder pełny zadziałał?", success_full)

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
    message = [random.randint(0, 1) for _ in range(k)]
    encoded_message = bch.encode(message)
    if not bch.validate_codeword(encoded_message):
        raise EncodingError("Niepoprawny kod.")

    received_message = encoded_message[:]
    errors_array = error_generator(n, errors_amount)
    for error_position in errors_array:
        error_type(received_message, error_position)
    corrected_codeword = bch.decode_with_error_correction(received_message)
    original_message = bch.recover_original_message(corrected_codeword)
    if message != original_message:
        raise MessagesNotMatchError("Odzyskana wiadomość nie zgadza się z oryginalną.")


def syndrome_test(bch, errors_amount, error_generator, error_type=error_flip):
    message = [random.randint(0, 1) for _ in range(k)]
    encoded_message = bch.encode(message)
    if not bch.validate_codeword(encoded_message):
        raise EncodingError("Niepoprawny kod.")

    received_message = encoded_message[:]
    errors_array = error_generator(n, errors_amount)
    for error_position in errors_array:
        error_type(received_message, error_position)

    syndromes = [bch.poly_evaluate(received_message, i) for i in range(1, 2 * bch.t)]
    return syndromes


def bc_test(bch, errors_amount, error_generator, error_type=error_flip):
    message = [random.randint(0, 1) for _ in range(k)]
    encoded_message = bch.encode(message)
    if not bch.validate_codeword(encoded_message):
        raise EncodingError("Niepoprawny kod.")

    received_message = encoded_message[:]
    errors_array = error_generator(n, errors_amount)
    for error_position in errors_array:
        error_type(received_message, error_position)

    syndromes_bits = [bch.poly_evaluate(received_message, i) for i in range(1, 2 * bch.t)]
    syndromes = [poly_to_int(syn_bits[::-1]) for syn_bits in syndromes_bits]
    Lambda, L = bch.berlekamp_massey(syndromes)
    return Lambda, L


def chein_test(bch, errors_amount, error_generator, error_type=error_flip):
    message = [random.randint(0, 1) for _ in range(k)]
    encoded_message = bch.encode(message)
    if not bch.validate_codeword(encoded_message):
        raise EncodingError("Niepoprawny kod.")

    received_message = encoded_message[:]
    errors_array = error_generator(n, errors_amount)
    for error_position in errors_array:
        error_type(received_message, error_position)

    syndromes_bits = [bch.poly_evaluate(received_message, i) for i in range(1, 2 * bch.t)]
    syndromes = [poly_to_int(syn_bits[::-1]) for syn_bits in syndromes_bits]
    Lambda, L = bch.berlekamp_massey(syndromes)
    error_positions = bch.chien_search(Lambda)
    return error_positions


def full_decode_test(bch, errors_amount, error_generator, error_type=error_flip):
    message = [random.randint(0, 1) for _ in range(k)]
    encoded_message = bch.encode(message)
    if not bch.validate_codeword(encoded_message):
        raise EncodingError("Niepoprawny kod.")

    received_message = encoded_message[:]
    errors_array = error_generator(n, errors_amount)
    for error_position in errors_array:
        error_type(received_message, error_position)

    decoded_message = bch.decode_with_full_correction(received_message)
    if message != decoded_message:
        for i, elem in enumerate(decoded_message):
            if elem != message[i]:
                print(f"Error at position {i}")
        raise MessagesNotMatchError("Odzyskana wiadomość nie zgadza się z oryginalną.")
    return decoded_message


def write_to_excel(data, file_name):
    df = pd.DataFrame.from_dict(data)
    df = df.transpose()
    df.to_excel(file_name, index=False, header=True)
    print(f"Tablica została zapisana do {file_name}")


test_suite = [
    {
        'name': 'Random errors',
        'error_generator': error_generator_random,
        'error_type': error_flip,
        'error_config': {
            1: 255,
            2: 600,
            3: 900,
            4: 600,
            5: 400,
            6: 600,
            7: 300,
            8: 300,
            9: 300,
            10: 300,
            11: 300,
            12: 300,
            30: 300,
        }
    },

    {
        'name': 'Burst high errors',
        'error_generator': error_generator_burst,
        'error_type': error_to_high,
        'error_config': {
            1: 255,
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
            12: 244,
            30: 226
        }
    },

    {
        'name': 'Burst low errors',
        'error_generator': error_generator_burst,
        'error_type': error_to_low,
        'error_config': {
            1: 255,
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
            12: 244,
            30: 226
        }
    },
     {
        'name': 'Burst flip errors',
        'error_generator': error_generator_burst,
        'error_type': error_flip,
        'error_config': {
            1: 255,
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
            12: 244,
            30: 226
        }
    },
]

if __name__ == '__main__':
    n = 255
    k = 171
    t = 11
    errors_amount = 4
    bch_coder = BCHCoder(n, k, t)

    original_message = [random.randint(0, 1) for _ in range(k)]
    encoded_message = bch_coder.encode(original_message)
    received_message = encoded_message[:]

    error_positions = error_generator_random(n, errors_amount)
    for pos in error_positions:
        error_flip(received_message, pos)

    try:
        corrected_simple = bch_coder.decode_with_error_correction(received_message)
        success_simple = corrected_simple[:k] == original_message
    except MessageUnfixableError:
        corrected_simple = received_message
        success_simple = False

    try:
        corrected_full = bch_coder.decode_with_full_correction(received_message)
        success_full = corrected_full == original_message
    except MessageUnfixableError:
        corrected_full = received_message
        success_full = False

    bch_coder.display_results(original_message, encoded_message, received_message, corrected_simple, corrected_full,
                              success_simple, success_full, error_positions)

    # test_info = {}
    # for test_case in test_suite:
    #     for error_count, test_amount in test_case['error_config'].items():
    #         test_info[f"{test_case['name']} errors: {error_count}"] = {
    #             'test_case': test_case['name'],
    #             'errors_amount': error_count,
    #             'test_amount': test_amount,
    #             'success': 0,
    #             'unfixable': 0,
    #             'fixed_incorrectly': 0,
    #             'encoding_error': 0,
    #         }
    #         for _ in progressbar(range(test_amount), prefix=f"{test_case['name']} amount: {error_count} "):
    #             try:
    #                 decoder_test(bch_coder, error_count, test_case['error_generator'], test_case['error_type'])
    #             except MessagesNotMatchError:
    #                 test_info[f"{test_case['name']} errors: {error_count}"]['fixed_incorrectly'] += 1
    #             except EncodingError:
    #                 test_info[f"{test_case['name']} errors: {error_count}"]['encoding_error'] += 1
    #             except MessageUnfixableError:
    #                 test_info[f"{test_case['name']} errors: {error_count}"]['unfixable'] += 1
    #             else:
    #                 test_info[f"{test_case['name']} errors: {error_count}"]['success'] += 1
    #
    # write_to_excel(test_info, "test_info_nowe.xlsx")
    # print(json.dumps(list(test_info.items()), indent=4))
