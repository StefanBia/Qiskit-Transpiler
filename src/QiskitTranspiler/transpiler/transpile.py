from QiskitTranspiler.transpiler.passes.layout.layout import Layout
from qiskit import QuantumCircuit
from QiskitTranspiler.transpiler.passes.translation.translator import translate_circuit
from QiskitTranspiler.transpiler.passes.optimization.optimization import optimize


def apply_layout(qc: QuantumCircuit, mapping, num_physical_qubits: int) -> QuantumCircuit:
    num_virtual_qubits = qc.num_qubits
    physical_qc = QuantumCircuit(num_physical_qubits, num_virtual_qubits)
    
    # normalize mapping to a dict {virtual: physical}
    if isinstance(mapping, list):
        mapping_dict = {v: mapping[v] for v in range(num_virtual_qubits)}
    elif isinstance(mapping, dict):
        mapping_dict = mapping
    else:
        raise TypeError(f"Unsupported mapping type: {type(mapping)}")

    for inst in qc.data:
        name = inst.operation.name
        if name in ("barrier", "reset", "delay"):
            continue
        elif name == "measure":
            virtual_q = qc.find_bit(inst.qubits[0]).index
            virtual_c = qc.find_bit(inst.clbits[0]).index
            physical_qc.measure(mapping_dict[virtual_q], virtual_c)
        else:
            virtual_qubits = [qc.find_bit(q).index for q in inst.qubits]
            physical_qubits = [mapping_dict[v] for v in virtual_qubits]
            physical_qc.append(inst.operation, physical_qubits)
    
    return physical_qc


def transpile(circuit: QuantumCircuit, backend) -> QuantumCircuit:
    coupling_map = backend.coupling_map
    # print(coupling_map)

    INFRASTRUCTURE_GATES = { "measure", "delay", "reset"}
    CONTROL_FLOW_GATES = {"if_else", "for_loop", "switch_case", "while_loop", "break", "continue"}

    basis_gates = [
        g for g in backend.operation_names 
        if g not in INFRASTRUCTURE_GATES and g not in CONTROL_FLOW_GATES
    ]

    # print("Basis gates:", basis_gates)

    layout_no_translate, mapping = Layout.run_layout(circuit, backend)

    layout_no_translate = translate_circuit(layout_no_translate, basis=basis_gates)

    layout_no_translate = optimize(layout_no_translate)

    physical_qc = apply_layout(layout_no_translate, mapping, backend.num_qubits)
    return physical_qc