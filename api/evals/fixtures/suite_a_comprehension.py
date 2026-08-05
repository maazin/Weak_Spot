"""Suite A cases labelled `comprehension` — misread the problem."""

from __future__ import annotations

CASES: list[dict] = [
    {
        "id": "a094",
        "problem_slug": "two-sum-ii-input-array-is-sorted",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "comprehension.missed_sorted_input_guarantee",
        "code": """\
def twoSum(numbers, target):
    ordered = sorted(numbers)
    for i in range(len(ordered)):
        for j in range(i + 1, len(ordered)):
            if ordered[i] + ordered[j] == target:
                return [i + 1, j + 1]
    return []
""",
    },
    {
        "id": "a095",
        "problem_slug": "merge-sorted-array",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "comprehension.missed_sorted_input_guarantee",
        "code": """\
def merge(nums1, m, nums2, n):
    for i in range(n):
        nums1[m + i] = nums2[i]
    for i in range(len(nums1)):
        for j in range(len(nums1) - 1):
            if nums1[j] > nums1[j + 1]:
                nums1[j], nums1[j + 1] = nums1[j + 1], nums1[j]
""",
    },
    {
        "id": "a096",
        "problem_slug": "longest-increasing-subsequence",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "comprehension.missed_constraint_bound",
        "code": """\
def lengthOfLIS(nums):
    best = 0

    def build(i, prev, length):
        nonlocal best
        if i == len(nums):
            best = max(best, length)
            return
        if prev is None or nums[i] > prev:
            build(i + 1, nums[i], length + 1)
        build(i + 1, prev, length)

    build(0, None, 0)
    return best
""",
    },
    {
        "id": "a097",
        "problem_slug": "target-sum",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "comprehension.missed_constraint_bound",
        "code": """\
def findTargetSumWays(nums, target):
    count = 0

    def build(i, total):
        nonlocal count
        if i == len(nums):
            if total == target:
                count += 1
            return
        build(i + 1, total + nums[i])
        build(i + 1, total - nums[i])

    build(0, 0)
    return count
""",
    },
    {
        "id": "a098",
        "problem_slug": "maximum-subarray",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_negative_values",
        "code": """\
def maxSubArray(nums):
    best = 0
    cur = 0
    for n in nums:
        cur = max(0, cur + n)
        best = max(best, cur)
    return best
""",
    },
    {
        "id": "a099",
        "problem_slug": "maximum-product-subarray",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_negative_values",
        "code": """\
def maxProduct(nums):
    best = nums[0]
    cur = 1
    for n in nums:
        cur *= n
        if cur > best:
            best = cur
        if cur == 0:
            cur = 1
    return best
""",
    },
    {
        "id": "a100",
        "problem_slug": "minimum-size-subarray-sum",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_negative_values",
        "code": """\
def minSubArrayLen(target, nums):
    left = 0
    total = 0
    best = len(nums) + 1
    for right, n in enumerate(nums):
        total += n
        while total >= target:
            best = min(best, right - left + 1)
            total -= nums[left]
            left += 1
    return best if best <= len(nums) else 0
""",
    },
    {
        "id": "a101",
        "problem_slug": "two-sum",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_return_format",
        "code": """\
def twoSum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [target - n, n]
        seen[n] = i
    return []
""",
    },
    {
        "id": "a102",
        "problem_slug": "two-sum-ii-input-array-is-sorted",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_return_format",
        "code": """\
def twoSum(numbers, target):
    lo, hi = 0, len(numbers) - 1
    while lo < hi:
        total = numbers[lo] + numbers[hi]
        if total == target:
            return [lo, hi]
        if total < target:
            lo += 1
        else:
            hi -= 1
    return []
""",
    },
    {
        "id": "a103",
        "problem_slug": "find-first-and-last-position-of-element-in-sorted-array",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_return_format",
        "code": """\
def searchRange(nums, target):
    for i, n in enumerate(nums):
        if n == target:
            return i
    return -1
""",
    },
    {
        "id": "a104",
        "problem_slug": "remove-duplicates-from-sorted-array",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_in_place_requirement",
        "code": """\
def removeDuplicates(nums):
    out = []
    for n in nums:
        if not out or out[-1] != n:
            out.append(n)
    return out
""",
    },
    {
        "id": "a105",
        "problem_slug": "move-zeroes",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_in_place_requirement",
        "code": """\
def moveZeroes(nums):
    nonzero = [n for n in nums if n != 0]
    zeros = [0] * (len(nums) - len(nonzero))
    return nonzero + zeros
""",
    },
    {
        "id": "a106",
        "problem_slug": "rotate-image",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_in_place_requirement",
        "code": """\
def rotate(matrix):
    n = len(matrix)
    out = [[0] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            out[c][n - 1 - r] = matrix[r][c]
    return out
""",
    },
    {
        "id": "a107",
        "problem_slug": "binary-search",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_duplicate_elements_allowed",
        "code": """\
def search(nums, target):
    positions = {n: i for i, n in enumerate(nums)}
    return positions.get(target, -1)
""",
    },
    {
        "id": "a108",
        "problem_slug": "3sum",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_duplicate_elements_allowed",
        "code": """\
def threeSum(nums):
    nums.sort()
    out = []
    for i in range(len(nums) - 2):
        lo, hi = i + 1, len(nums) - 1
        while lo < hi:
            total = nums[i] + nums[lo] + nums[hi]
            if total == 0:
                out.append([nums[i], nums[lo], nums[hi]])
                lo += 1
                hi -= 1
            elif total < 0:
                lo += 1
            else:
                hi -= 1
    return out
""",
    },
    {
        "id": "a109",
        "problem_slug": "top-k-frequent-elements",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_duplicate_elements_allowed",
        "code": """\
def topKFrequent(nums, k):
    counts = {}
    for n in nums:
        counts[n] = 1
    ordered = sorted(counts, key=lambda x: counts[x], reverse=True)
    return ordered[:k]
""",
    },
    {
        "id": "a110",
        "problem_slug": "largest-number",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_tiebreak_rule",
        "code": """\
def largestNumber(nums):
    strs = [str(n) for n in nums]
    strs.sort(key=lambda s: s[0], reverse=True)
    return "".join(strs).lstrip("0") or "0"
""",
    },
    {
        "id": "a111",
        "problem_slug": "merge-intervals",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_tiebreak_rule",
        "code": """\
def merge(intervals):
    intervals.sort(key=lambda x: x[1])
    out = []
    for start, end in intervals:
        if out and start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return out
""",
    },
    {
        "id": "a112",
        "problem_slug": "maximum-subarray",
        "language": "python",
        "failure_type": "runtime_error",
        "pattern_id": "comprehension.missed_empty_or_single_element_case",
        "code": """\
def maxSubArray(nums):
    best = nums[0]
    cur = nums[0]
    for i in range(1, len(nums)):
        cur = max(nums[i], cur + nums[i])
        best = max(best, cur)
    return best if nums else 0
""",
    },
    {
        "id": "a113",
        "problem_slug": "best-time-to-buy-and-sell-stock",
        "language": "python",
        "failure_type": "runtime_error",
        "pattern_id": "comprehension.missed_empty_or_single_element_case",
        "code": """\
def maxProfit(prices):
    low = prices[0]
    best = 0
    for p in prices[1:]:
        best = max(best, p - low)
        low = min(low, p)
    return best
""",
    },
    {
        "id": "a114",
        "problem_slug": "spiral-matrix",
        "language": "python",
        "failure_type": "runtime_error",
        "pattern_id": "comprehension.missed_empty_or_single_element_case",
        "code": """\
def spiralOrder(matrix):
    out = []
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        for c in range(left, right + 1):
            out.append(matrix[top][c])
        top += 1
        for r in range(top, bottom + 1):
            out.append(matrix[r][right])
        right -= 1
        for c in range(right, left - 1, -1):
            out.append(matrix[bottom][c])
        bottom -= 1
        for r in range(bottom, top - 1, -1):
            out.append(matrix[r][left])
        left += 1
    return out
""",
    },
    {
        "id": "a115",
        "problem_slug": "longest-increasing-subsequence",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.misread_subsequence_vs_subarray",
        "code": """\
def lengthOfLIS(nums):
    best = 1
    run = 1
    for i in range(1, len(nums)):
        if nums[i] > nums[i - 1]:
            run += 1
            best = max(best, run)
        else:
            run = 1
    return best
""",
    },
    {
        "id": "a116",
        "problem_slug": "longest-common-subsequence",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.misread_subsequence_vs_subarray",
        "code": """\
def longestCommonSubsequence(text1, text2):
    best = 0
    for i in range(len(text1)):
        for j in range(len(text2)):
            length = 0
            while (
                i + length < len(text1)
                and j + length < len(text2)
                and text1[i + length] == text2[j + length]
            ):
                length += 1
            best = max(best, length)
    return best
""",
    },
    {
        "id": "a117",
        "problem_slug": "is-subsequence",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.misread_subsequence_vs_subarray",
        "code": """\
def isSubsequence(s, t):
    return s in t
""",
    },
    {
        "id": "a118",
        "problem_slug": "knight-dialer",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_modulo_requirement",
        "code": """\
def knightDialer(n):
    moves = {
        0: [4, 6], 1: [6, 8], 2: [7, 9], 3: [4, 8], 4: [0, 3, 9],
        5: [], 6: [0, 1, 7], 7: [2, 6], 8: [1, 3], 9: [2, 4],
    }
    dp = [1] * 10
    for _ in range(n - 1):
        nxt = [0] * 10
        for d in range(10):
            for m in moves[d]:
                nxt[m] += dp[d]
        dp = nxt
    return sum(dp)
""",
    },
    {
        "id": "a119",
        "problem_slug": "count-sorted-vowel-strings",
        "language": "java",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_modulo_requirement",
        "code": """\
class Solution {
    public int countVowelStrings(int n) {
        int[] dp = {1, 1, 1, 1, 1};
        for (int i = 1; i < n; i++) {
            for (int j = 3; j >= 0; j--) {
                dp[j] = dp[j] + dp[j + 1];
            }
        }
        int total = 0;
        for (int v : dp) total += v;
        return total;
    }
}
""",
    },
    {
        "id": "a120",
        "problem_slug": "next-greater-element-ii",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_cyclic_or_wraparound",
        "code": """\
def nextGreaterElements(nums):
    out = [-1] * len(nums)
    stack = []
    for i, n in enumerate(nums):
        while stack and nums[stack[-1]] < n:
            out[stack.pop()] = n
        stack.append(i)
    return out
""",
    },
    {
        "id": "a121",
        "problem_slug": "house-robber-ii",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_cyclic_or_wraparound",
        "code": """\
def rob(nums):
    prev = 0
    cur = 0
    for n in nums:
        prev, cur = cur, max(cur, prev + n)
    return cur
""",
    },
    {
        "id": "a122",
        "problem_slug": "gas-station",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_cyclic_or_wraparound",
        "code": """\
def canCompleteCircuit(gas, cost):
    tank = 0
    for i in range(len(gas)):
        tank += gas[i] - cost[i]
        if tank < 0:
            return -1
    return 0
""",
    },
    {
        "id": "a123",
        "problem_slug": "string-to-integer-atoi",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "comprehension.missed_return_format",
        "code": """\
def myAtoi(s):
    return int(s.strip())
""",
    },
    {
        "id": "a124",
        "problem_slug": "first-missing-positive",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "comprehension.missed_constraint_bound",
        "code": """\
def firstMissingPositive(nums):
    i = 1
    while True:
        if i not in nums:
            return i
        i += 1
""",
    },
]
