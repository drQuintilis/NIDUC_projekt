class GF256:
    def __init__(self):
        # wielomiany beda potrzebne tylko od 1 do 21 (2t-1) dla liczb niepatrzystych, zeby stworzyc wielomian generujacy
        self.known_polynomials = {
            0: '0b11',  # m0
            1: '0b100011101',  # m1
            3: '0b101110111',  # m3
            5: '0b111110011',  # m5
            7: '0b101101001',       # m7
            9: '0b110111101',       # m9
            11: '0b111100111',      # m11
            13: '0b100101011',      # m13
            15: '0b111010111',      # m15
            17: '0b10011',          # m17
            19: '0b101100101',      # m19
            21: '0b110001011',      # m21

        }

        def wiel_generujacy(t):
                #wielomian generujacy bedzie wynikiem mnozenia funkcji od m_1 do m_21