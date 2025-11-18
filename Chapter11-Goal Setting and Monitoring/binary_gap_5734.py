# This Python program implements the following use case:
# Write code to find BinaryGap of a given positive integer

def binary_gap(n):
    """
    Find the longest sequence of consecutive zeros between ones in binary representation.
    
    Args:
        n (int): A positive integer
    
    Returns:
        int: The length of the longest binary gap (0 if no gap exists)
    """
    binary = bin(n)[2:]
    
    max_gap = 0
    current_gap = 0
    gap_tracking_active = False
    
    for digit in binary:
        if digit == '1':
            if gap_tracking_active and current_gap > max_gap:
                max_gap = current_gap
            current_gap = 0
            gap_tracking_active = True
        elif gap_tracking_active:
            current_gap += 1
    
    return max_gap

def main():
    """Test the binary_gap function with various examples."""
    test_cases = [
        1,      # binary: 1, gap: 0
        2,      # binary: 10, gap: 0
        5,      # binary: 101, gap: 1
        6,      # binary: 110, gap: 1
        9,      # binary: 1001, gap: 2
        15,     # binary: 1111, gap: 0
        20,     # binary: 10100, gap: 1
        22,     # binary: 10110, gap: 2
        32,     # binary: 100000, gap: 0
        1041,   # binary: 10000010001, gap: 5
        529,    # binary: 1000010001, gap: 4
        328,    # binary: 101001000, gap: 2
        2147483647,  # max 32-bit signed integer
    ]
    
    print("Binary Gap Examples:")
    print("-" * 40)
    
    for num in test_cases:
        gap = binary_gap(num)
        binary_rep = bin(num)[2:]
        print(f"Number: {num:10} | Binary: {binary_rep:20} | Binary Gap: {gap}")
    
    print("\n" + "-" * 40)
    
    try:
        user_input = int(input("\nEnter a positive integer to find its binary gap: "))
        if user_input <= 0:
            print("Error: Please enter a positive integer.")
        else:
            gap = binary_gap(user_input)
            print(f"Binary representation: {bin(user_input)[2:]}")
            print(f"Longest binary gap: {gap}")
    except ValueError:
        print("Error: Invalid input. Please enter a valid integer.")

if __name__ == "__main__":
    main()