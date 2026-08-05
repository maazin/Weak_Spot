"""Suite C — 100 labelled (pattern, problem) pairs, marked relevant or not.

"Relevant" means: a user who just failed with this pattern would genuinely be drilling
the same idea by attempting this problem. Negatives are deliberately *plausible* — same
family, adjacent topic, or overlapping tags — because a suite of obvious negatives makes
any retriever look good and tells you nothing about fusion.
"""

from __future__ import annotations

PAIRS: list[dict] = [
    # --- two pointers / sortedness ---
    {
        "pattern_id": "pattern_selection.hashmap_over_two_pointers",
        "problem_slug": "two-sum-ii-input-array-is-sorted",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.hashmap_over_two_pointers",
        "problem_slug": "3sum",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.hashmap_over_two_pointers",
        "problem_slug": "container-with-most-water",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.hashmap_over_two_pointers",
        "problem_slug": "squares-of-a-sorted-array",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.hashmap_over_two_pointers",
        "problem_slug": "course-schedule",
        "relevant": False,
    },
    {
        "pattern_id": "pattern_selection.hashmap_over_two_pointers",
        "problem_slug": "implement-trie-prefix-tree",
        "relevant": False,
    },
    {
        "pattern_id": "comprehension.missed_sorted_input_guarantee",
        "problem_slug": "two-sum-ii-input-array-is-sorted",
        "relevant": True,
    },
    {
        "pattern_id": "comprehension.missed_sorted_input_guarantee",
        "problem_slug": "merge-sorted-array",
        "relevant": True,
    },
    {
        "pattern_id": "comprehension.missed_sorted_input_guarantee",
        "problem_slug": "intersection-of-two-arrays",
        "relevant": True,
    },
    {
        "pattern_id": "comprehension.missed_sorted_input_guarantee",
        "problem_slug": "n-queens",
        "relevant": False,
    },
    # --- sorting unlocks linear ---
    {
        "pattern_id": "pattern_selection.sorting_unlocks_linear",
        "problem_slug": "merge-intervals",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.sorting_unlocks_linear",
        "problem_slug": "insert-interval",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.sorting_unlocks_linear",
        "problem_slug": "non-overlapping-intervals",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.sorting_unlocks_linear",
        "problem_slug": "minimum-number-of-arrows-to-burst-balloons",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.sorting_unlocks_linear",
        "problem_slug": "linked-list-cycle",
        "relevant": False,
    },
    {
        "pattern_id": "pattern_selection.sorting_unlocks_linear",
        "problem_slug": "counting-bits",
        "relevant": False,
    },
    # --- greedy vs dp ---
    {
        "pattern_id": "pattern_selection.greedy_over_dp",
        "problem_slug": "coin-change",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.greedy_over_dp",
        "problem_slug": "house-robber",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.greedy_over_dp",
        "problem_slug": "partition-equal-subset-sum",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.greedy_over_dp",
        "problem_slug": "best-time-to-buy-and-sell-stock-with-cooldown",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.greedy_over_dp",
        "problem_slug": "valid-parentheses",
        "relevant": False,
    },
    {
        "pattern_id": "pattern_selection.greedy_over_dp",
        "problem_slug": "reverse-linked-list",
        "relevant": False,
    },
    # --- bfs vs dfs shortest path ---
    {
        "pattern_id": "pattern_selection.dfs_over_bfs_shortest_path",
        "problem_slug": "shortest-path-in-binary-matrix",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.dfs_over_bfs_shortest_path",
        "problem_slug": "word-ladder",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.dfs_over_bfs_shortest_path",
        "problem_slug": "rotting-oranges",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.dfs_over_bfs_shortest_path",
        "problem_slug": "open-the-lock",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.dfs_over_bfs_shortest_path",
        "problem_slug": "number-of-islands",
        "relevant": False,
    },
    {
        "pattern_id": "pattern_selection.dfs_over_bfs_shortest_path",
        "problem_slug": "climbing-stairs",
        "relevant": False,
    },
    # --- sliding window ---
    {
        "pattern_id": "pattern_selection.nested_loops_over_sliding_window",
        "problem_slug": "longest-substring-without-repeating-characters",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.nested_loops_over_sliding_window",
        "problem_slug": "minimum-size-subarray-sum",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.nested_loops_over_sliding_window",
        "problem_slug": "find-all-anagrams-in-a-string",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.nested_loops_over_sliding_window",
        "problem_slug": "max-consecutive-ones-iii",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.nested_loops_over_sliding_window",
        "problem_slug": "longest-increasing-subsequence",
        "relevant": False,
    },
    {
        "pattern_id": "pattern_selection.nested_loops_over_sliding_window",
        "problem_slug": "merge-k-sorted-lists",
        "relevant": False,
    },
    # --- binary search ---
    {
        "pattern_id": "pattern_selection.linear_scan_over_binary_search",
        "problem_slug": "search-insert-position",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.linear_scan_over_binary_search",
        "problem_slug": "find-first-and-last-position-of-element-in-sorted-array",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.linear_scan_over_binary_search",
        "problem_slug": "search-in-rotated-sorted-array",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.linear_scan_over_binary_search",
        "problem_slug": "group-anagrams",
        "relevant": False,
    },
    {
        "pattern_id": "pattern_selection.exhaustive_search_over_binary_search_on_answer",
        "problem_slug": "koko-eating-bananas",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.exhaustive_search_over_binary_search_on_answer",
        "problem_slug": "capacity-to-ship-packages-within-d-days",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.exhaustive_search_over_binary_search_on_answer",
        "problem_slug": "split-array-largest-sum",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.exhaustive_search_over_binary_search_on_answer",
        "problem_slug": "minimum-number-of-days-to-make-m-bouquets",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.exhaustive_search_over_binary_search_on_answer",
        "problem_slug": "binary-search",
        "relevant": False,
    },
    {
        "pattern_id": "implementation.binary_search_bounds_off_by_one",
        "problem_slug": "binary-search",
        "relevant": True,
    },
    {
        "pattern_id": "implementation.binary_search_bounds_off_by_one",
        "problem_slug": "search-insert-position",
        "relevant": True,
    },
    {
        "pattern_id": "implementation.binary_search_bounds_off_by_one",
        "problem_slug": "find-first-and-last-position-of-element-in-sorted-array",
        "relevant": True,
    },
    {
        "pattern_id": "implementation.binary_search_bounds_off_by_one",
        "problem_slug": "trapping-rain-water",
        "relevant": False,
    },
    {
        "pattern_id": "implementation.binary_search_infinite_loop",
        "problem_slug": "find-minimum-in-rotated-sorted-array",
        "relevant": True,
    },
    {
        "pattern_id": "implementation.binary_search_infinite_loop",
        "problem_slug": "find-peak-element",
        "relevant": True,
    },
    {
        "pattern_id": "implementation.binary_search_infinite_loop",
        "problem_slug": "valid-anagram",
        "relevant": False,
    },
    # --- heap / top k ---
    {
        "pattern_id": "pattern_selection.sorting_over_heap_for_top_k",
        "problem_slug": "kth-largest-element-in-an-array",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.sorting_over_heap_for_top_k",
        "problem_slug": "top-k-frequent-elements",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.sorting_over_heap_for_top_k",
        "problem_slug": "k-closest-points-to-origin",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.sorting_over_heap_for_top_k",
        "problem_slug": "find-median-from-data-stream",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.sorting_over_heap_for_top_k",
        "problem_slug": "valid-parentheses",
        "relevant": False,
    },
    {
        "pattern_id": "implementation.heap_wrong_polarity",
        "problem_slug": "kth-largest-element-in-an-array",
        "relevant": True,
    },
    {
        "pattern_id": "implementation.heap_wrong_polarity",
        "problem_slug": "last-stone-weight",
        "relevant": True,
    },
    {
        "pattern_id": "implementation.heap_wrong_polarity",
        "problem_slug": "task-scheduler",
        "relevant": True,
    },
    {
        "pattern_id": "implementation.heap_wrong_polarity",
        "problem_slug": "unique-paths",
        "relevant": False,
    },
    # --- union find ---
    {
        "pattern_id": "pattern_selection.visited_set_over_union_find",
        "problem_slug": "number-of-connected-components-in-an-undirected-graph",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.visited_set_over_union_find",
        "problem_slug": "redundant-connection",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.visited_set_over_union_find",
        "problem_slug": "accounts-merge",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.visited_set_over_union_find",
        "problem_slug": "graph-valid-tree",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.visited_set_over_union_find",
        "problem_slug": "binary-tree-inorder-traversal",
        "relevant": False,
    },
    # --- monotonic stack ---
    {
        "pattern_id": "pattern_selection.brute_force_over_monotonic_stack",
        "problem_slug": "daily-temperatures",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.brute_force_over_monotonic_stack",
        "problem_slug": "largest-rectangle-in-histogram",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.brute_force_over_monotonic_stack",
        "problem_slug": "next-greater-element-i",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.brute_force_over_monotonic_stack",
        "problem_slug": "online-stock-span",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.brute_force_over_monotonic_stack",
        "problem_slug": "valid-anagram",
        "relevant": False,
    },
    # --- prefix sum ---
    {
        "pattern_id": "pattern_selection.recompute_over_prefix_sum",
        "problem_slug": "range-sum-query-immutable",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.recompute_over_prefix_sum",
        "problem_slug": "subarray-sum-equals-k",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.recompute_over_prefix_sum",
        "problem_slug": "find-pivot-index",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.recompute_over_prefix_sum",
        "problem_slug": "product-of-array-except-self",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.recompute_over_prefix_sum",
        "problem_slug": "n-queens",
        "relevant": False,
    },
    # --- topological sort / graph modeling ---
    {
        "pattern_id": "pattern_selection.missed_topological_sort",
        "problem_slug": "course-schedule",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.missed_topological_sort",
        "problem_slug": "course-schedule-ii",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.missed_topological_sort",
        "problem_slug": "alien-dictionary",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.missed_topological_sort",
        "problem_slug": "number-of-islands",
        "relevant": False,
    },
    {
        "pattern_id": "pattern_selection.missed_graph_modeling",
        "problem_slug": "word-ladder",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.missed_graph_modeling",
        "problem_slug": "evaluate-division",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.missed_graph_modeling",
        "problem_slug": "open-the-lock",
        "relevant": True,
    },
    {
        "pattern_id": "pattern_selection.missed_graph_modeling",
        "problem_slug": "reverse-string",
        "relevant": False,
    },
    # --- memoization / complexity ---
    {
        "pattern_id": "complexity.missing_memoization",
        "problem_slug": "fibonacci-number",
        "relevant": True,
    },
    {
        "pattern_id": "complexity.missing_memoization",
        "problem_slug": "climbing-stairs",
        "relevant": True,
    },
    {
        "pattern_id": "complexity.missing_memoization",
        "problem_slug": "word-break",
        "relevant": True,
    },
    {
        "pattern_id": "complexity.missing_memoization",
        "problem_slug": "unique-paths",
        "relevant": True,
    },
    {
        "pattern_id": "complexity.missing_memoization",
        "problem_slug": "valid-palindrome",
        "relevant": False,
    },
    {
        "pattern_id": "complexity.list_membership_scan",
        "problem_slug": "contains-duplicate",
        "relevant": True,
    },
    {
        "pattern_id": "complexity.list_membership_scan",
        "problem_slug": "longest-consecutive-sequence",
        "relevant": True,
    },
    {
        "pattern_id": "complexity.list_membership_scan",
        "problem_slug": "intersection-of-two-arrays",
        "relevant": True,
    },
    {
        "pattern_id": "complexity.list_membership_scan",
        "problem_slug": "rotate-image",
        "relevant": False,
    },
    {
        "pattern_id": "complexity.front_insertion_or_removal_on_array",
        "problem_slug": "number-of-recent-calls",
        "relevant": True,
    },
    {
        "pattern_id": "complexity.front_insertion_or_removal_on_array",
        "problem_slug": "binary-tree-level-order-traversal",
        "relevant": True,
    },
    {
        "pattern_id": "complexity.front_insertion_or_removal_on_array",
        "problem_slug": "sliding-window-maximum",
        "relevant": True,
    },
    {
        "pattern_id": "complexity.front_insertion_or_removal_on_array",
        "problem_slug": "single-number",
        "relevant": False,
    },
    {
        "pattern_id": "complexity.string_concat_in_loop",
        "problem_slug": "excel-sheet-column-title",
        "relevant": True,
    },
    {
        "pattern_id": "complexity.string_concat_in_loop",
        "problem_slug": "multiply-strings",
        "relevant": True,
    },
    {
        "pattern_id": "complexity.string_concat_in_loop",
        "problem_slug": "counting-bits",
        "relevant": False,
    },
    # --- backtracking / duplicates ---
    {
        "pattern_id": "implementation.duplicates_not_deduped",
        "problem_slug": "subsets-ii",
        "relevant": True,
    },
    {
        "pattern_id": "implementation.duplicates_not_deduped",
        "problem_slug": "combination-sum-ii",
        "relevant": True,
    },
    {
        "pattern_id": "implementation.duplicates_not_deduped",
        "problem_slug": "permutations-ii",
        "relevant": True,
    },
    {
        "pattern_id": "implementation.duplicates_not_deduped",
        "problem_slug": "binary-search",
        "relevant": False,
    },
    {
        "pattern_id": "implementation.backtracking_state_not_restored",
        "problem_slug": "word-search",
        "relevant": True,
    },
    {
        "pattern_id": "implementation.backtracking_state_not_restored",
        "problem_slug": "permutations",
        "relevant": True,
    },
    {
        "pattern_id": "implementation.backtracking_state_not_restored",
        "problem_slug": "n-queens",
        "relevant": True,
    },
    {
        "pattern_id": "implementation.backtracking_state_not_restored",
        "problem_slug": "plus-one",
        "relevant": False,
    },
]
