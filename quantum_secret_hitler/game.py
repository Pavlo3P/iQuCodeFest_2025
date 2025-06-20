"""Quantum Secret Hitler utilities.

This module implements key quantum mechanics for the Secret Hitler variant
outlined in ``IQU_CODE_FEST_CapitalQ.pdf``. It focuses on preparing the
initial role distribution, running the quantum voting procedure, selecting
policies with quantum bias, the randomized bullet mechanic, and unsharp role
measurements.
"""
from __future__ import annotations

import itertools
from typing import List, Tuple

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit.quantum_info import Statevector, Kraus

from . import constants


def uniform_role_state(num_players: int, num_liberals: int) -> Statevector:
    """Return the superposition assigning roles as in Eq. (1)."""
    if not 0 < num_liberals < num_players:
        raise ValueError("num_liberals must be between 1 and num_players - 1")

    dim = 2 ** num_players
    amps = np.zeros(dim, dtype=complex)
    for bits in itertools.product([0, 1], repeat=num_players):
        if bits.count(0) == num_liberals:
            idx = int("".join(str(b) for b in bits), 2)
            amps[idx] = 1
    amps /= np.linalg.norm(amps)
    return Statevector(amps)


def uniform_hitler_state(num_fascists: int) -> Statevector:
    """Return the initial Hitler distribution among the fascists (Eq. 2)."""
    if num_fascists <= 0:
        raise ValueError("There must be at least one fascist")

    dim = 2 ** num_fascists
    amps = np.zeros(dim, dtype=complex)
    for j in range(num_fascists):
        amps[1 << j] = 1
    amps /= np.sqrt(num_fascists)
    return Statevector(amps)


def quantum_vote(votes: List[int], phi: float) -> Tuple[int, Statevector]:
    """Run the quantum voting procedure for a proposed chancellor."""
    qc = QuantumCircuit(1)
    qc.h(0)
    for v in votes:
        qc.ry(phi if v else -phi, 0)

    qc.save_statevector()
    backend = Aer.get_backend("aer_simulator")
    result = backend.run(qc).result()
    state = Statevector(result.get_statevector())
    outcome = np.random.choice([0, 1], p=state.probabilities())
    return int(outcome), state


def policy_selection(pres_bias: int, chan_bias: int, phi: float) -> Tuple[int, Statevector]:
    """Simulate policy drawing as described in the PDF."""
    qc = QuantumCircuit(1)
    qc.initialize(
        [
            np.sqrt(constants.LIBERAL_POLICIES / constants.TOTAL_POLICIES),
            np.sqrt(constants.FASCIST_POLICIES / constants.TOTAL_POLICIES),
        ],
        0,
    )

    qc.ry(phi if pres_bias == 1 else -phi / 2, 0)
    qc.ry(phi if chan_bias == 1 else -phi / 2, 0)

    qc.save_statevector()
    backend = Aer.get_backend("aer_simulator")
    result = backend.run(qc).result()
    state = Statevector(result.get_statevector())
    outcome = np.random.choice([0, 1], p=state.probabilities())
    return int(outcome), state


def biased_bullet_state(num_players: int, target: int) -> Statevector:
    """Return ``|Ψ_i⟩`` (Eq. 11) favouring ``target`` to be shot."""
    if not 0 <= target < num_players:
        raise ValueError("target index out of range")
    amps = np.full(
        num_players,
        np.sqrt(constants.BULLET_OTHER_PROB / (num_players - 1)),
        dtype=complex,
    )
    amps[target] = np.sqrt(constants.BULLET_TARGET_PROB)
    return Statevector(amps)


def unsharp_measure(state: Statevector, eta: float) -> Statevector:
    """Apply an unsharp measurement with parameter ``eta`` to ``state``."""
    if not constants.MIN_ETA <= eta <= constants.MAX_ETA:
        raise ValueError(
            f"eta must be between {constants.MIN_ETA} and {constants.MAX_ETA}"
        )
    mh = np.array([[np.sqrt((1 - eta) / 2), 0], [0, np.sqrt((1 + eta) / 2)]])
    mnh = np.array([[np.sqrt((1 + eta) / 2), 0], [0, np.sqrt((1 - eta) / 2)]])
    kraus = [mh, mnh]
    channel = Kraus(kraus)
    probs = channel.probabilities(state)
    outcome = np.random.choice([0, 1], p=probs)
    new_state = channel._channel_matrices[outcome] @ state.data
    return Statevector(new_state)
