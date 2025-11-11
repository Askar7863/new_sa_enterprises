import numpy as np

def calculate_3d_array_sum(arr):
    """
    Calculates the sum of all elements in a 3D array using NumPy.

    Args:
        arr: A list of lists of lists representing a 3D array, or a numpy array.

    Returns:
        The sum of all elements in the array.

    Raises:
        ValueError: If the input cannot be converted to a NumPy array,
                    or if it is not 3-dimensional.
    """
    try:
        np_array = np.array(arr)

        # Check if the array is actually 3-dimensional
        if np_array.ndim != 3:
            raise ValueError(f"Input array must be 3-dimensional, but got {np_array.ndim} dimensions.")

        total_sum = np.sum(np_array)
        return total_sum
    except TypeError as e:
        raise ValueError(f"Error converting input to a NumPy array. Ensure it is array-like: {e}")
    except Exception as e:
        # Catch any other potential errors during sum calculation or array processing
        raise ValueError(f"An unexpected error occurred during sum calculation: {e}")


if __name__ == "__main__":
    print("--- Demonstrating 3D Array Sum Calculation ---")

    # Example 1: A valid 3D array
    my_3d_array = [
        [
            [1, 2, 3],
            [4, 5, 6]
        ],
        [
            [7, 8, 9],
            [10, 11, 12]
        ],
        [
            [13, 14, 15],
            [16, 17, 18]
        ]
    ]

    print(f"\nInput 3D array (list representation):\n{my_3d_array}")
    print(f"NumPy representation:\n{np.array(my_3d_array)}")
    try:
        sum_result = calculate_3d_array_sum(my_3d_array)
        print(f"The sum of the 3D array is: {sum_result}") # Expected: 171
    except ValueError as e:
        print(f"Error: {e}")

    # Example 2: Testing with an already existing NumPy 3D array
    numpy_3d_array = np.arange(1, 28).reshape((3, 3, 3)) # 3x3x3 array from 1 to 27
    print(f"\nInput NumPy 3D array:\n{numpy_3d_array}")
    try:
        sum_result_numpy = calculate_3d_array_sum(numpy_3d_array)
        print(f"The sum of the NumPy 3D array is: {sum_result_numpy}") # Expected: 378
    except ValueError as e:
        print(f"Error: {e}")

    # Example 3: Testing with an invalid array (2D instead of 3D)
    invalid_2d_array = [
        [10, 20],
        [30, 40]
    ]
    print(f"\nInput invalid 2D array:\n{invalid_2d_array}")
    try:
        sum_result_2d = calculate_3d_array_sum(invalid_2d_array)
        print(f"The sum of the 2D array is: {sum_result_2d}")
    except ValueError as e:
        print(f"Error: {e}")

    # Example 4: Testing with an input that is not array-like (string)
    invalid_non_array = "this is not an array"
    print(f"\nInput invalid non-array (string): '{invalid_non_array}'")
    try:
        sum_result_str = calculate_3d_array_sum(invalid_non_array)
        print(f"The sum of the string input is: {sum_result_str}")
    except ValueError as e:
        print(f"Error: {e}")
