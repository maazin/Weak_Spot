"""Suite B — 60 human-rated explanations for judge calibration.

Ratings are 1-5 on three dimensions: `clarity`, `correctness`, and `avoids_solution`
(5 meaning it hands over nothing pasteable). The set is deliberately spread across the
scale — a calibration set of only good explanations produces a meaningless kappa,
because a judge that always answers 5 would score perfectly.

Roughly: a third are strong, a third are mediocre in a specific way (vague, hedged,
generic), and a third fail hard (wrong diagnosis, or solution code handed over).
"""

from __future__ import annotations


def _c(pattern_id: str, text: str, clarity: int, correctness: int, avoids: int) -> dict:
    return {
        "pattern_id": pattern_id,
        "explanation": text,
        "human": {
            "clarity": clarity,
            "correctness": correctness,
            "avoids_solution": avoids,
        },
    }


CASES: list[dict] = [
    # ---------- strong explanations ----------
    _c(
        "pattern_selection.hashmap_over_two_pointers",
        "The constraints tell you the array is already sorted, and your solution never "
        "uses that. Building a hash map of every element you have seen buys you a linear "
        "scan you already had for free, at the cost of linear extra memory. With sorted "
        "input, two indices walking inward let each comparison tell you which side to "
        "move.",
        5,
        5,
        5,
    ),
    _c(
        "complexity.missing_memoization",
        "Your recursion is correct but recomputes the same arguments across branches: "
        "the call for n-2 happens inside both the n-1 and n-2 subtrees. That turns a "
        "problem with n distinct states into an exponential number of calls. Caching "
        "results by argument collapses the tree to the number of distinct states.",
        5,
        5,
        5,
    ),
    _c(
        "implementation.binary_search_bounds_off_by_one",
        "Your high bound starts at len(nums), which is one past the last valid index, "
        "but the loop condition treats it as inclusive. On the iteration where mid lands "
        "there, the index is out of range. Pick one convention — inclusive high with <=, "
        "or exclusive high with < — and apply it to both the bound and the loop test.",
        5,
        5,
        5,
    ),
    _c(
        "implementation.bfs_visited_marked_on_dequeue",
        "You mark a cell visited after popping it rather than before pushing it. In a "
        "breadth-first search several neighbours in the same layer discover the same "
        "cell, so each one pushes its own copy before any is processed. The queue fills "
        "with duplicates. Treat membership in the visited set as 'already scheduled'.",
        5,
        5,
        5,
    ),
    _c(
        "comprehension.missed_negative_values",
        "Seeding your running maximum at zero assumes some subarray sums to at least "
        "zero. When every value is negative, the answer should be the largest single "
        "element, and your code returns zero instead. Seed from the first element rather "
        "than from a neutral value.",
        5,
        5,
        5,
    ),
    _c(
        "implementation.backtracking_state_not_restored",
        "You add the index to the used set before recursing but never remove it "
        "afterwards, so once a branch has consumed an index no sibling branch can use it "
        "again. Every change made before a recursive call needs an exact inverse after "
        "it — the working state belongs to the current path only.",
        5,
        5,
        5,
    ),
    _c(
        "complexity.list_membership_scan",
        "The membership test on line 3 searches a list, which walks it element by "
        "element. Inside your loop that is a nested loop that does not look like one, "
        "which is exactly why it survives review. The container type is the whole fix.",
        5,
        5,
        5,
    ),
    _c(
        "pattern_selection.greedy_over_dp",
        "Taking the largest coin that fits at each step is a local choice you cannot "
        "justify globally: spending a large coin early can leave a remainder that no "
        "combination of smaller coins reaches, even though a different early choice "
        "would have worked. Greed is only safe when you can state why the local pick is "
        "part of some optimal answer.",
        5,
        5,
        5,
    ),
    _c(
        "implementation.mutable_reference_stored_instead_of_copy",
        "You append the working list itself into your results, which stores a pointer "
        "rather than a snapshot. Every later mutation of that list is visible through "
        "every reference already stored, so all your results end up equal to the final "
        "state. Store a copy at the moment of storage.",
        5,
        5,
        5,
    ),
    _c(
        "comprehension.missed_return_format",
        "Your algorithm finds the right pair, but the problem asks for their indices and "
        "you return the values. The computation is correct and the shape is not — check "
        "indices versus values, and zero- versus one-based, before you start.",
        5,
        5,
        5,
    ),
    _c(
        "complexity.string_concat_in_loop",
        "Each concatenation allocates a new string and copies everything accumulated so "
        "far, so building an n-character result one piece at a time costs quadratic time. "
        "That is why this passes the small tests and dies only on the largest. Collect "
        "the pieces and join once at the end.",
        5,
        5,
        5,
    ),
    _c(
        "implementation.dp_iteration_order_wrong",
        "You flattened the table to one dimension but sweep the capacity upward, so a "
        "cell you already updated in this pass is read again for the same item. That "
        "silently permits reusing an item you are allowed to use once. The traversal "
        "direction is what enforces the constraint here.",
        5,
        5,
        5,
    ),
    _c(
        "pattern_selection.dfs_over_bfs_shortest_path",
        "The problem asks for the fewest moves and the edges are unweighted, but you "
        "explore depth-first. The first time a depth-first search reaches a node may be "
        "down a long detour, so it gives no shortest-path guarantee. A layer-by-layer "
        "traversal reaches every node by a path of the fewest possible edges.",
        5,
        5,
        5,
    ),
    _c(
        "comprehension.missed_empty_or_single_element_case",
        "Line 2 reads the first element before anything checks the length, so an empty "
        "input raises before your logic runs. Your guard at the end is correct but comes "
        "too late to help. Decide what the answer is for an empty input and assert it at "
        "the top.",
        5,
        5,
        5,
    ),
    _c(
        "implementation.two_pointer_advance_condition_wrong",
        "You move both pointers on every iteration regardless of the comparison, so the "
        "pair you actually need is skipped whenever it does not sit symmetrically. On a "
        "sorted pair search, which pointer moves has to follow from whether the current "
        "sum is too small or too large.",
        5,
        5,
        5,
    ),
    _c(
        "comprehension.misread_subsequence_vs_subarray",
        "You are tracking a contiguous run, but the problem allows skipping elements. "
        "Contiguity is what makes a running scan valid; a subsequence permits gaps, so "
        "each state has to consider every earlier index. This is a confident solution to "
        "a different problem.",
        5,
        5,
        5,
    ),
    _c(
        "complexity.front_insertion_or_removal_on_array",
        "You use a list as a queue and remove from index zero, which shifts every "
        "remaining element and costs linear time per operation. Inside your loop that is "
        "quadratic. A structure with constant-time removal at both ends is the fix.",
        5,
        5,
        5,
    ),
    _c(
        "implementation.recursion_base_case_wrong",
        "Your base case stops the descent but returns a value that breaks the combining "
        "step for the smallest input. A base case has to do both jobs: terminate, and "
        "return the identity that makes the caller's arithmetic come out right at size "
        "zero and size one.",
        5,
        5,
        5,
    ),
    _c(
        "comprehension.missed_modulo_requirement",
        "The problem asks for the answer modulo a value, which is telling you the true "
        "count overflows. You apply the modulus only to the final return, by which point "
        "the intermediate value has already wrapped. It belongs at every addition along "
        "the way.",
        5,
        5,
        5,
    ),
    _c(
        "pattern_selection.brute_force_over_monotonic_stack",
        "For each index you scan forward looking for a larger value, which is quadratic. "
        "The structure you are missing is that once an element has a larger neighbour to "
        "its right it can never be the answer for anything further right, so it can be "
        "discarded permanently.",
        5,
        5,
        5,
    ),
    # ---------- mediocre: correct but vague, generic, or hedged ----------
    _c(
        "complexity.missing_memoization",
        "Your solution is too slow. Consider using dynamic programming to speed it up.",
        2,
        4,
        5,
    ),
    _c(
        "pattern_selection.hashmap_over_two_pointers",
        "A two pointer approach would probably be better here than what you did.",
        2,
        4,
        5,
    ),
    _c(
        "implementation.binary_search_bounds_off_by_one",
        "There is an off-by-one error somewhere in your binary search bounds. Check the "
        "loop carefully.",
        2,
        4,
        5,
    ),
    _c(
        "complexity.recompute_inside_loop",
        "You are doing extra work inside the loop. Try to avoid that and it should be faster.",
        2,
        4,
        5,
    ),
    _c(
        "implementation.duplicates_not_deduped",
        "The output has duplicates in it. You should handle duplicate values.",
        2,
        4,
        5,
    ),
    _c(
        "comprehension.missed_constraint_bound",
        "Read the constraints more carefully next time. The input can be quite large.",
        2,
        3,
        5,
    ),
    _c(
        "pattern_selection.sorting_unlocks_linear",
        "Sorting the input first tends to help with problems like this one. Worth trying.",
        3,
        3,
        5,
    ),
    _c(
        "implementation.heap_wrong_polarity",
        "Your heap is the wrong way round. Python's heapq is a min-heap, so think about "
        "what that means for your problem.",
        3,
        4,
        5,
    ),
    _c(
        "complexity.exponential_recursion_branching",
        "This branches too much and will time out on larger inputs. You need to prune or "
        "memoise, depending on the problem.",
        3,
        4,
        5,
    ),
    _c(
        "comprehension.missed_negative_values",
        "Negative numbers break your assumption. Think about what happens when all the "
        "values are below zero.",
        3,
        5,
        5,
    ),
    _c(
        "implementation.dp_base_case_or_dimensions_wrong",
        "Your dp array is sized wrong. Usually you want n plus one.",
        3,
        4,
        5,
    ),
    _c(
        "pattern_selection.linear_scan_over_binary_search",
        "This is linear when it could be logarithmic. The array is sorted, so use that.",
        3,
        5,
        5,
    ),
    _c(
        "implementation.grid_bounds_or_direction_error",
        "There is an indexing problem in the grid traversal. Check your bounds.",
        2,
        4,
        5,
    ),
    _c(
        "complexity.repeated_slicing",
        "Slicing in a recursion is expensive. Consider passing indices instead.",
        3,
        5,
        5,
    ),
    _c(
        "comprehension.missed_tiebreak_rule",
        "You are not handling ties the way the problem wants. Re-read the statement.",
        2,
        4,
        5,
    ),
    _c(
        "implementation.custom_comparator_wrong",
        "The sort key does not capture the ordering you need. It is more subtle than "
        "sorting the strings directly.",
        3,
        4,
        5,
    ),
    _c(
        "pattern_selection.visited_set_over_union_find",
        "Union-find would be a better fit for this kind of connectivity question.",
        3,
        4,
        5,
    ),
    _c(
        "complexity.sort_inside_loop",
        "Sorting inside the loop is the bottleneck. Move it or use a different structure.",
        3,
        5,
        5,
    ),
    _c(
        "implementation.linked_list_pointer_loss",
        "You lose the rest of the list when you rewire. Save the next pointer first.",
        4,
        5,
        5,
    ),
    _c(
        "comprehension.missed_in_place_requirement",
        "The problem wants an in-place modification and you build a new list.",
        3,
        5,
        5,
    ),
    # ---------- weak: wrong diagnosis, or hands over the solution ----------
    _c(
        "complexity.missing_memoization",
        "Add a cache decorator above your function and it will pass:\n\n"
        "```python\nfrom functools import cache\n\n@cache\ndef fib(n):\n"
        "    if n < 2:\n        return n\n    return fib(n - 1) + fib(n - 2)\n```",
        4,
        5,
        1,
    ),
    _c(
        "pattern_selection.hashmap_over_two_pointers",
        "Here is the correct version:\n\n```python\ndef twoSum(numbers, target):\n"
        "    lo, hi = 0, len(numbers) - 1\n    while lo < hi:\n"
        "        s = numbers[lo] + numbers[hi]\n        if s == target:\n"
        "            return [lo + 1, hi + 1]\n        if s < target:\n"
        "            lo += 1\n        else:\n            hi -= 1\n    return []\n```",
        4,
        5,
        1,
    ),
    _c(
        "implementation.binary_search_bounds_off_by_one",
        "Change your code to this and it works:\n\n```python\nlo, hi = 0, len(nums) - 1\n"
        "while lo <= hi:\n    mid = (lo + hi) // 2\n    if nums[mid] == target:\n"
        "        return mid\n    elif nums[mid] < target:\n        lo = mid + 1\n"
        "    else:\n        hi = mid - 1\nreturn -1\n```",
        4,
        5,
        1,
    ),
    _c(
        "complexity.list_membership_scan",
        "Just replace your list with a set:\n\n```python\nseen = set()\nfor n in nums:\n"
        "    if n in seen:\n        return True\n    seen.add(n)\nreturn False\n```",
        4,
        5,
        2,
    ),
    _c(
        "pattern_selection.nested_loops_over_sliding_window",
        "The full sliding window implementation you want:\n\n```python\n"
        "left = 0\nseen = set()\nbest = 0\nfor right, ch in enumerate(s):\n"
        "    while ch in seen:\n        seen.remove(s[left])\n        left += 1\n"
        "    seen.add(ch)\n    best = max(best, right - left + 1)\nreturn best\n```",
        4,
        5,
        1,
    ),
    _c(
        "implementation.dp_iteration_order_wrong",
        "Flip the inner loop:\n\n```python\nfor n in nums:\n"
        "    for cap in range(half, n - 1, -1):\n        dp[cap] |= dp[cap - n]\n```\n"
        "That is the whole fix.",
        4,
        5,
        2,
    ),
    _c(
        "complexity.string_concat_in_loop",
        "Your problem is that the input is not sorted, so the two pointer approach cannot "
        "work here. Sort it first and the concatenation will be fine.",
        3,
        1,
        5,
    ),
    _c(
        "implementation.bfs_visited_marked_on_dequeue",
        "The issue is that you are using a hash map where an array would do. Memory is "
        "the constraint being violated, not the traversal order.",
        3,
        1,
        5,
    ),
    _c(
        "comprehension.missed_return_format",
        "This is a complexity problem: your solution is quadratic and needs to be linear "
        "to pass the time limit.",
        3,
        1,
        5,
    ),
    _c(
        "pattern_selection.greedy_over_dp",
        "Your base case is wrong. The recursion should return 1 rather than 0 when the "
        "input is empty.",
        3,
        1,
        5,
    ),
    _c(
        "complexity.missing_memoization",
        "The gap here is that you misread the return format — the problem wants indices "
        "and you are returning values.",
        3,
        1,
        5,
    ),
    _c(
        "implementation.backtracking_state_not_restored",
        "You need to sort the input first. Without sorting, the duplicate detection cannot work.",
        3,
        2,
        5,
    ),
    _c(
        "comprehension.missed_sorted_input_guarantee",
        "Something is wrong here.",
        1,
        2,
        5,
    ),
    _c(
        "implementation.recursion_base_case_wrong",
        "Try again.",
        1,
        1,
        5,
    ),
    _c(
        "complexity.recompute_inside_loop",
        "Consider the problem more deeply and think about what data structure would be "
        "most appropriate given the constraints and the shape of the input as described.",
        1,
        2,
        5,
    ),
    _c(
        "pattern_selection.missed_graph_modeling",
        "Model it as a graph. Nodes are states and edges are transitions. Here is the "
        "skeleton:\n\n```python\nfrom collections import deque\nq = deque([(start, 0)])\n"
        "seen = {start}\nwhile q:\n    node, d = q.popleft()\n"
        "    if node == goal:\n        return d\n```",
        4,
        5,
        2,
    ),
    _c(
        "implementation.heap_wrong_polarity",
        "Negate on push and negate on pop:\n\n```python\nheapq.heappush(h, -n)\n"
        "value = -heapq.heappop(h)\n```",
        4,
        5,
        3,
    ),
    _c(
        "comprehension.missed_empty_or_single_element_case",
        "Add `if not nums: return 0` at the top of the function.",
        4,
        5,
        3,
    ),
    _c(
        "complexity.copying_state_per_recursive_call",
        "You copy the visited set at every level, which is why you hit the memory limit. "
        "Mutating one shared set and undoing the change on the way out gives the same "
        "semantics at constant cost per level.",
        5,
        5,
        5,
    ),
    _c(
        "comprehension.missed_cyclic_or_wraparound",
        "Your traversal stops at the last index, but the structure wraps around to the "
        "first. Every case whose answer does not cross the boundary comes out right, "
        "which is what hides the bug.",
        5,
        5,
        5,
    ),
]
