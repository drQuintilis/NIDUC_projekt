class GF256:
    def __init__(self):
        self.wielomian = 0x11B  # Nierozkładalny wielomian dla ciała GF(2^8)
        self.size = 256
        self.exp_table = [0] * self.size
        self.log_table = [0] * self.size
        self.known_polynomials = {
            0: [1, 1],  # m0
            1:[1, 0, 0, 0, 1, 1, 1, 0, 1],  # m1
            3: [1, 0, 1, 1, 1, 0, 1, 1, 1],  # m3
            5: [1, 1, 1, 1, 1, 0, 0, 1, 1],  # m5
            7: [1, 0, 1, 1, 0, 1, 0, 0, 1],  # m7
            9: [1, 1, 0, 1, 1, 1, 1, 0, 1],  # m9
            11:[1, 1, 1, 1, 0, 0, 1, 1, 1],  # m11
            13: [1, 0, 0, 1, 0, 1, 0, 1, 1],  # m13
            15: [1, 1, 1, 0, 1, 0, 1, 1, 1],  # m15
            17: [1, 0, 0, 1, 1],  # m17
            19: [1, 0, 1, 1, 0, 0, 1, 0, 1],  # m19
            21:[1, 1, 0, 0, 0, 1, 0, 1, 1],  # m21
        }
        self.generator_polynomial = self.generate_generator_polynomial()
        self._create_galois_tables()

    def _create_galois_tables(self):
        # Tworzenie tabeli wykładników i logarytmów
        x = 1
        for i in range(self.size - 1):
            self.exp_table[i] = x
            self.log_table[x] = i
            x <<= 1
            if x & 0x100:  # Jeśli wartość przekracza 8 bitów, stosujemy modulo
                x ^= self.wielomian
        self.exp_table[self.size - 1] = 1  # 1 na końcu dla cykliczności

    def galois_multiply(self, a, b):
        if a == 0 or b == 0:
            return 0
        return self.exp_table[(self.log_table[a] + self.log_table[b]) % (self.size - 1)]

    def multiply_polynomials(self, poly1, poly2):
        # Mnożenie dwóch wielomianów
        result = [0] * (len(poly1) + len(poly2) - 1)
        for i in range(len(poly1)):
            for j in range(len(poly2)):
                result[i + j] ^= self.galois_multiply(poly1[i], poly2[j])
        return result

    def generate_generator_polynomial(self):
        # Generowanie wielomianu generującego przez mnożenie wszystkich wielomianów minimalnych
        generator_poly = [1]  # Rozpoczynamy od wielomianu 1
        for poly in self.known_polynomials.values():
            generator_poly = self.multiply_polynomials(generator_poly, poly)
        return generator_poly

def encode(self, data):
    encoded_data = []
    part_length = 171  # Długość słowa danych

    for i in range(0, len(data), part_length):
        part = data[i:i + part_length]
        if len(part) < part_length:
            part += [0] * (part_length - len(part))  # Uzupełnianie zerami

        padded_data = part + [0] * (len(self.generator_polynomial) - 1)
        for j in range(part_length):
            coeff = padded_data[j]
            if coeff != 0:
                for k in range(len(self.generator_polynomial)):
                    padded_data[j + k] ^= self.galois_multiply(coeff, self.generator_polynomial[k])

        # Dodajemy część danych zakodowanych jako końcowe symbole (część kontrolna)
        encoded_data.extend(part + padded_data[part_length:])
    return encoded_data

# Przykładowe użycie
gf = GF256()
data = [1]*255  # Słowo kodowe o długości 255
encoded = gf.encode(data)

print("Zakodowane dane:", encoded)