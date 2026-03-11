def findSumPair(numbers, k):
    """
    Find if there exists a pair of integers in the array that sum to exactly k.
    
    Args:
        numbers: List of positive integers
        k: Target sum (positive integer)
    
    Returns:
        bool: True if a pair exists that sums to k, False otherwise
    """
    # Use a set to store numbers we've seen for O(1) lookup
    seen = set()
    
    for num in numbers:
        # Calculate what number we need to complete the sum
        complement = k - num
        
        # If we've seen the complement before, we found a pair
        if complement in seen:
            return True
        
        # Add current number to seen set
        seen.add(num)
    
    return False


# Test with the provided example
if __name__ == "__main__":
    numbers = [1, 5, 8, 1, 2]
    k = 13
    
    result = findSumPair(numbers, k)
    print(f"numbers = {numbers}")
    print(f"k = {k}")
    print(f"Result: {result}")
    
    # Additional test cases
    print("\nAdditional tests:")
    print(f"findSumPair([1, 2, 3, 4], 7): {findSumPair([1, 2, 3, 4], 7)}")  # True (3+4)
    print(f"findSumPair([1, 2, 3, 4], 10): {findSumPair([1, 2, 3, 4], 10)}")  # False
    print(f"findSumPair([5, 5], 10): {findSumPair([5, 5], 10)}")  # True (5+5)