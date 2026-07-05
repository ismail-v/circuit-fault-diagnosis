import argparse
from circuitplotter import plot_circuit
from guesscomponentsgame import choose_components, score_function
from conflictsets import ConflictSetRetriever
from hittingsets import compute_hitting_sets

# --- Argument parsing ---
parser = argparse.ArgumentParser(
    description="Circuit Fault Diagnosis — derives conflict sets and minimal hitting sets from a circuit description."
)
parser.add_argument(
    "--circuit",
    type=str,
    default="circuits/circuit1.txt",
    help="Path to the circuit file (default: circuits/circuit1.txt)"
)
parser.add_argument(
    "--game",
    action="store_true",
    help="Launch the guessing game mode before running diagnosis"
)
args = parser.parse_args()

document = args.circuit
game = args.game

# --- Main logic ---
if game:
    plot_circuit(document)
    chosen_conflict_sets = choose_components()
    print("Your chosen conflict sets:", chosen_conflict_sets)
    chosen_hitting_sets, chosen_minimal_hitting_sets = compute_hitting_sets(chosen_conflict_sets)
    print("Your hitting sets:", chosen_hitting_sets)
    print("Your minimal hitting sets:", chosen_minimal_hitting_sets, "\n")

# Collect conflict sets
csr = ConflictSetRetriever(document)
conflict_sets = csr.retrieve_conflict_sets()
print("Actual conflict sets:", *conflict_sets)

# Collect minimal hitting sets
if len(conflict_sets) == 0:
    print("This circuit works correctly, there are no faulty components!")
else:
    hitting_sets, minimal_hitting_sets = compute_hitting_sets(conflict_sets)
    print("Hitting sets:", *hitting_sets)
    print("Minimal hitting sets:", *minimal_hitting_sets, "\n")

# Score the user's guesses
if game:
    score = score_function(conflict_sets, chosen_conflict_sets)
    print(f"Your score: {score:.2f}%")