"""Simple simulation of the Quantum Secret Hitler game.

This module provides a ``QuantumSecretHitlerGame`` class capable of running a
single simulated game with the rules sketched in ``IQU_CODE_FEST_CapitalQ.pdf``.
The implementation focuses on the quantum-inspired mechanics while keeping the
control flow lightweight so it can run entirely offline.
"""

from __future__ import annotations

import numpy as np
from typing import List, Optional
import sys

from . import constants
from .game import (
    uniform_role_state,
    uniform_hitler_state,
    quantum_vote,
    policy_selection,
    biased_bullet_state,
)


class Player:
    """Represents a player in the game."""

    def __init__(self, index: int, role: str) -> None:
        self.index = index
        self.role = role  # "liberal" or "fascist"
        self.alive = True


class QuantumSecretHitlerGame:
    """Manage a single run of the game with 10 players."""

    def __init__(self) -> None:
        self.num_players = constants.PLAYER_COUNT
        self.players = self._assign_roles()
        self.hitler = self._assign_hitler()
        self.president = np.random.randint(self.num_players)

        print("Initial roles:")
        for p in self.players:
            print(f"  Player {p.index}: {p.role}")
        lib_prob = constants.LIBERAL_PLAYERS / constants.PLAYER_COUNT
        print(
            f"Role probabilities -> Liberal: {lib_prob:.2f}, Fascist: {1-lib_prob:.2f}"
        )
        fascists = [p.index for p in self.players if p.role == "fascist"]
        if fascists:
            hit_prob = 1 / len(fascists)
            print(
                f"Hitler probability for each fascist: {hit_prob:.2f}"
            )
        print(f"Hitler is player {self.hitler}\n")

        self.liberal_policies = 0
        self.fascist_policies = 0
        self.failed_elections = 0
        self.round = 0

    # ------------------------------------------------------------------
    # Role assignment helpers
    # ------------------------------------------------------------------
    def _assign_roles(self) -> List[Player]:
        """Measure ``|Ψ_role⟩`` once to distribute liberal/fascist roles."""
        state = uniform_role_state(
            constants.PLAYER_COUNT, constants.LIBERAL_PLAYERS
        )
        probs = state.probabilities()
        uniform_prob = 1 / len(probs)
        print(f"Role assignment probability for each valid state: {uniform_prob:.4f}")
        outcome = np.random.choice(2 ** self.num_players, p=probs)
        bits = list(map(int, bin(outcome)[2:].zfill(self.num_players)))
        players: List[Player] = []
        for i, b in enumerate(bits):
            role = "liberal" if b == 0 else "fascist"
            players.append(Player(i, role))
        return players

    def _assign_hitler(self) -> int:
        """Randomly pick the initial Hitler among the fascists."""
        fascists = [p.index for p in self.players if p.role == "fascist"]
        state = uniform_hitler_state(len(fascists))
        hit_prob = 1 / len(fascists)
        dist = {f: round(hit_prob, 2) for f in fascists}
        print(f"Initial Hitler distribution: {dist}")
        outcome = np.random.choice(fascists, p=[hit_prob] * len(fascists))
        return outcome

    # ------------------------------------------------------------------
    # Basic helpers
    # ------------------------------------------------------------------
    def _alive_players(self) -> List[Player]:
        return [p for p in self.players if p.alive]

    def _next_president(self) -> None:
        idx = self.president
        while True:
            idx = (idx + 1) % self.num_players
            if self.players[idx].alive:
                self.president = idx
                break

    # ------------------------------------------------------------------
    # Game mechanics
    # ------------------------------------------------------------------
    def _elect_chancellor(self) -> Optional[int]:
        alive = self._alive_players()
        choices = [p.index for p in alive if p.index != self.president]
        candidate = int(np.random.choice(choices))

        print(f"President {self.president} nominates player {candidate} as chancellor")

        votes = [1 if p.role == self.players[candidate].role else 0 for p in alive]
        print(f"Votes: {votes}")
        success, state = quantum_vote(votes, constants.VOTE_PHI)
        probs = state.probabilities()
        print(
            f"Vote probabilities -> Fail: {probs[0]:.2f}, Success: {probs[1]:.2f}"
        )
        if success:
            print("Election successful")
        else:
            print("Election failed")
        if success:
            self.failed_elections = 0
            return candidate
        self.failed_elections += 1
        return None

    def _enact_policy(self, chancellor: Optional[int]) -> None:
        if chancellor is None:
            if self.failed_elections >= 3:
                policy, state = policy_selection(0, 0, constants.POLICY_PHI)
                probs = state.probabilities()
                print(
                    f"Policy probabilities -> Liberal: {probs[0]:.2f}, Fascist: {probs[1]:.2f}"
                )
                self.failed_elections = 0
                print("Top-deck policy due to anarchy")
            else:
                print("No chancellor elected")
                return
        else:
            pres_bias = 1 if self.players[self.president].role == "liberal" else 0
            chan_bias = 1 if self.players[chancellor].role == "liberal" else 0
            policy, state = policy_selection(pres_bias, chan_bias, constants.POLICY_PHI)
            probs = state.probabilities()
            print(
                f"Policy probabilities -> Liberal: {probs[0]:.2f}, Fascist: {probs[1]:.2f}"
            )
            print(f"Chancellor {chancellor} enacts {'Liberal' if policy == 0 else 'Fascist'} policy")

        if policy == 0:
            self.liberal_policies += 1
        else:
            self.fascist_policies += 1
        print(
            f"Policies -> Liberal: {self.liberal_policies}, Fascist: {self.fascist_policies}"
        )

    def _bullet_phase(self) -> None:
        if self.fascist_policies not in (4, 5):
            return
        alive = self._alive_players()
        choices = [p.index for p in alive if p.index != self.president]
        target = int(np.random.choice(choices))
        print(f"President {self.president} chooses policy kill targeting player {target}")
        target_local = [p.index for p in alive].index(target)
        bullet_state = biased_bullet_state(len(alive), target_local)
        probs = bullet_state.probabilities()
        dist = {alive[i].index: round(prob, 2) for i, prob in enumerate(probs)}
        print(f"Bullet probabilities: {dist}")
        shot_idx_local = int(np.random.choice(len(alive), p=probs))
        shot = alive[shot_idx_local].index
        self.players[shot].alive = False
        print(f"Player {shot} was shot")
        if shot == self.hitler:
            print("Hitler was eliminated!")
        if shot == self.hitler:
            # Immediate liberal victory
            self.liberal_policies = constants.LIBERAL_WIN_POLICIES

    def _check_winner(self, chancellor: Optional[int]) -> Optional[str]:
        if (
            chancellor is not None
            and chancellor == self.hitler
            and self.fascist_policies >= 3
        ):
            print("Hitler elected as chancellor - Fascists win!")
            return "Fascists"
        if self.fascist_policies >= constants.FASCIST_WIN_POLICIES:
            print("Fascists have enough policies to win")
            return "Fascists"
        if self.liberal_policies >= constants.LIBERAL_WIN_POLICIES:
            print("Liberals enacted enough policies to win")
            return "Liberals"
        return None

    def play_round(self) -> Optional[str]:
        self.round += 1
        print(f"\n--- Round {self.round} ---")
        print(f"President is {self.president}")
        chancellor = self._elect_chancellor()
        self._enact_policy(chancellor)
        self._bullet_phase()
        winner = self._check_winner(chancellor)
        self._next_president()
        return winner

    def play_game(self) -> str:
        while True:
            result = self.play_round()
            if result:
                print(f"\n{result} win the game!")
                return result


if __name__ == "__main__":
    game = QuantumSecretHitlerGame()
    game.play_game()
