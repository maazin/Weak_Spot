"""Suite A cases labelled `implementation` — right shape, wrong details."""

from __future__ import annotations

CASES: list[dict] = [
    {
        "id": "a033",
        "problem_slug": "binary-search",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.binary_search_bounds_off_by_one",
        "code": """\
def search(nums, target):
    lo, hi = 0, len(nums)
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
""",
    },
    {
        "id": "a034",
        "problem_slug": "search-insert-position",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.binary_search_bounds_off_by_one",
        "code": """\
def searchInsert(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo
""",
    },
    {
        "id": "a035",
        "problem_slug": "find-minimum-in-rotated-sorted-array",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "implementation.binary_search_infinite_loop",
        "code": """\
def findMin(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > nums[hi]:
            lo = mid
        else:
            hi = mid
    return nums[lo]
""",
    },
    {
        "id": "a036",
        "problem_slug": "find-peak-element",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "implementation.binary_search_infinite_loop",
        "code": """\
def findPeakElement(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] < nums[mid + 1]:
            lo = mid
        else:
            hi = mid - 1
    return lo
""",
    },
    {
        "id": "a037",
        "problem_slug": "rotting-oranges",
        "language": "python",
        "failure_type": "mle",
        "pattern_id": "implementation.bfs_visited_marked_on_dequeue",
        "code": """\
from collections import deque


def orangesRotting(grid):
    q = deque()
    seen = set()
    fresh = 0
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 2:
                q.append((r, c, 0))
            elif grid[r][c] == 1:
                fresh += 1
    minutes = 0
    while q:
        r, c, t = q.popleft()
        if (r, c) in seen:
            continue
        seen.add((r, c))
        minutes = max(minutes, t)
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] == 1:
                q.append((nr, nc, t + 1))
    return minutes if len(seen) >= fresh else -1
""",
    },
    {
        "id": "a038",
        "problem_slug": "01-matrix",
        "language": "python",
        "failure_type": "mle",
        "pattern_id": "implementation.bfs_visited_marked_on_dequeue",
        "code": """\
from collections import deque


def updateMatrix(mat):
    rows, cols = len(mat), len(mat[0])
    dist = [[-1] * cols for _ in range(rows)]
    q = deque()
    for r in range(rows):
        for c in range(cols):
            if mat[r][c] == 0:
                q.append((r, c, 0))
    visited = set()
    while q:
        r, c, d = q.popleft()
        if (r, c) in visited:
            continue
        visited.add((r, c))
        dist[r][c] = d
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                q.append((nr, nc, d + 1))
    return dist
""",
    },
    {
        "id": "a039",
        "problem_slug": "fibonacci-number",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.recursion_base_case_wrong",
        "code": """\
def fib(n):
    if n == 1:
        return 1
    return fib(n - 1) + fib(n - 2)
""",
    },
    {
        "id": "a040",
        "problem_slug": "maximum-depth-of-binary-tree",
        "language": "python",
        "failure_type": "runtime_error",
        "pattern_id": "implementation.recursion_base_case_wrong",
        "code": """\
def maxDepth(root):
    left = maxDepth(root.left)
    right = maxDepth(root.right)
    if root is None:
        return 0
    return 1 + max(left, right)
""",
    },
    {
        "id": "a041",
        "problem_slug": "subsets-ii",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.duplicates_not_deduped",
        "code": """\
def subsetsWithDup(nums):
    nums.sort()
    out = []

    def build(i, path):
        out.append(list(path))
        for j in range(i, len(nums)):
            path.append(nums[j])
            build(j + 1, path)
            path.pop()

    build(0, [])
    return out
""",
    },
    {
        "id": "a042",
        "problem_slug": "combination-sum-ii",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.duplicates_not_deduped",
        "code": """\
def combinationSum2(candidates, target):
    candidates.sort()
    out = []

    def build(i, remaining, path):
        if remaining == 0:
            out.append(list(path))
            return
        for j in range(i, len(candidates)):
            if candidates[j] > remaining:
                break
            path.append(candidates[j])
            build(j + 1, remaining - candidates[j], path)
            path.pop()

    build(0, target, [])
    return out
""",
    },
    {
        "id": "a043",
        "problem_slug": "permutations",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.backtracking_state_not_restored",
        "code": """\
def permute(nums):
    out = []

    def build(path, used):
        if len(path) == len(nums):
            out.append(list(path))
            return
        for i, n in enumerate(nums):
            if i in used:
                continue
            used.add(i)
            path.append(n)
            build(path, used)
            path.pop()

    build([], set())
    return out
""",
    },
    {
        "id": "a044",
        "problem_slug": "word-search",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.backtracking_state_not_restored",
        "code": """\
def exist(board, word):
    rows, cols = len(board), len(board[0])
    seen = set()

    def dfs(r, c, i):
        if i == len(word):
            return True
        if r < 0 or c < 0 or r >= rows or c >= cols:
            return False
        if (r, c) in seen or board[r][c] != word[i]:
            return False
        seen.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if dfs(r + dr, c + dc, i + 1):
                return True
        return False

    return any(dfs(r, c, 0) for r in range(rows) for c in range(cols))
""",
    },
    {
        "id": "a045",
        "problem_slug": "subsets",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.mutable_reference_stored_instead_of_copy",
        "code": """\
def subsets(nums):
    out = []
    path = []

    def build(i):
        out.append(path)
        for j in range(i, len(nums)):
            path.append(nums[j])
            build(j + 1)
            path.pop()

    build(0)
    return out
""",
    },
    {
        "id": "a046",
        "problem_slug": "generate-parentheses",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.mutable_reference_stored_instead_of_copy",
        "code": """\
def generateParenthesis(n):
    out = []
    cur = []

    def build(open_count, close_count):
        if len(cur) == 2 * n:
            out.append(cur)
            return
        if open_count < n:
            cur.append("(")
            build(open_count + 1, close_count)
            cur.pop()
        if close_count < open_count:
            cur.append(")")
            build(open_count, close_count + 1)
            cur.pop()

    build(0, 0)
    return ["".join(x) for x in out]
""",
    },
    {
        "id": "a047",
        "problem_slug": "partition-equal-subset-sum",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.dp_iteration_order_wrong",
        "code": """\
def canPartition(nums):
    total = sum(nums)
    if total % 2:
        return False
    half = total // 2
    dp = [False] * (half + 1)
    dp[0] = True
    for n in nums:
        for cap in range(n, half + 1):
            if dp[cap - n]:
                dp[cap] = True
    return dp[half]
""",
    },
    {
        "id": "a048",
        "problem_slug": "coin-change-ii",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.dp_iteration_order_wrong",
        "code": """\
def change(amount, coins):
    dp = [0] * (amount + 1)
    dp[0] = 1
    for total in range(1, amount + 1):
        for c in coins:
            if c <= total:
                dp[total] += dp[total - c]
    return dp[amount]
""",
    },
    {
        "id": "a049",
        "problem_slug": "climbing-stairs",
        "language": "python",
        "failure_type": "runtime_error",
        "pattern_id": "implementation.dp_base_case_or_dimensions_wrong",
        "code": """\
def climbStairs(n):
    dp = [0] * n
    dp[0] = 1
    dp[1] = 2
    for i in range(2, n):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n - 1]
""",
    },
    {
        "id": "a050",
        "problem_slug": "coin-change",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.dp_base_case_or_dimensions_wrong",
        "code": """\
def coinChange(coins, amount):
    dp = [0] * (amount + 1)
    for i in range(1, amount + 1):
        best = 0
        for c in coins:
            if c <= i:
                best = min(best, dp[i - c] + 1)
        dp[i] = best
    return dp[amount]
""",
    },
    {
        "id": "a051",
        "problem_slug": "two-sum-ii-input-array-is-sorted",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.two_pointer_advance_condition_wrong",
        "code": """\
def twoSum(numbers, target):
    lo, hi = 0, len(numbers) - 1
    while lo < hi:
        total = numbers[lo] + numbers[hi]
        if total == target:
            return [lo + 1, hi + 1]
        lo += 1
        hi -= 1
    return []
""",
    },
    {
        "id": "a052",
        "problem_slug": "longest-repeating-character-replacement",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.two_pointer_advance_condition_wrong",
        "code": """\
from collections import Counter


def characterReplacement(s, k):
    counts = Counter()
    left = 0
    best = 0
    for right, ch in enumerate(s):
        counts[ch] += 1
        window = right - left + 1
        if window - max(counts.values()) > k:
            counts[s[left]] -= 1
        best = max(best, right - left + 1)
    return best
""",
    },
    {
        "id": "a053",
        "problem_slug": "kth-largest-element-in-an-array",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.heap_wrong_polarity",
        "code": """\
import heapq


def findKthLargest(nums, k):
    heap = []
    for n in nums:
        heapq.heappush(heap, n)
        if len(heap) > k:
            heapq.heappop(heap)
    return heapq.heappop(heap) if heap else -1
""",
    },
    {
        "id": "a054",
        "problem_slug": "last-stone-weight",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.heap_wrong_polarity",
        "code": """\
import heapq


def lastStoneWeight(stones):
    heapq.heapify(stones)
    while len(stones) > 1:
        a = heapq.heappop(stones)
        b = heapq.heappop(stones)
        if a != b:
            heapq.heappush(stones, abs(a - b))
    return stones[0] if stones else 0
""",
    },
    {
        "id": "a055",
        "problem_slug": "largest-number",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.custom_comparator_wrong",
        "code": """\
def largestNumber(nums):
    parts = sorted((str(n) for n in nums), reverse=True)
    out = "".join(parts)
    return out.lstrip("0") or "0"
""",
    },
    {
        "id": "a056",
        "problem_slug": "meeting-rooms-ii",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.custom_comparator_wrong",
        "code": """\
import heapq


def minMeetingRooms(intervals):
    intervals.sort(key=lambda x: x[1])
    rooms = []
    for start, end in intervals:
        if rooms and rooms[0] <= start:
            heapq.heapreplace(rooms, end)
        else:
            heapq.heappush(rooms, end)
    return len(rooms)
""",
    },
    {
        "id": "a057",
        "problem_slug": "reverse-linked-list",
        "language": "python",
        "failure_type": "runtime_error",
        "pattern_id": "implementation.linked_list_pointer_loss",
        "code": """\
def reverseList(head):
    prev = None
    cur = head
    while cur:
        cur.next = prev
        prev = cur
        cur = cur.next
    return prev
""",
    },
    {
        "id": "a058",
        "problem_slug": "remove-nth-node-from-end-of-list",
        "language": "python",
        "failure_type": "runtime_error",
        "pattern_id": "implementation.linked_list_pointer_loss",
        "code": """\
def removeNthFromEnd(head, n):
    fast = head
    for _ in range(n):
        fast = fast.next
    slow = head
    while fast.next:
        fast = fast.next
        slow = slow.next
    slow.next = slow.next.next
    return head
""",
    },
    {
        "id": "a059",
        "problem_slug": "remove-element",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.in_place_mutation_while_iterating",
        "code": """\
def removeElement(nums, val):
    for i in range(len(nums)):
        if i < len(nums) and nums[i] == val:
            nums.remove(val)
    return len(nums)
""",
    },
    {
        "id": "a060",
        "problem_slug": "move-zeroes",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.in_place_mutation_while_iterating",
        "code": """\
def moveZeroes(nums):
    for i, n in enumerate(nums):
        if n == 0:
            nums.pop(i)
            nums.append(0)
""",
    },
    {
        "id": "a061",
        "problem_slug": "binary-search",
        "language": "java",
        "failure_type": "runtime_error",
        "pattern_id": "implementation.integer_overflow_or_precision_loss",
        "code": """\
class Solution {
    public int search(int[] nums, int target) {
        int lo = 0, hi = nums.length - 1;
        while (lo <= hi) {
            int mid = (lo + hi) / 2;
            if (nums[mid] == target) return mid;
            if (nums[mid] < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return -1;
    }
}
""",
    },
    {
        "id": "a062",
        "problem_slug": "multiply-strings",
        "language": "java",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.integer_overflow_or_precision_loss",
        "code": """\
class Solution {
    public String multiply(String num1, String num2) {
        int a = Integer.parseInt(num1);
        int b = Integer.parseInt(num2);
        return String.valueOf(a * b);
    }
}
""",
    },
    {
        "id": "a063",
        "problem_slug": "number-of-islands",
        "language": "python",
        "failure_type": "runtime_error",
        "pattern_id": "implementation.grid_bounds_or_direction_error",
        "code": """\
def numIslands(grid):
    rows, cols = len(grid), len(grid[0])

    def sink(r, c):
        if grid[r][c] != "1":
            return
        grid[r][c] = "0"
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sink(r + dr, c + dc)

    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1":
                sink(r, c)
                count += 1
    return count
""",
    },
    {
        "id": "a064",
        "problem_slug": "rotate-image",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.grid_bounds_or_direction_error",
        "code": """\
def rotate(matrix):
    rows = len(matrix)
    cols = len(matrix[0])
    for r in range(rows):
        for c in range(cols):
            matrix[r][c], matrix[c][r] = matrix[c][r], matrix[r][c]
    for row in matrix:
        row.reverse()
""",
    },
    {
        "id": "a065",
        "problem_slug": "validate-binary-search-tree",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.recursion_base_case_wrong",
        "code": """\
def isValidBST(root):
    if root is None:
        return True
    if root.left and root.left.val >= root.val:
        return False
    if root.right and root.right.val <= root.val:
        return False
    return isValidBST(root.left) and isValidBST(root.right)
""",
    },
    {
        "id": "a066",
        "problem_slug": "search-in-rotated-sorted-array",
        "language": "go",
        "failure_type": "wrong_answer",
        "pattern_id": "implementation.binary_search_bounds_off_by_one",
        "code": """\
func search(nums []int, target int) int {
    lo, hi := 0, len(nums)
    for lo < hi {
        mid := (lo + hi) / 2
        if nums[mid] == target {
            return mid
        }
        if nums[lo] <= nums[mid] {
            if nums[lo] <= target && target < nums[mid] {
                hi = mid - 1
            } else {
                lo = mid + 1
            }
        } else {
            if nums[mid] < target && target <= nums[hi] {
                lo = mid + 1
            } else {
                hi = mid - 1
            }
        }
    }
    return -1
}
""",
    },
]
