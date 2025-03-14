**Project Overview**

This repository demonstrates how BCH codes (Bose–Chaudhuri–Hocquenghem) can effectively detect and correct multiple errors in a codeword of length n = 255 bits. 
The project was implemented under the subject "reliability and diagnostics of digital systems". 
The code was written in Python, and the report presents (sprawozdanie.pdf) a detailed theoretical analysis and test results.

The key parameters are:

        k = 171 data bits
        t = 11 error-correcting capability

Hence, each 171-bit message is encoded into a 255-bit codeword, allowing up to 11 errors to be corrected.

**Encoding:**

The project encodes a 171-bit message by appending 84 parity bits, using a generator polynomial built from minimal polynomials over GF(2^8).

**Decoding (Simplified Version):**

Relies on calculating the syndrome and monitoring its Hamming weight. 
If the weight is no larger than t, errors are presumed to lie within the parity bits and can be corrected by XORing with the syndrome. 
Otherwise, the codeword undergoes cyclic shifts to locate correctable error positions.

**Decoding (Full Version):**

Implements Berlekamp-Massey (to derive the error-locator polynomial) and Chien search (to identify the exact positions of errors). 
This method ensures near-100% correction success for all error patterns that do not exceed the code’s theoretical correction limit t.

