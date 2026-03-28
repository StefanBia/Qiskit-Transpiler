
from qiskit import QuantumCircuit
from qiskit.circuit import Gate
from qiskit.circuit.library import (
    RZGate, SXGate, XGate, IGate, ECRGate, CZGate,
    CXGate, HGate, TGate, TdgGate, SGate, SdgGate,
    RYGate, RXGate, SwapGate, RZZGate, CCXGate,
)

from QiskitTranspiler.transpiler.passes.translation.equivalence_library import BASIS_SETS, EQUIVALENCES_FOR_BASIS


_GATE_MAP = {
    "rz":   lambda p: RZGate(p[0]),
    "sx":   lambda p: SXGate(),
    "x":    lambda p: XGate(),
    "id":   lambda p: IGate(),
    "ecr":  lambda p: ECRGate(),
    "cz":   lambda p: CZGate(),
    "cx":   lambda p: CXGate(),
    "h":    lambda p: HGate(),
    "t":    lambda p: TGate(),
    "tdg":  lambda p: TdgGate(),
    "s":    lambda p: SGate(),
    "sdg":  lambda p: SdgGate(),
    "ry":   lambda p: RYGate(p[0]),
    "rx":   lambda p: RXGate(p[0]),
    "swap": lambda p: SwapGate(),
    "rzz":  lambda p: RZZGate(p[0]),
    "ccx":  lambda p: CCXGate(),
}

def _build_gate(name: str, params: list) -> Gate:
    """Return a Qiskit Gate object for the given name and params."""
    if name not in _GATE_MAP:
        raise NotImplementedError(
            f"_build_gate: no factory entry for '{name}'. "
            "Add it to _GATE_MAP in basis_translator.py."
        )
    return _GATE_MAP[name](params)


def _translate_gate(
    out: QuantumCircuit,
    name: str,
    params: list,
    qubits: list,
    equivalences: dict,
    target_basis: frozenset,
    _depth: int = 0,
) -> None:

    if _depth > 20:
        raise RecursionError(
            f"Decomposition depth exceeded for gate '{name}'. "
            "This likely means a circular equivalence rule."
        )

    if name in ("barrier", "measure", "reset", "delay"):
        # if name == "barrier":
        #     out.barrier(*qubits)
        # elif name == "measure":
        #     out.measure(*qubits)
        # elif name == "reset":
        #     out.reset(*qubits)
        # elif name == "delay":
        #     out.delay(params[0], *qubits)
        return

    if name in target_basis:
        out.append(_build_gate(name, params), qubits)
        return

    if name not in equivalences:
        raise NotImplementedError(
            f"No equivalence rule for gate '{name}' and it is not in the "
            f"target basis {target_basis}.\n"
            "Either add a rule to equivalence_library.py or extend the "
            "target basis."
        )

    rule = equivalences[name]
    decomposed = rule(qubits, params)

    for (sub_name, sub_params, sub_qubits) in decomposed:
        _translate_gate(
            out, sub_name, sub_params, sub_qubits,
            equivalences, target_basis, _depth + 1
        )


def translate_circuit(
    qc: QuantumCircuit,
    backend: str = None,
    basis=None,
    custom_equivalences: dict = None,
) -> QuantumCircuit:

    key = backend or (basis if isinstance(basis, str) else None)
    

    if isinstance(basis, (list, set, frozenset)) and not isinstance(basis, str):
        target_basis = frozenset(basis)
        if custom_equivalences is not None:
            equivalences = custom_equivalences
        else:
            INFRASTRUCTURE_GATES = {"id", "measure", "delay", "reset"}

            basis_gates = frozenset(g for g in target_basis if g not in INFRASTRUCTURE_GATES)
            found = False
            for name, equiv in BASIS_SETS.items():
                # print(f"Checking if target_basis {target_basis} is subset of {name} basis {equiv}...")
                if basis_gates.issubset(equiv):
                    equivalences = EQUIVALENCES_FOR_BASIS[name]
                    print(
                        "[BasisTranslator] Warning: Found a built-in equivalence table that covers the provided custom_basis. "
                        f"Using '{name}'"
                    )
                    found = True
                    break
            if not found:
                from QiskitTranspiler.transpiler.passes.translation.equivalence_library import EQUIVALENCES_ECR
                equivalences = EQUIVALENCES_ECR
                print(
                    "[BasisTranslator] Warning: custom_basis provided without "
                    "custom_equivalences — using built-in ECR equivalence table as fallback."
                )

    elif key is not None:
        if key not in BASIS_SETS:
            raise ValueError(
                f"Unknown backend/basis '{key}'. "
                f"Available options: {list(BASIS_SETS.keys())}"
            )
        target_basis = BASIS_SETS[key]
        equivalences = EQUIVALENCES_FOR_BASIS[key]

    else:
        raise ValueError(
            "You must specify one of: backend, or basis (string name or list of gate names).\n"
            "Examples:\n"
            "  translate_circuit(qc, backend='eagle')\n"
            "  translate_circuit(qc, basis=['x', 'sx', 'rz', 'cx'])"
        )


    out = QuantumCircuit(qc.num_qubits)
    
    # Add classical registers to the output circuit
    if qc.num_clbits > 0:
        out.add_register(*qc.cregs)

    for inst in qc.data:
        name   = inst.operation.name
        params = list(inst.operation.params)
        qubits = [qc.find_bit(q).index for q in inst.qubits]
    
        if name == "barrier":
            out.barrier(qubits)
        elif name == "measure":
            out.measure(qubits, [qc.find_bit(cbit).index for cbit in inst.clbits])
        elif name == "reset":
            out.reset(qubits)
        elif name == "delay":
            out.delay(params[0], qubits)
        else:
            _translate_gate(out, name, params, qubits, equivalences, target_basis)

    return out


def list_supported_bases() -> None:
    """Print all predefined basis sets and their gate names."""
    for name, gates in BASIS_SETS.items():
        print(f"{name:20s}: {sorted(gates)}")
