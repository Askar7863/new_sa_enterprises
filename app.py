import sys

def calculate_factorial(n: int) -> int:
    """
    Calculates the factorial of a non-negative integer n.
    Factorial is defined as the product of all positive integers less than or equal to n.
    The factorial of 0 is 1.

    Args:
        n (int): The non-negative integer for which to calculate the factorial.

    Returns:
        int: The factorial of n.

    Raises:
        ValueError: If n is a negative integer.
        TypeError: If n is not an integer.
    """
    if not isinstance(n, int):
        raise TypeError("Input must be an integer.")
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers.")
    if n == 0:
        return 1

    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

def main():
    """
    Main function to get two numbers from the user and calculate their factorials.
    """
    print("\n--- Factorial Calculator for Two Numbers ---")

    numbers = []
    for i in range(1, 3):
        while True:
            try:
                input_str = input(f"Enter non-negative integer number {i}: ")
                num = int(input_str)
                if num < 0:
                    print("Error: Please enter a non-negative integer.")
                else:
                    numbers.append(num)
                    break
            except ValueError:
                print(f"Error: Invalid input '{input_str}'. Please enter an integer.")
            except EOFError:
                print("\nInput stream closed unexpectedly. Exiting.")
                sys.exit(1)

    print("\n--- Results ---")
    for i, num in enumerate(numbers):
        try:
            factorial_result = calculate_factorial(num)
            print(f"The factorial of {num} is: {factorial_result}")
        except (ValueError, TypeError) as e:
            # This block might not be strictly necessary if input validation for calculate_factorial is perfect
            # but it's good practice for defense-in-depth.
            print(f"Error calculating factorial for {num}: {e}")

    print("\n--- Calculation Complete ---")

if __name__ == "__main__":
    main()
