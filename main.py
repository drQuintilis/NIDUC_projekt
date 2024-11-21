class GF256:
    def __init__(self):
        # wielomiany beda potrzebne tylko od 1 do 21 (2t-1) dla liczb niepatrzystych, zeby stworzyc wielomian generujacy
        self.known_polynomials = {
            0: '11',  # m0
            1: '100011101',  # m1
            3: '101110111',  # m3
            5: '111110011',  # m5
            7: '101101001',       # m7
            9: '110111101',       # m9
            11: '111100111',      # m11
            13: '100101011',      # m13
            15: '111010111',      # m15
            17: '10011',          # m17
            19: '101100101',      # m19
            21: '110001011',      # m21

        }

        def wiel_generujacy(t):
            #wielomian generujacy bedzie wynikiem mnozenia funkcji od m_1 do m_21
            return