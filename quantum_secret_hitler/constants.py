"""Module storing constants for the Quantum Secret Hitler game.

This module centralizes numeric values so the rest of the code can simply
import ``constants``.  In addition to the deck composition, we fix the total
number of players to 10 and the distribution of liberals and fascists.
The angles used in the voting and policy selection procedures are derived
from the ``DELTA`` parameter described in ``IQU_CODE_FEST_CapitalQ.pdf``.
"""

from __future__ import annotations

import numpy as np

# Number of liberal and fascist policies in the deck
LIBERAL_POLICIES = 6
FASCIST_POLICIES = 11
TOTAL_POLICIES = LIBERAL_POLICIES + FASCIST_POLICIES

# ---------------------------------------------------------------------------
# Player distribution
# ---------------------------------------------------------------------------

# Total number of people in the game.  The PDF explicitly considers a ten
# player session, so we keep that fixed for the simple simulator.
PLAYER_COUNT = 10

# For a ten-player game the classical distribution is six liberals and four
# fascists.  The ``FASCIST_PLAYERS`` value counts everyone who initially plays
# for the fascist team.  The Hitler role is chosen among them.
LIBERAL_PLAYERS = 6
FASCIST_PLAYERS = PLAYER_COUNT - LIBERAL_PLAYERS

# ---------------------------------------------------------------------------
# Voting and policy selection parameters
# ---------------------------------------------------------------------------

# Constant ``c`` controlling the bias of an individual vote.  The instructions
# give ``0 < c < 2`` so that ``delta = c/(N-1)`` remains below ``1/2``.
VOTE_BIAS_C = 1.0
# Derived "delta" value and rotation angle ``phi`` used in the voting circuit.
VOTE_DELTA = VOTE_BIAS_C / (PLAYER_COUNT - 1)
VOTE_PHI = np.arcsin(2 * VOTE_DELTA)

# ``POLICY_PHI`` controls the bias when the president and chancellor draw a
# policy.  It is chosen so that if both players favour a liberal action the
# probability of drawing a liberal policy is ``LIBERAL_POLICY_PROBABILITY``.

# Probability of drawing a liberal policy when both president and
# chancellor favour liberal action
LIBERAL_POLICY_PROBABILITY = 0.8

# Base angle describing the neutral deck state. ``POLICY_PHI`` is chosen so
# that applying it twice raises the liberal probability to
# ``LIBERAL_POLICY_PROBABILITY`` when both leaders favour a liberal policy.
_theta = np.arccos(np.sqrt(LIBERAL_POLICIES / TOTAL_POLICIES))
POLICY_PHI = np.arccos(np.sqrt(LIBERAL_POLICY_PROBABILITY)) - _theta

# Bullet mechanic probabilities
BULLET_TARGET_PROB = 0.8
BULLET_OTHER_PROB = 0.2

# Bounds for the unsharp measurement parameter
MIN_ETA = 0.0
MAX_ETA = 1.0

# ---------------------------------------------------------------------------
# Victory conditions
# ---------------------------------------------------------------------------

# Number of liberal and fascist policies required for each side to win.
LIBERAL_WIN_POLICIES = 5
FASCIST_WIN_POLICIES = 6

# ---------------------------------------------------------------------------
# Hitler distribution update
# ---------------------------------------------------------------------------

# Factor used to bias the Hitler probability toward a player when they take a
# fascist-leaning action.  A value greater than ``1`` increases the chance that
# the player is Hitler while keeping a non-zero probability for others.
HITLER_BIAS_FACTOR = 1.2
