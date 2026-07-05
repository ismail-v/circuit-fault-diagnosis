from typing import List, Set


def choose_components() -> List[List[str]]:
    """
    UI loop for letting the user choose their own components.

    :return: chosen conflict sets list, formatted correctly
    """
    print("Choose your conflict sets.\n"
          "Separate components within a conflict set by using a space.\n"
          "Make separate conflict sets by hitting the enter key.\n"
          "Once you are done, type \"Stop\"")
    chosen_conflict_sets = []
    prompt = ""
    while True:
        prompt = input("Conflict set >> ")
        if prompt.strip().lower() == "stop":
            break
        if prompt:
            chosen_conflict_sets.append(prompt.upper().split())
    if len(chosen_conflict_sets) == 0:
        chosen_conflict_sets = [[]]
    return chosen_conflict_sets


def jaccard_similarity(set1: Set, set2: Set) -> float:
    """
    Jaccard similarity function of two sets.
    Takes into account empty sets.

    :param set1: first set to compare
    :param set2: second set to compare
    :return: the Jaccard similarity score
    """
    return len(set1 & set2) / len(set1 | set2) if set1 | set2 else 1.0


def score_function(actual_conflict_sets: List, chosen_conflict_sets: List) -> float:
    """
    Custom scoring function for comparing the user's chosen conflict sets
    to the ground truth conflict sets.
    Finds the most similar guessed set for each ground truth set via
    Jaccard similarity, and penalizes for any extra or missing sets.

    :param actual_conflict_sets: list of the true conflict sets.
    :param chosen_conflict_sets: list of the user's guessed conflict sets.
    :return: the score as a float (between 0 and 100)
    """
    actual_conflict_sets = [set(s) for s in actual_conflict_sets]
    chosen_conflict_sets = [set(s) for s in chosen_conflict_sets]

    total_score = 0

    # Score each ground truth set by best matching guessed set
    for actual_set in actual_conflict_sets:
        best_score = 0
        for chosen_set in chosen_conflict_sets:
            score = jaccard_similarity(actual_set, chosen_set)
            if score > best_score:
                best_score = score
        total_score += best_score

    # No actual conflict sets: full marks if the player also chose none,
    # otherwise zero.
    if not actual_conflict_sets:
        return 100.0 if not chosen_conflict_sets else 0.0

    # Penalize extra sets in guessed list
    extra_sets = max(0, len(chosen_conflict_sets) - len(actual_conflict_sets))
    penalty = extra_sets / len(actual_conflict_sets)

    # Normalize score by number of ground truth sets and apply penalty
    final_score = (total_score / len(actual_conflict_sets)) - penalty
    final_score = max(0, final_score)  # ensure score doesn't go below 0

    return final_score * 100
