"""Suite A cases labelled `complexity` — correct and too slow."""

from __future__ import annotations

CASES: list[dict] = [
    {
        "id": "a067",
        "problem_slug": "fibonacci-number",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.missing_memoization",
        "code": """\
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
""",
    },
    {
        "id": "a068",
        "problem_slug": "climbing-stairs",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.missing_memoization",
        "code": """\
def climbStairs(n):
    if n <= 2:
        return n
    return climbStairs(n - 1) + climbStairs(n - 2)
""",
    },
    {
        "id": "a069",
        "problem_slug": "unique-paths",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.missing_memoization",
        "code": """\
def uniquePaths(m, n):
    if m == 1 or n == 1:
        return 1
    return uniquePaths(m - 1, n) + uniquePaths(m, n - 1)
""",
    },
    {
        "id": "a070",
        "problem_slug": "word-break",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.missing_memoization",
        "code": """\
def wordBreak(s, wordDict):
    words = set(wordDict)

    def solve(i):
        if i == len(s):
            return True
        for j in range(i + 1, len(s) + 1):
            if s[i:j] in words and solve(j):
                return True
        return False

    return solve(0)
""",
    },
    {
        "id": "a071",
        "problem_slug": "find-pivot-index",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.recompute_inside_loop",
        "code": """\
def pivotIndex(nums):
    for i in range(len(nums)):
        if sum(nums[:i]) == sum(nums[i + 1:]):
            return i
    return -1
""",
    },
    {
        "id": "a072",
        "problem_slug": "product-of-array-except-self",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.recompute_inside_loop",
        "code": """\
def productExceptSelf(nums):
    out = []
    for i in range(len(nums)):
        product = 1
        for j in range(len(nums)):
            if i != j:
                product *= nums[j]
        out.append(product)
    return out
""",
    },
    {
        "id": "a073",
        "problem_slug": "longest-consecutive-sequence",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.recompute_inside_loop",
        "code": """\
def longestConsecutive(nums):
    best = 0
    for n in nums:
        length = 1
        nxt = n + 1
        while nxt in list(nums):
            length += 1
            nxt += 1
        best = max(best, length)
    return best
""",
    },
    {
        "id": "a074",
        "problem_slug": "reverse-string",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.string_concat_in_loop",
        "code": """\
def reverseString(s):
    out = ""
    for ch in s:
        out = ch + out
    for i in range(len(s)):
        s[i] = out[i]
""",
    },
    {
        "id": "a075",
        "problem_slug": "excel-sheet-column-title",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.string_concat_in_loop",
        "code": """\
def convertToTitle(columnNumber):
    out = ""
    while columnNumber > 0:
        columnNumber -= 1
        out = chr(ord("A") + columnNumber % 26) + out
        columnNumber //= 26
    return out
""",
    },
    {
        "id": "a076",
        "problem_slug": "multiply-strings",
        "language": "java",
        "failure_type": "tle",
        "pattern_id": "complexity.string_concat_in_loop",
        "code": """\
class Solution {
    public String multiply(String num1, String num2) {
        String out = "";
        int[] digits = new int[num1.length() + num2.length()];
        for (int i = 0; i < digits.length; i++) {
            out = out + digits[i];
        }
        return out;
    }
}
""",
    },
    {
        "id": "a077",
        "problem_slug": "contains-duplicate",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.list_membership_scan",
        "code": """\
def containsDuplicate(nums):
    seen = []
    for n in nums:
        if n in seen:
            return True
        seen.append(n)
    return False
""",
    },
    {
        "id": "a078",
        "problem_slug": "intersection-of-two-arrays",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.list_membership_scan",
        "code": """\
def intersection(nums1, nums2):
    out = []
    for n in nums1:
        if n in nums2 and n not in out:
            out.append(n)
    return out
""",
    },
    {
        "id": "a079",
        "problem_slug": "missing-number",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.list_membership_scan",
        "code": """\
def missingNumber(nums):
    for i in range(len(nums) + 1):
        if i not in nums:
            return i
    return -1
""",
    },
    {
        "id": "a080",
        "problem_slug": "kth-largest-element-in-an-array",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.sort_inside_loop",
        "code": """\
def findKthLargest(nums, k):
    out = []
    for n in nums:
        out.append(n)
        out.sort(reverse=True)
        out = out[:k]
    return out[-1]
""",
    },
    {
        "id": "a081",
        "problem_slug": "last-stone-weight",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.sort_inside_loop",
        "code": """\
def lastStoneWeight(stones):
    while len(stones) > 1:
        stones.sort()
        a = stones.pop()
        b = stones.pop()
        if a != b:
            stones.append(a - b)
    return stones[0] if stones else 0
""",
    },
    {
        "id": "a082",
        "problem_slug": "number-of-recent-calls",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.front_insertion_or_removal_on_array",
        "code": """\
class RecentCounter:
    def __init__(self):
        self.calls = []

    def ping(self, t):
        self.calls.append(t)
        while self.calls[0] < t - 3000:
            self.calls.pop(0)
        return len(self.calls)
""",
    },
    {
        "id": "a083",
        "problem_slug": "binary-tree-level-order-traversal",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.front_insertion_or_removal_on_array",
        "code": """\
def levelOrder(root):
    if not root:
        return []
    out = []
    queue = [(root, 0)]
    while queue:
        node, depth = queue.pop(0)
        if depth == len(out):
            out.append([])
        out[depth].append(node.val)
        if node.left:
            queue.append((node.left, depth + 1))
        if node.right:
            queue.append((node.right, depth + 1))
    return out
""",
    },
    {
        "id": "a084",
        "problem_slug": "longest-palindromic-substring",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.repeated_slicing",
        "code": """\
def longestPalindrome(s):
    best = ""
    for i in range(len(s)):
        for j in range(i, len(s)):
            chunk = s[i:j + 1]
            if chunk == chunk[::-1] and len(chunk) > len(best):
                best = chunk
    return best
""",
    },
    {
        "id": "a085",
        "problem_slug": "merge-k-sorted-lists",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.repeated_slicing",
        "code": """\
def mergeKLists(lists):
    values = []
    for node in lists:
        while node:
            values = values + [node.val]
            node = node.next
    values.sort()
    return values
""",
    },
    {
        "id": "a086",
        "problem_slug": "permutations",
        "language": "python",
        "failure_type": "mle",
        "pattern_id": "complexity.copying_state_per_recursive_call",
        "code": """\
def permute(nums):
    out = []

    def build(path, remaining):
        if not remaining:
            out.append(path)
            return
        for i in range(len(remaining)):
            build(path + [remaining[i]], remaining[:i] + remaining[i + 1:])

    build([], list(nums))
    return out
""",
    },
    {
        "id": "a087",
        "problem_slug": "word-search",
        "language": "python",
        "failure_type": "mle",
        "pattern_id": "complexity.copying_state_per_recursive_call",
        "code": """\
def exist(board, word):
    rows, cols = len(board), len(board[0])

    def dfs(r, c, i, seen):
        if i == len(word):
            return True
        if r < 0 or c < 0 or r >= rows or c >= cols:
            return False
        if (r, c) in seen or board[r][c] != word[i]:
            return False
        nxt = set(seen)
        nxt.add((r, c))
        return any(
            dfs(r + dr, c + dc, i + 1, nxt)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )

    return any(dfs(r, c, 0, set()) for r in range(rows) for c in range(cols))
""",
    },
    {
        "id": "a088",
        "problem_slug": "n-queens",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.exponential_recursion_branching",
        "code": """\
def solveNQueens(n):
    out = []

    def valid(board):
        for i in range(len(board)):
            for j in range(i + 1, len(board)):
                if board[i] == board[j] or abs(board[i] - board[j]) == j - i:
                    return False
        return True

    def build(board):
        if len(board) == n:
            if valid(board):
                out.append(list(board))
            return
        for c in range(n):
            build(board + [c])

    build([])
    return out
""",
    },
    {
        "id": "a089",
        "problem_slug": "subsets",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.exponential_recursion_branching",
        "code": """\
def subsets(nums):
    out = []

    def build(i, path):
        if i == len(nums):
            if path not in out:
                out.append(path)
            return
        build(i + 1, path + [nums[i]])
        build(i + 1, list(path))

    build(0, [])
    return out
""",
    },
    {
        "id": "a090",
        "problem_slug": "range-sum-query-2d-immutable",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.redundant_full_recomputation_per_query",
        "code": """\
class NumMatrix:
    def __init__(self, matrix):
        self.matrix = matrix

    def sumRegion(self, row1, col1, row2, col2):
        total = 0
        for r in range(row1, row2 + 1):
            for c in range(col1, col2 + 1):
                total += self.matrix[r][c]
        return total
""",
    },
    {
        "id": "a091",
        "problem_slug": "range-sum-query-mutable",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.redundant_full_recomputation_per_query",
        "code": """\
class NumArray:
    def __init__(self, nums):
        self.nums = nums

    def update(self, index, val):
        self.nums[index] = val

    def sumRange(self, left, right):
        return sum(self.nums[left:right + 1])
""",
    },
    {
        "id": "a092",
        "problem_slug": "group-anagrams",
        "language": "javascript",
        "failure_type": "tle",
        "pattern_id": "complexity.sort_inside_loop",
        "code": """\
var groupAnagrams = function(strs) {
    const out = [];
    for (const s of strs) {
        let placed = false;
        for (const group of out) {
            if (group[0].split('').sort().join('') === s.split('').sort().join('')) {
                group.push(s);
                placed = true;
                break;
            }
        }
        if (!placed) out.push([s]);
    }
    return out;
};
""",
    },
    {
        "id": "a093",
        "problem_slug": "two-sum",
        "language": "go",
        "failure_type": "tle",
        "pattern_id": "complexity.recompute_inside_loop",
        "code": """\
func twoSum(nums []int, target int) []int {
    for i := 0; i < len(nums); i++ {
        for j := 0; j < len(nums); j++ {
            if i != j && nums[i]+nums[j] == target {
                return []int{i, j}
            }
        }
    }
    return nil
}
""",
    },
    {
        "id": "a125",
        "problem_slug": "two-sum",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.pairwise_scan_over_hashing",
        "code": """\
class Solution:
    def twoSum(self, nums, target):
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
        return []
""",
    },
    {
        "id": "a126",
        "problem_slug": "contains-duplicate",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "complexity.pairwise_scan_over_hashing",
        "code": """\
def containsDuplicate(nums):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] == nums[j]:
                return True
    return False
""",
    },
    {
        "id": "a127",
        "problem_slug": "3sum",
        "language": "java",
        "failure_type": "tle",
        "pattern_id": "complexity.pairwise_scan_over_hashing",
        "code": """\
class Solution {
    public boolean hasPairWithSum(int[] nums, int target) {
        for (int i = 0; i < nums.length; i++) {
            for (int j = i + 1; j < nums.length; j++) {
                if (nums[i] + nums[j] == target) {
                    return true;
                }
            }
        }
        return false;
    }
}
""",
    },
]
