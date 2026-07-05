from z3 import *
from itertools import chain, combinations
from typing import Tuple, List
import re


class ConflictSetRetriever:
    """
    Class that handles reads in a file and finds the conflict sets.
    """
    def __init__(self, document_path):
        """
        Opens file and handles logic to read the system description

        :param document_path: path to the circuit file.
        """
        self.document_path = document_path
        self.document = self.validate_file()

        self.all_comps = {}
        self.extract_gates()
        self.find_inputs_and_outputs()
        self.fault_assumptions = self.make_fault_assumptions()
        self.observations = self.extract_observations()


    def validate_file(self) -> str:
        """
        Reads the circuit file and checks that it has a correct format,
        raising an error if not.
 
        :return: the document contents as a string
        """
        
        with open(self.document_path, "r") as file:
            document = file.read()

        sections_to_check = {
            "COMPONENTS": "ENDCOMPONENTS",
            "BEHAVIOUR": "ENDBEHAVIOUR",
            "OBSERVATIONS": "ENDOBSERVATIONS",
            "OUTOBSERVATIONS": "ENDOUTOBSERVATIONS"
        }
        for start, end in sections_to_check.items():
            if not re.search(rf"{start}:\s*(.*?)\s*{end}", document, re.DOTALL):
                raise Exception(f"Missing {start} section")
        
        comp_section = re.search(r"COMPONENTS:\s*(.*?)\s*ENDCOMPONENTS", document, re.DOTALL)
        components = re.findall(r"\((.*?)\)", comp_section.group(1))

        # Count IN1 and IN2 for each component
        in_counts = {comp: {"IN1": 0, "IN2": 0} for comp in components}

        for comp in components:
            in_counts[comp]["IN1"] = len(
                re.findall(rf"\bIN1\({re.escape(comp)}\)\s*=", document))
            in_counts[comp]["IN2"] = len(
                re.findall(rf"\bIN2\({re.escape(comp)}\)\s*=", document))

        errors = []
        for comp, counts in in_counts.items():
            if counts["IN1"] != 1 or counts["IN2"] != 1:
                errors.append(
                    f"- component {comp} has {counts['IN1']} IN1 connections and "
                    f"{counts['IN2']} IN2 connections.")

        if errors:
            raise ValueError("Invalid component connections:\n" + "\n".join(errors))

        return document

    def extract_gates(self) -> None:
        """
        Parses the COMPONENTS section and populates self.all_comps with
        one entry per gate, keyed by the gate name (e.g. "A1"). Each
        entry stores:
            - fault_flag: the gate's fault-flag Bool (e.g. A1_gate)
            - comp_out:   the gate's output Bool (e.g. A1)
            - gate_type:  the Z3 function implementing the gate (And/Or/Xor)
        """

        gate_map = {
            "ANDG": And,
            "ORG": Or,
            "XORG": Xor
        }

        match = re.search(r"COMPONENTS:\s*(.*?)\s*ENDCOMPONENTS", self.document, re.DOTALL)
        if not match:
            raise Exception("No components found.")
        else:
            components_string = match.group(1)
            components = [line for line in components_string.split("\n") if line]
            gate_pattern = re.compile(r"(ANDG|ORG|XORG)\((.+)\)")
            for component in components:
                match = gate_pattern.search(component)
                if not match:
                    raise Exception("Error reading components.")
                else:
                    self.all_comps[match.group(2)] = {"fault_flag": Bool(match.group(2) + "_gate"),
                                                      "comp_out": Bool(match.group(2)),
                                                      "gate_type": gate_map[match.group(1)]}
    

    @staticmethod
    def _resolve_input(match) -> Tuple[z3.z3.BoolRef | bool, bool]:
        """
        Resolves a single gate input (IN1 or IN2) from its regex match
        into either a constant truth value or a wire to another gate.
 
        :param match: a regex match against an "IN1(comp)=..." or
            "IN2(comp)=..." line, where group(2) is the full right-hand
            side ("0", "1", or "OUT(other_comp)") and group(3) is the
            wired component's name, if any.
        :return: a tuple of (value, is_constant), where value is a
            Python bool for a constant input, or a Z3 Bool for a wired
            input.
        """
        value_str = match.group(2)
        if value_str in ("0", "1"):
            return bool(int(value_str)), True   # (value, is_constant)
        return Bool(match.group(3)), False


    def find_inputs_and_outputs(self) -> None:
        """
        Populates each component's input and output info in
        self.all_comps:
            - in1_bool / in2_bool: the Z3 Bools used to observe a
              constant input's value (e.g. IN1(A1))
            - in1 / in2: the resolved input, either a constant truth
              value or another gate's output Bool
            - in1_is_constant / in2_is_constant: whether that input is
              a directly observed constant, as opposed to wired from
              another gate
            - out_val: the gate's observed output value (True/False),
              or None if its output was not observed directly
        """
        
        for k, i in self.all_comps.items():
            match = re.search(rf"OUT\({i["comp_out"]}\)=(0|1)\n", self.document)
            if match:
                self.all_comps[k]["out_val"] = bool(int(match.group(1)))
            else:
                self.all_comps[k]["out_val"] = None

        for k, v in self.all_comps.items():
            match_a = re.search(rf"(IN1\({str(v["comp_out"])}\))=(0|1|OUT\((.+)\))\n", self.document)
            match_b = re.search(rf"(IN2\({str(v["comp_out"])}\))=(0|1|OUT\((.+)\))\n", self.document)

            if not (match_a and match_b):
                raise Exception("Error reading components.")
            else:
                self.all_comps[k]["in1"], self.all_comps[k]["in1_is_constant"] = self._resolve_input(match_a)
                self.all_comps[k]["in2"], self.all_comps[k]["in2_is_constant"] = self._resolve_input(match_b)


    def make_fault_assumptions(self) -> List[z3.z3.BoolRef]:
        """
        Builds one fault assumption per gate: "this gate is faulty, or
        its output is consistent with its inputs and gate type".
 
        :return: list of fault assumptions
        """
        fault_assumptions = []

        # a fault assumption is needed for every single gate:
        for comp in self.all_comps.values():
            fault_assumptions.append(Or(comp["fault_flag"], comp["gate_type"](comp["in1"], comp["in2"]) == comp["comp_out"]))

        return fault_assumptions


    def extract_observations(self) -> List[z3.z3.BoolRef]:
        """
        Builds the list of observed truth values: constant gate inputs
        and any directly observed gate outputs.
 
        :return: list of observations with truth values.
        """

        all_observations = []

        for comp in self.all_comps.values():
            if comp["out_val"] is not None:
                all_observations.append(comp["out_val"] == comp["comp_out"])
 
        return all_observations


    @staticmethod
    def powerset(s) -> chain[Tuple[z3.z3.BoolRef]]:
        """
        Generates a powerset of s, excluding the empty set.
        Used for brute-force checking of all combinations of gates.
 
        :param s: iterable of which to generate powerset
        :return: powerset of s
        """
        return chain.from_iterable(combinations(s, r) for r in range(1, len(s) + 1))


    def retrieve_conflict_sets(self) -> List[List[str]]:
        """
        Handles all Z3 logic to retrieve the minimal conflict sets: the
        smallest groups of gates that cannot all be healthy at once,
        given the circuit's behaviour and the observed values.
 
        :return: list of minimal conflict sets, each a list of plain
            gate names (e.g. "X1").
        """
        name_by_flag = {
            comp["fault_flag"]: str(comp["comp_out"]) for comp in self.all_comps.values()
        }
        all_flags = list(name_by_flag.keys())
        conflict_sets = []
        
        s = Solver()
        s.add(*self.fault_assumptions, *self.observations)
        
        for healthy_combo in self.powerset(all_flags):
            s.push()
            for flag in all_flags:
                s.add(flag == (flag not in healthy_combo))

            if s.check() == unsat:
                conflict_sets.append(set(healthy_combo))

            s.pop()


        # Keep only the minimal conflict sets: drop any set that is a
        # strict superset of another conflict set (cs > other).
        minimal_conflicts = []
        for cs in conflict_sets:
            if all(not cs > other for other in conflict_sets):
                minimal_conflicts.append(list(cs))

        return [[name_by_flag[flag] for flag in sublist] for sublist in minimal_conflicts]
