from itertools import combinations
from typing import List, Set, Tuple


def is_hitting_set(candidate: Set, conflict_sets: List[Set]) -> bool:
    """
    Returns True if candidate shares an element with every conflict set.

    :param candidate: set of elements to test
    :param conflict_sets: iterable of conflict sets that must all be hit
    :return: True if candidate intersects every conflict set
    """
    for conflict_set in conflict_sets:
        if candidate.isdisjoint(conflict_set):
            return False
    return True


def compute_hitting_sets(conflict_sets: List) -> Tuple[List[list], List[list]]:
    """
    Finds all hitting sets (and the minimal ones) for the conflict sets,
    trying smallest combinations first.

    :param conflict_sets: list of conflict sets, each an iterable of names
    :return: tuple (all_hitting_sets, minimal_hitting_sets)
    """

    if not conflict_sets or not any(conflict_sets):
        return [], []

    conflict_sets = [set(cs) for cs in conflict_sets if cs]
    if not conflict_sets:
        return [], []

    all_elements = sorted(set().union(*conflict_sets), key=str)

    all_hitting_sets = []
    minimal_hitting_sets = []

    for size in range(1, len(all_elements) + 1):
        for combo in combinations(all_elements, size):
            candidate = set(combo)

            already_covered = any(
                minimal.issubset(candidate) for minimal in minimal_hitting_sets
            )

            if already_covered:
                all_hitting_sets.append(list(candidate))
                continue

            if is_hitting_set(candidate, conflict_sets):
                all_hitting_sets.append(list(candidate))
                minimal_hitting_sets.append(candidate)

    minimal_hitting_sets = [list(s) for s in minimal_hitting_sets]

    return all_hitting_sets, minimal_hitting_sets