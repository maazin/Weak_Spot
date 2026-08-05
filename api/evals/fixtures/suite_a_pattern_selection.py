"""Suite A cases labelled `pattern_selection` — wrong algorithmic shape chosen.

Each case is a failing attempt plus the true `pattern_id`. Labels were written before
the diagnoser existed, so they record what actually went wrong rather than what a model
was observed to say.
"""

from __future__ import annotations

CASES: list[dict] = [
    {
        "id": "a001",
        "problem_slug": "two-sum-ii-input-array-is-sorted",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "pattern_selection.hashmap_over_two_pointers",
        "code": """\
def twoSum(numbers, target):
    seen = {}
    for i, n in enumerate(numbers):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
""",
    },
    {
        "id": "a002",
        "problem_slug": "3sum",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.hashmap_over_two_pointers",
        "code": """\
def threeSum(nums):
    nums.sort()
    out = set()
    for i in range(len(nums)):
        seen = {}
        for j in range(i + 1, len(nums)):
            need = -nums[i] - nums[j]
            if need in seen:
                out.add((nums[i], need, nums[j]))
            seen[nums[j]] = j
    return [list(t) for t in out]
""",
    },
    {
        "id": "a003",
        "problem_slug": "merge-intervals",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "pattern_selection.sorting_unlocks_linear",
        "code": """\
def merge(intervals):
    out = []
    for a in intervals:
        placed = False
        for b in out:
            if a[0] <= b[1] and b[0] <= a[1]:
                b[0] = min(b[0], a[0])
                b[1] = max(b[1], a[1])
                placed = True
                break
        if not placed:
            out.append(a)
    return out
""",
    },
    {
        "id": "a004",
        "problem_slug": "maximum-gap",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.sorting_unlocks_linear",
        "code": """\
def maximumGap(nums):
    best = 0
    for i in range(len(nums)):
        for j in range(len(nums)):
            if i != j:
                best = max(best, abs(nums[i] - nums[j]))
    return best
""",
    },
    {
        "id": "a005",
        "problem_slug": "coin-change",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "pattern_selection.greedy_over_dp",
        "code": """\
def coinChange(coins, amount):
    coins.sort(reverse=True)
    count = 0
    for c in coins:
        while amount >= c:
            amount -= c
            count += 1
    return count if amount == 0 else -1
""",
    },
    {
        "id": "a006",
        "problem_slug": "house-robber",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "pattern_selection.greedy_over_dp",
        "code": """\
def rob(nums):
    total = 0
    i = 0
    while i < len(nums):
        if i + 1 < len(nums) and nums[i + 1] > nums[i]:
            total += nums[i + 1]
            i += 3
        else:
            total += nums[i]
            i += 2
    return total
""",
    },
    {
        "id": "a007",
        "problem_slug": "partition-equal-subset-sum",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "pattern_selection.greedy_over_dp",
        "code": """\
def canPartition(nums):
    total = sum(nums)
    if total % 2:
        return False
    half = total // 2
    nums.sort(reverse=True)
    acc = 0
    for n in nums:
        if acc + n <= half:
            acc += n
    return acc == half
""",
    },
    {
        "id": "a008",
        "problem_slug": "shortest-path-in-binary-matrix",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "pattern_selection.dfs_over_bfs_shortest_path",
        "code": """\
def shortestPathBinaryMatrix(grid):
    n = len(grid)
    best = [10 ** 9]

    def dfs(r, c, d, seen):
        if r < 0 or c < 0 or r >= n or c >= n or grid[r][c] or (r, c) in seen:
            return
        if r == n - 1 and c == n - 1:
            best[0] = min(best[0], d)
            return
        seen.add((r, c))
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                dfs(r + dr, c + dc, d + 1, seen)
        seen.discard((r, c))

    dfs(0, 0, 1, set())
    return best[0] if best[0] < 10 ** 9 else -1
""",
    },
    {
        "id": "a009",
        "problem_slug": "word-ladder",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.dfs_over_bfs_shortest_path",
        "code": """\
def ladderLength(beginWord, endWord, wordList):
    words = set(wordList)
    best = [0]

    def dfs(word, depth, used):
        if word == endWord:
            best[0] = depth if best[0] == 0 else min(best[0], depth)
            return
        for w in list(words):
            if w in used:
                continue
            diff = sum(1 for a, b in zip(word, w) if a != b)
            if diff == 1:
                used.add(w)
                dfs(w, depth + 1, used)
                used.discard(w)

    dfs(beginWord, 1, {beginWord})
    return best[0]
""",
    },
    {
        "id": "a010",
        "problem_slug": "longest-substring-without-repeating-characters",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.nested_loops_over_sliding_window",
        "code": """\
def lengthOfLongestSubstring(s):
    best = 0
    for i in range(len(s)):
        for j in range(i, len(s)):
            chunk = s[i:j + 1]
            if len(set(chunk)) == len(chunk):
                best = max(best, len(chunk))
    return best
""",
    },
    {
        "id": "a011",
        "problem_slug": "minimum-size-subarray-sum",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.nested_loops_over_sliding_window",
        "code": """\
def minSubArrayLen(target, nums):
    best = len(nums) + 1
    for i in range(len(nums)):
        total = 0
        for j in range(i, len(nums)):
            total += nums[j]
            if total >= target:
                best = min(best, j - i + 1)
                break
    return best if best <= len(nums) else 0
""",
    },
    {
        "id": "a012",
        "problem_slug": "find-all-anagrams-in-a-string",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.nested_loops_over_sliding_window",
        "code": """\
from collections import Counter


def findAnagrams(s, p):
    target = Counter(p)
    out = []
    for i in range(len(s) - len(p) + 1):
        if Counter(s[i:i + len(p)]) == target:
            out.append(i)
    return out
""",
    },
    {
        "id": "a013",
        "problem_slug": "search-insert-position",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.linear_scan_over_binary_search",
        "code": """\
def searchInsert(nums, target):
    for i, n in enumerate(nums):
        if n >= target:
            return i
    return len(nums)
""",
    },
    {
        "id": "a014",
        "problem_slug": "find-first-and-last-position-of-element-in-sorted-array",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.linear_scan_over_binary_search",
        "code": """\
def searchRange(nums, target):
    first = -1
    last = -1
    for i, n in enumerate(nums):
        if n == target:
            if first == -1:
                first = i
            last = i
    return [first, last]
""",
    },
    {
        "id": "a015",
        "problem_slug": "koko-eating-bananas",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.exhaustive_search_over_binary_search_on_answer",
        "code": """\
import math


def minEatingSpeed(piles, h):
    speed = 1
    while True:
        hours = sum(math.ceil(p / speed) for p in piles)
        if hours <= h:
            return speed
        speed += 1
""",
    },
    {
        "id": "a016",
        "problem_slug": "capacity-to-ship-packages-within-d-days",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.exhaustive_search_over_binary_search_on_answer",
        "code": """\
def shipWithinDays(weights, days):
    cap = max(weights)
    while True:
        used = 1
        cur = 0
        for w in weights:
            if cur + w > cap:
                used += 1
                cur = 0
            cur += w
        if used <= days:
            return cap
        cap += 1
""",
    },
    {
        "id": "a017",
        "problem_slug": "kth-largest-element-in-an-array",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.sorting_over_heap_for_top_k",
        "code": """\
def findKthLargest(nums, k):
    return sorted(nums, reverse=True)[k - 1]
""",
    },
    {
        "id": "a018",
        "problem_slug": "top-k-frequent-elements",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.sorting_over_heap_for_top_k",
        "code": """\
from collections import Counter


def topKFrequent(nums, k):
    counts = Counter(nums)
    ordered = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    return [key for key, _ in ordered[:k]]
""",
    },
    {
        "id": "a019",
        "problem_slug": "number-of-connected-components-in-an-undirected-graph",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.visited_set_over_union_find",
        "code": """\
def countComponents(n, edges):
    count = 0
    for start in range(n):
        reached = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node in reached:
                continue
            reached.add(node)
            for a, b in edges:
                if a == node:
                    stack.append(b)
                if b == node:
                    stack.append(a)
        if min(reached) == start:
            count += 1
    return count
""",
    },
    {
        "id": "a020",
        "problem_slug": "redundant-connection",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.visited_set_over_union_find",
        "code": """\
def findRedundantConnection(edges):
    adj = {}
    for a, b in edges:
        seen = set()
        stack = [a]
        while stack:
            node = stack.pop()
            if node == b:
                return [a, b]
            if node in seen:
                continue
            seen.add(node)
            stack.extend(adj.get(node, []))
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    return []
""",
    },
    {
        "id": "a021",
        "problem_slug": "daily-temperatures",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.brute_force_over_monotonic_stack",
        "code": """\
def dailyTemperatures(temperatures):
    out = [0] * len(temperatures)
    for i in range(len(temperatures)):
        for j in range(i + 1, len(temperatures)):
            if temperatures[j] > temperatures[i]:
                out[i] = j - i
                break
    return out
""",
    },
    {
        "id": "a022",
        "problem_slug": "largest-rectangle-in-histogram",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.brute_force_over_monotonic_stack",
        "code": """\
def largestRectangleArea(heights):
    best = 0
    for i in range(len(heights)):
        lo = heights[i]
        for j in range(i, len(heights)):
            lo = min(lo, heights[j])
            best = max(best, lo * (j - i + 1))
    return best
""",
    },
    {
        "id": "a023",
        "problem_slug": "range-sum-query-immutable",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.recompute_over_prefix_sum",
        "code": """\
class NumArray:
    def __init__(self, nums):
        self.nums = nums

    def sumRange(self, left, right):
        total = 0
        for i in range(left, right + 1):
            total += self.nums[i]
        return total
""",
    },
    {
        "id": "a024",
        "problem_slug": "subarray-sum-equals-k",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.recompute_over_prefix_sum",
        "code": """\
def subarraySum(nums, k):
    count = 0
    for i in range(len(nums)):
        for j in range(i, len(nums)):
            if sum(nums[i:j + 1]) == k:
                count += 1
    return count
""",
    },
    {
        "id": "a025",
        "problem_slug": "evaluate-division",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "pattern_selection.missed_graph_modeling",
        "code": """\
def calcEquation(equations, values, queries):
    direct = {}
    for (a, b), v in zip(equations, values):
        direct[(a, b)] = v
        direct[(b, a)] = 1 / v
    out = []
    for a, b in queries:
        if a == b and (a, a) in direct:
            out.append(1.0)
        elif (a, b) in direct:
            out.append(direct[(a, b)])
        else:
            out.append(-1.0)
    return out
""",
    },
    {
        "id": "a026",
        "problem_slug": "open-the-lock",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "pattern_selection.missed_graph_modeling",
        "code": """\
def openLock(deadends, target):
    dead = set(deadends)
    if "0000" in dead:
        return -1
    moves = 0
    cur = "0000"
    for i in range(4):
        want = int(target[i])
        have = int(cur[i])
        step = min((want - have) % 10, (have - want) % 10)
        moves += step
        cur = cur[:i] + target[i] + cur[i + 1:]
        if cur in dead:
            return -1
    return moves
""",
    },
    {
        "id": "a027",
        "problem_slug": "course-schedule-ii",
        "language": "python",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.missed_topological_sort",
        "code": """\
def findOrder(numCourses, prerequisites):
    order = []
    done = set()
    changed = True
    while changed and len(order) < numCourses:
        changed = False
        for c in range(numCourses):
            if c in done:
                continue
            if all(p in done for a, p in prerequisites if a == c):
                order.append(c)
                done.add(c)
                changed = True
    return order if len(order) == numCourses else []
""",
    },
    {
        "id": "a028",
        "problem_slug": "alien-dictionary",
        "language": "python",
        "failure_type": "wrong_answer",
        "pattern_id": "pattern_selection.missed_topological_sort",
        "code": """\
def alienOrder(words):
    seen = []
    for w in words:
        for ch in w:
            if ch not in seen:
                seen.append(ch)
    return "".join(seen)
""",
    },
    {
        "id": "a029",
        "problem_slug": "container-with-most-water",
        "language": "java",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.nested_loops_over_sliding_window",
        "code": """\
class Solution {
    public int maxArea(int[] height) {
        int best = 0;
        for (int i = 0; i < height.length; i++) {
            for (int j = i + 1; j < height.length; j++) {
                int area = Math.min(height[i], height[j]) * (j - i);
                best = Math.max(best, area);
            }
        }
        return best;
    }
}
""",
    },
    {
        "id": "a030",
        "problem_slug": "kth-largest-element-in-an-array",
        "language": "cpp",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.sorting_over_heap_for_top_k",
        "code": """\
class Solution {
public:
    int findKthLargest(vector<int>& nums, int k) {
        sort(nums.begin(), nums.end(), greater<int>());
        return nums[k - 1];
    }
};
""",
    },
    {
        "id": "a031",
        "problem_slug": "number-of-provinces",
        "language": "go",
        "failure_type": "tle",
        "pattern_id": "pattern_selection.visited_set_over_union_find",
        "code": """\
func findCircleNum(isConnected [][]int) int {
    n := len(isConnected)
    count := 0
    for start := 0; start < n; start++ {
        reached := map[int]bool{}
        stack := []int{start}
        for len(stack) > 0 {
            node := stack[len(stack)-1]
            stack = stack[:len(stack)-1]
            if reached[node] {
                continue
            }
            reached[node] = true
            for j := 0; j < n; j++ {
                if isConnected[node][j] == 1 {
                    stack = append(stack, j)
                }
            }
        }
        smallest := start
        for k := range reached {
            if k < smallest {
                smallest = k
            }
        }
        if smallest == start {
            count++
        }
    }
    return count
}
""",
    },
    {
        "id": "a032",
        "problem_slug": "jump-game-ii",
        "language": "javascript",
        "failure_type": "wrong_answer",
        "pattern_id": "pattern_selection.greedy_over_dp",
        "code": """\
var jump = function(nums) {
    let steps = 0;
    let i = 0;
    while (i < nums.length - 1) {
        i += nums[i];
        steps += 1;
    }
    return steps;
};
""",
    },
]
