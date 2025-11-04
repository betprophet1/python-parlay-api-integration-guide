function findSumPair(numbers, k) {
    /**
     * Find the indices of two integers in the array that sum to exactly k.
     * 
     * @param {number[]} numbers - Array of positive integers
     * @param {number} k - Target sum (positive integer)
     * @returns {number[]} Array of two indices [i, j] where numbers[i] + numbers[j] = k, or empty array if no pair found
     */
    
    // Use a Map to store numbers we've seen and their indices
    const seen = new Map();
    
    for (let i = 0; i < numbers.length; i++) {
        const num = numbers[i];
        const complement = k - num;
        
        // If we've seen the complement before, we found a pair
        if (seen.has(complement)) {
            return [seen.get(complement), i];
        }
        
        // Add current number and its index to seen map
        seen.set(num, i);
    }
    
    return [];
}

// Test with the provided example
const numbers = [1, 5, 8, 1, 2];
const k = 13;

const result = findSumPair(numbers, k);
console.log(`numbers = [${numbers}]`);
console.log(`k = ${k}`);
console.log(`Result: ${result}`);

// Additional test cases
console.log('\nAdditional tests:');
console.log(`findSumPair([1, 2, 3, 4], 7): ${findSumPair([1, 2, 3, 4], 7)}`);  // true (3+4)
console.log(`findSumPair([1, 2, 3, 4], 10): ${findSumPair([1, 2, 3, 4], 10)}`);  // false
console.log(`findSumPair([5, 5], 10): ${findSumPair([5, 5], 10)}`);  // true (5+5)

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = findSumPair;
}