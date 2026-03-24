
import numpy as np


BASIS_SETS = {
    "eagle":            frozenset({"ecr", "rz", "sx", "x", "id"}),
    "heron":            frozenset({"cz",  "rz", "sx", "x", "id"}),
    "heron_fractional": frozenset({"cz",  "rz", "sx", "x", "id", "rx", "rzz"}),
}


_SINGLE_QUBIT = {

    "h": lambda q, p: [
        ("rz", [np.pi / 2], [q[0]]),
        ("sx", [],          [q[0]]),
        ("rz", [np.pi / 2], [q[0]]),
    ],

    "y": lambda q, p: [
        ("x",  [],       [q[0]]),
        ("rz", [np.pi],  [q[0]]),
    ],

    "z": lambda q, p: [
        ("rz", [np.pi], [q[0]]),
    ],

    "t":   lambda q, p: [("rz", [np.pi / 4],  [q[0]])],
    "tdg": lambda q, p: [("rz", [-np.pi / 4], [q[0]])],

    "s":   lambda q, p: [("rz", [np.pi / 2],  [q[0]])],
    "sdg": lambda q, p: [("rz", [-np.pi / 2], [q[0]])],

    "ry": lambda q, p: [
        ("rz", [-np.pi / 2],      [q[0]]),
        ("sx", [],                 [q[0]]),
        ("rz", [p[0] + np.pi / 2], [q[0]]),
    ],

    "rx": lambda q, p: [
        ("rz", [-np.pi / 2],      [q[0]]),
        ("sx", [],                 [q[0]]),
        ("rz", [p[0] - np.pi / 2], [q[0]]),
    ],

    "u1": lambda q, p: [
        ("rz", [p[0]], [q[0]]),
    ],

    "u2": lambda q, p: [
        ("rz", [p[1] - np.pi / 2], [q[0]]),
        ("sx", [],                  [q[0]]),
        ("rz", [p[0] + np.pi / 2], [q[0]]),
    ],

    "u3": lambda q, p: [
        ("rz", [p[2]],          [q[0]]),
        ("sx", [],               [q[0]]),
        ("rz", [p[0] + np.pi],  [q[0]]),
        ("sx", [],               [q[0]]),
        ("rz", [p[1] + np.pi],  [q[0]]),
    ],

    "u": lambda q, p: [
        ("rz", [p[2]],          [q[0]]),
        ("sx", [],               [q[0]]),
        ("rz", [p[0] + np.pi],  [q[0]]),
        ("sx", [],               [q[0]]),
        ("rz", [p[1] + np.pi],  [q[0]]),
    ],

    "p": lambda q, p: [
        ("rz", [p[0]], [q[0]]),
    ],
}

_TWO_QUBIT_ECR = {

    "cx": lambda q, p: [
        ("rz",  [-np.pi / 2], [q[1]]),
        ("sx",  [],            [q[1]]),
        ("rz",  [np.pi / 2],  [q[1]]),
        ("ecr", [],            [q[0], q[1]]),
        ("x",   [],            [q[0]]),
    ],

    "cz": lambda q, p: [
        ("h",  [], [q[1]]),
        ("cx", [], [q[0], q[1]]),
        ("h",  [], [q[1]]),
    ],

    "swap": lambda q, p: [
        ("cx", [], [q[0], q[1]]),
        ("cx", [], [q[1], q[0]]),
        ("cx", [], [q[0], q[1]]),
    ],

    "ccx": lambda q, p: [
        ("h",   [], [q[2]]),
        ("cx",  [], [q[1], q[2]]),
        ("tdg", [], [q[2]]),
        ("cx",  [], [q[0], q[2]]),
        ("t",   [], [q[2]]),
        ("cx",  [], [q[1], q[2]]),
        ("tdg", [], [q[2]]),
        ("cx",  [], [q[0], q[2]]),
        ("t",   [], [q[1]]),
        ("t",   [], [q[2]]),
        ("h",   [], [q[2]]),
        ("cx",  [], [q[0], q[1]]),
        ("t",   [], [q[0]]),
        ("tdg", [], [q[1]]),
        ("cx",  [], [q[0], q[1]]),
    ],

    "rzz": lambda q, p: [
        ("cx", [],     [q[0], q[1]]),
        ("rz", [p[0]], [q[1]]),
        ("cx", [],     [q[0], q[1]]),
    ],

    "rxx": lambda q, p: [
        ("h",   [],     [q[0]]),
        ("h",   [],     [q[1]]),
        ("rzz", [p[0]], [q[0], q[1]]),
        ("h",   [],     [q[0]]),
        ("h",   [],     [q[1]]),
    ],

    "iswap": lambda q, p: [
        ("s",  [], [q[0]]),
        ("s",  [], [q[1]]),
        ("h",  [], [q[0]]),
        ("cx", [], [q[0], q[1]]),
        ("cx", [], [q[1], q[0]]),
        ("h",  [], [q[1]]),
    ],
}

_TWO_QUBIT_CZ = {

    "cx": lambda q, p: [
        ("h",  [], [q[1]]),
        ("cz", [], [q[0], q[1]]),
        ("h",  [], [q[1]]),
    ],

    "ecr": lambda q, p: [
        ("rz", [np.pi / 2],  [q[0]]),
        ("sx", [],            [q[0]]),
        ("cx", [],            [q[0], q[1]]),
        ("x",  [],            [q[1]]),
    ],

    "swap": lambda q, p: [
        ("cx", [], [q[0], q[1]]),
        ("cx", [], [q[1], q[0]]),
        ("cx", [], [q[0], q[1]]),
    ],

    "ccx": lambda q, p: [
        ("h",   [], [q[2]]),
        ("cx",  [], [q[1], q[2]]),
        ("tdg", [], [q[2]]),
        ("cx",  [], [q[0], q[2]]),
        ("t",   [], [q[2]]),
        ("cx",  [], [q[1], q[2]]),
        ("tdg", [], [q[2]]),
        ("cx",  [], [q[0], q[2]]),
        ("t",   [], [q[1]]),
        ("t",   [], [q[2]]),
        ("h",   [], [q[2]]),
        ("cx",  [], [q[0], q[1]]),
        ("t",   [], [q[0]]),
        ("tdg", [], [q[1]]),
        ("cx",  [], [q[0], q[1]]),
    ],

    "rzz": lambda q, p: [
        ("cx", [],     [q[0], q[1]]),
        ("rz", [p[0]], [q[1]]),
        ("cx", [],     [q[0], q[1]]),
    ],

    "rxx": lambda q, p: [
        ("h",   [],     [q[0]]),
        ("h",   [],     [q[1]]),
        ("rzz", [p[0]], [q[0], q[1]]),
        ("h",   [],     [q[0]]),
        ("h",   [],     [q[1]]),
    ],

    "iswap": lambda q, p: [
        ("s",  [], [q[0]]),
        ("s",  [], [q[1]]),
        ("h",  [], [q[0]]),
        ("cx", [], [q[0], q[1]]),
        ("cx", [], [q[1], q[0]]),
        ("h",  [], [q[1]]),
    ],
}


EQUIVALENCES_ECR = {**_SINGLE_QUBIT, **_TWO_QUBIT_ECR}
EQUIVALENCES_CZ  = {**_SINGLE_QUBIT, **_TWO_QUBIT_CZ}

EQUIVALENCES_FOR_BASIS = {
    "eagle":            EQUIVALENCES_ECR,
    "heron":            EQUIVALENCES_CZ,
    "heron_fractional": EQUIVALENCES_CZ,
}