from qiskit import QuantumCircuit
import numpy as np

EPSILON = 1e-9  # tolerance for float comparisons

def optimize(qc: QuantumCircuit) -> QuantumCircuit:
    """Run all optimization passes until no further reduction is possible."""
    current = qc
    while True:
        optimized = _run_passes(current)
        if optimized.count_ops() == current.count_ops():
            break  # no improvement, stop
        current = optimized
    return current

def _run_passes(qc: QuantumCircuit) -> QuantumCircuit:
    qc = cancel_two_qubit_gates(qc)
    qc = merge_rz_rotations(qc)
    qc = cancel_x_gates(qc)
    qc = remove_identity_gates(qc)
    return qc

def merge_rz_rotations(qc: QuantumCircuit) -> QuantumCircuit:
    """Merge consecutive RZ gates on the same qubit into one."""
    out = QuantumCircuit(qc.num_qubits, qc.num_clbits)
    
    # track pending RZ angle per qubit
    pending_rz = {}  # qubit_index -> accumulated angle

    for inst in qc.data:
        name = inst.operation.name
        qubits = [qc.find_bit(q).index for q in inst.qubits]
        clbits = [qc.find_bit(c).index for c in inst.clbits]

        if name == 'rz' and len(qubits) == 1:
            q = qubits[0]
            angle = float(inst.operation.params[0])
            pending_rz[q] = pending_rz.get(q, 0.0) + angle
        else:
            # flush any pending RZ on qubits this gate touches
            for q in qubits:
                if q in pending_rz:
                    angle = pending_rz.pop(q) % (2 * np.pi)
                    if angle > np.pi:
                        angle -= 2 * np.pi #normalize to [-pi, pi]
                    if abs(angle) > EPSILON:  # skip if effectively zero
                        out.rz(angle, q)
            # emit the current gate
            if name == 'measure':
                out.measure(qubits[0], clbits[0])
            else:
                out.append(inst.operation, qubits)

    # flush any remaining pending RZ at end of circuit
    for q, angle in pending_rz.items():
        angle = angle % (2 * np.pi)
        if angle > np.pi:
            angle -= 2 * np.pi
        if abs(angle) > EPSILON:
            out.rz(angle, q)

    return out


def cancel_two_qubit_gates(qc: QuantumCircuit) -> QuantumCircister:

    CANCELLABLE = {'cx', 'ecr', 'cz'}
    
    instructions = list(qc.data)
    to_remove = set()
    
    last_two_qubit_on = {} 

    for i, inst in enumerate(instructions):
        name = inst.operation.name
        qubits = [qc.find_bit(q).index for q in inst.qubits]

        if name in CANCELLABLE and len(qubits) == 2:
            q0, q1 = qubits

            last_q0 = last_two_qubit_on.get(q0)
            last_q1 = last_two_qubit_on.get(q1)

            if (last_q0 is not None
                    and last_q0 == last_q1  
                    and last_q0 not in to_remove):

                prev_inst = instructions[last_q0]
                prev_qubits = [qc.find_bit(q).index for q in prev_inst.qubits]

                if (prev_inst.operation.name == name
                        and prev_qubits == qubits):
                    to_remove.add(last_q0)
                    to_remove.add(i)
                   
                    last_two_qubit_on.pop(q0, None)
                    last_two_qubit_on.pop(q1, None)
                    continue

            last_two_qubit_on[q0] = i
            last_two_qubit_on[q1] = i

        elif name not in ('measure', 'barrier'):
            for q in qubits:
                last_two_qubit_on.pop(q, None)

    out = QuantumCircuit(qc.num_qubits, qc.num_clbits)
    for i, inst in enumerate(instructions):
        if i not in to_remove:
            qubits = [qc.find_bit(q).index for q in inst.qubits]
            clbits = [qc.find_bit(c).index for c in inst.clbits]
            if inst.operation.name == 'measure':
                out.measure(qubits[0], clbits[0])
            else:
                out.append(inst.operation, qubits)

    return out


def cancel_x_gates(qc: QuantumCircuit) -> QuantumCircuit:

    instructions = list(qc.data)
    to_remove = set()

    last_x_on = {}

    for i, inst in enumerate(instructions):
        name = inst.operation.name
        qubits = [qc.find_bit(q).index for q in inst.qubits]

        if name == 'x' and len(qubits) == 1:
            q = qubits[0]
            last = last_x_on.get(q)

            if last is not None and last not in to_remove:
                to_remove.add(last)
                to_remove.add(i)
                last_x_on.pop(q)
            else:
                last_x_on[q] = i

        else:
            for q in qubits:
                last_x_on.pop(q, None)

    out = QuantumCircuit(qc.num_qubits, qc.num_clbits)
    for i, inst in enumerate(instructions):
        if i not in to_remove:
            qubits = [qc.find_bit(q).index for q in inst.qubits]
            clbits = [qc.find_bit(c).index for c in inst.clbits]
            if inst.operation.name == 'measure':
                out.measure(qubits[0], clbits[0])
            else:
                out.append(inst.operation, qubits)

    return out


def remove_identity_gates(qc: QuantumCircuit) -> QuantumCircuit:
    """Remove identity gates and zero-angle RZ rotations."""
    out = QuantumCircuit(qc.num_qubits, qc.num_clbits)
    for inst in qc.data:
        name = inst.operation.name
        qubits = [qc.find_bit(q).index for q in inst.qubits]
        clbits = [qc.find_bit(c).index for c in inst.clbits]
        if name == 'id':
            continue
        if name == 'rz' and abs(float(inst.operation.params[0]) % (2 * np.pi)) < EPSILON:
            continue
        if name == 'measure':
            out.measure(qubits[0], clbits[0])
        else:
            out.append(inst.operation, qubits)
    return out