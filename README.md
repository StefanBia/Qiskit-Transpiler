# QiskitTranspiler

A lightweight, pedagogical quantum circuit transpiler for NISQ devices.

This project implements a fully functional, Python-based transpiler for IBM quantum backends, built for clarity and simplicity rather than raw performance. It walks a quantum circuit through three independent stages: layout & routing, basis gate translation, and gate-level optimization, making it a practical entry point for students and researchers who want to understand how transpilation actually works, not just use it as a black box.

It is not intended to outperform production transpilers like Qiskit's; it's meant to be read, modified, and extended.

## Architecture

The transpiler is a three-stage pipeline. Each pass is independently callable and stateless, it takes a `QuantumCircuit` plus backend metadata and returns a new `QuantumCircuit`.

1. **Layout & Routing** — assigns logical qubits to physical qubits via VF2 subgraph isomorphism, falling back to a noise-aware initial mapping (BFS-based error scoring) and SABRE-based SWAP insertion when a direct match isn't found.
2. **Translation** — decomposes all gates into the target backend's native basis set using a structured equivalence library.
3. **Optimization** — reduces gate count through algebraic simplifications: X cancellation, RZ merging, and two-qubit gate cancellation.

<!-- TODO: embed Fig. 1 (pipeline diagram) here, e.g.: ![Pipeline architecture](docs/pipeline.png) -->


## Installation

The following prerequisites are required:

- Python 3.8 or higher
- Qiskit SDK already installed
- `pip` package manager
- A working internet connection

**Step 1: Clone the repository.**
Open a terminal and clone the project from GitHub:

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

**Step 2: (Optional) Create a virtual environment.**
It is recommended to install the package inside a dedicated environment to avoid conflicts with other Python packages:

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

**Step 3: Install the package.**
Install the transpiler and all its dependencies using `pip`:

```bash
pip install .
```

Or, if you plan to modify the source code, install it in editable mode:

```bash
pip install -e .
```

**Step 4: Verify the installation.**
Open a Python interpreter and verify that the package imports correctly:

```python
from QiskitTranspiler.transpiler.transpile import transpile
print("Installation successful.")
```

## How to Use

Once installed, the transpiler can be used from any Python script or Jupyter notebook. The main entry point is the `transpile` function, which accepts an abstract `QuantumCircuit` and a target backend, and returns a physically executable circuit.

**Step 1: Define a quantum circuit.**
Create any abstract quantum circuit using Qiskit:

```python
from qiskit import QuantumCircuit

qc = QuantumCircuit(3)
qc.h(0)
qc.cx(0, 1)
qc.cx(1, 2)
qc.measure_all()
```

**Step 2: Connect to an IBM backend.**
Retrieve a target backend using your IBM Quantum account:

```python
from qiskit_ibm_runtime import QiskitRuntimeService

service = QiskitRuntimeService()
backend = service.backend("ibm_fez")
```

Alternatively, use a local noise model simulator for testing without an IBM account:

```python
from qiskit_ibm_runtime.fake_provider import FakeFez

backend = FakeFez()
```

**Step 3: Transpile the circuit.**
Pass the circuit and backend to the transpiler:

```python
from QiskitTranspiler.transpiler.transpile import transpile

transpiled_circuit = transpile(qc, backend=backend)
```

**Step 4: Run the circuit.**
Submit the transpiled circuit for execution:

```python
from qiskit_ibm_runtime import SamplerV2 as Sampler

sampler = Sampler(backend)
job = sampler.run([transpiled_circuit], shots=1024)
result = job.result()
print(result)
```

## Tests

This repository includes the benchmark suite used to evaluate the transpiler's performance, producing the results reported in Table I and Fig. 6 of the accompanying paper.

**What's included:**
- 11 circuit configurations spanning 3, 5, and 10 qubits at varying depths (3–30), each containing at least one ring of CX gates to force routing
- Scripts to transpile each configuration with both this transpiler and Qiskit's transpiler (optimization level 2), for direct comparison
- Simulator evaluation (50 runs per configuration on the IBM Fez noise model via `FakeFez`) measuring gate count, circuit depth, transpilation time, and logical error rate
- Real hardware evaluation (10 runs per configuration on IBM Fez) for the same metrics

Real hardware runs require a configured IBM Quantum account and access to `ibm_fez` (or another Heron-family backend); simulator runs work out of the box with no IBM account needed.

You are encouraged to use and/or modify these tests if working on the transpiler as they're a useful starting point for benchmarking new passes or extensions against Qiskit's transpiler.

## Limitations

This transpiler prioritizes clarity and pedagogical value over performance. It does not match Qiskit's optimization level, producing more gates and deeper circuits than Qiskit's transpiler across all tested configurations, since it performs a single SABRE trial (vs. Qiskit's multiple randomized trials) and applies lighter gate-level optimization. See the accompanying paper for a detailed performance comparison and error-rate analysis on real IBM hardware. The translation pass prioritized the available IBM Quantum hardware as of June 2026 (Heron r2), so it might not be able to transform into any basis gate set without additional modifications.


## Authors

- **Stefan Bia** — Faculty of Automation and Computer Science, Technical University of Cluj-Napoca, bia.ca.stefan@student.utcluj.ro
- **Adrian Colesa** — Faculty of Automation and Computer Science, Technical University of Cluj-Napoca, Adrian.Colesa@campus.utcluj.ro