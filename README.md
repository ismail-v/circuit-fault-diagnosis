# Circuit Fault Diagnosis

Model-based fault diagnosis for logic circuits using the Z3 SMT solver. Given a circuit description and a set of observed inputs and outputs, the program identifies which components are likely faulty by computing conflict sets, hitting sets and minimal hitting sets.

## How it works

1. **Circuit Parsing** - Reads a circuit description file and validates its format, checking that all required sections are present (COMPONENTS, BEHAVIOUR, OBSERVATIONS, OUTOBSERVATIONS) and that each component has exactly one IN1 and one IN2 connection. Gates, their types, inputs, and observed values are then extracted and stored as a dictionary.
2. **Constraint encoding** — Each gate's type(AND, OR, and XOR), inputs, and output wire are encoded as Z3 logical constraints with a fault flag. Observed output values from the circuit file are then added as separate constraints to ground the variables to real measurements.
3. **Conflict sets** — The solver finds the smallest groups of components that cannot all be healthy simultaneously given the observations.
4. **Hitting sets** -  Derived from the conflict sets to enumerate all possible faulty component combinations; minimal hitting sets are then computed to show the smallest possible explanations for the observed fault.


## Features

- Visualises circuits as schematics using `schemdraw`
- Optional guessing game mode where the user try to idintify conflict sets from the schematic, scored using Jaccard similarity
- Command-line arguments for selecting circuit file and enabling game mode

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ismail-v/circuit-fault-diagnosis
cd circuit-fault-diagnosis
```
2. Install dependencies 
```bash
pip install -r requirements.txt
```

## Usage

Run diagnosis on the default circuit:
```bash
python app.py
```

Run on a specific circuit:
```bash
python app.py --circuit circuits/circuit3.txt
```

Enable the guessing game before diagnosis:
```bash
python app.py --circuit circuits/circuit1.txt --game
```

## Circuit File Format

Each circuit file has four sections: `COMPONENTS`, `BEHAVIOUR`, `OBSERVATIONS`, and `OUTOBSERVATIONS`. See any file in `circuits/` for a complete example.
