from math import comb

# Parameters
n = 255  # Length of the BCH codeword
min_distance = 24  # Minimum distance constraint

# Total number of combinations for t errors
def total_combinations(n, t):
    return comb(n, t)

# Calculate the number of valid configurations (d > min_distance)
def count_valid_error_combinations(n, min_distance, t):
    def recursive_count(positions, start):
        if len(positions) == t:  # We've placed t errors
            return 1
        valid_count = 0
        for i in range(start, n):
            # Ensure minimum distance constraint
            if not positions or i - positions[-1] > min_distance:
                valid_count += recursive_count(positions + [i], i + 1)
        return valid_count

    return recursive_count([], 0)

# Analyze for 2, 3, and 4 errors
results = {}
for errors in [2, 3, 4]:
    total_combinations_errors = total_combinations(n, errors)
    valid_combinations_errors = count_valid_error_combinations(n, min_distance, errors)
    invalid_combinations_errors = total_combinations_errors - valid_combinations_errors
    results[errors] = {
        "Total Combinations": total_combinations_errors,
        "Valid Combinations": valid_combinations_errors,
        "Invalid Combinations": invalid_combinations_errors,
    }

# Print results
for errors, data in results.items():
    print(f"\nFor {errors} errors:")
    print(f"  Total Combinations: {data['Total Combinations']}")
    print(f"  Invalid Combinations: {data['Valid Combinations']}")
    print(f"  Valid Combinations: {data['Invalid Combinations']}")
