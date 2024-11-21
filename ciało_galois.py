import pandas as pd


wielomian = 0x11B  # Nierozkładalny wielomian dla ciała GF(2^8)

def galois_multiply(a, b):
    # Wykonuje mnożenie dwóch liczb w ciele GF(2^8) z uwzględnieniem nierozkładalnego wielomianu
    result = 0
    while b:
        if b & 1:  # Jeśli najmłodszy bit jest ustawiony, dodajemy `a` do wyniku
            result ^= a  # XOR, ponieważ jesteśmy w ciele GF(2)
        a <<= 1  # Przesuwamy `a` w lewo (mnożymy przez x)
        if a & 0x100:  # Jeśli wartość przekracza 8 bitów, stosujemy modulo
            a ^= wielomian
        b >>= 1  # Przechodzimy do następnego bitu liczby b
    return result

def galois_addition(a, b):
    # Wykonuje dodawanie dwóch liczb w ciele GF(2^8)
    return a ^ b #XOR

def create_gf_2_8_table(dzialanie):
    # Tworzy tabelę o rozmiarze 256x256
    table_size = 256
    table = [[0] * (table_size + 1) for _ in range(table_size + 1)]

    # Wypełnia pierwszą kolumnę i wiersz wartościami od 0 do 255
    for i in range(1, table_size + 1):
        table[i][0] = i - 1
        table[0][i] = i - 1

    # Wypełnia resztę tabeli wynikami operacji
    for i in range(1, table_size + 1):
        for j in range(1, table_size + 1):
            table[i][j] = dzialanie(i - 1, j - 1)
    return table

def write_to_excel(data, file_name):
    #Zapisuje tabelę do pliku Excel
    df = pd.DataFrame(data)
    df.to_excel(file_name, index=False, header=False)
    print(f"Tablica została zapisana do {file_name}")


if __name__ == "__main__":
    # Generowanie tabeli i zapis do Excela
    multiplication_table = create_gf_2_8_table(galois_multiply)
    addition_table = create_gf_2_8_table(galois_addition)
    write_to_excel(multiplication_table, "gf_2_8_tabliczka_mnozenia.xlsx")
    write_to_excel(addition_table, "gf_2_8_tabliczka_dodawania.xlsx")

