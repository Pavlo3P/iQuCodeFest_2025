"""Tkinter interface for the Quantum Secret Hitler game.

This GUI displays the players around a round table. The president is
highlighted and players are clickable so the user can choose the
chancellor nominee and bullet target. Side panels show the current
probability distributions and game state.
"""
from __future__ import annotations

import io
import math
import tkinter as tk
from contextlib import redirect_stdout
from typing import Dict, Optional

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from .simulate import QuantumSecretHitlerGame
from . import constants


PLAYER_RADIUS = 20
TABLE_RADIUS = 180
CANVAS_SIZE = 400


class SecretHitlerGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Quantum Secret Hitler")
        self.game = QuantumSecretHitlerGame()

        # --- widgets -----------------------------------------------------
        self.canvas = tk.Canvas(self, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="darkgreen")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        sidebar = tk.Frame(self)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log = tk.Text(sidebar, width=40, height=15)
        self.log.pack(fill=tk.BOTH, expand=True)

        self.instr = tk.Label(sidebar, text="Click 'Next Round' to begin")
        self.instr.pack(pady=4)

        ctrl = tk.Frame(sidebar)
        ctrl.pack(pady=4)
        self.next_btn = tk.Button(ctrl, text="Next Round", command=self.start_round)
        self.next_btn.pack(side=tk.LEFT)
        tk.Button(ctrl, text="Quit", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self.vote_frame = tk.LabelFrame(sidebar, text="Votes (1=yes,0=no)")
        self.vote_vars = [tk.IntVar(value=1) for _ in range(constants.PLAYER_COUNT)]
        for i, var in enumerate(self.vote_vars):
            tk.Checkbutton(self.vote_frame, text=f"P{i}", variable=var).pack(anchor="w")
        self.vote_frame.pack(pady=4)

        self.bias_frame = tk.LabelFrame(sidebar, text="Policy bias")
        self.pres_var = tk.IntVar(value=1)
        self.chan_var = tk.IntVar(value=1)
        tk.Checkbutton(self.bias_frame, text="President liberal", variable=self.pres_var).pack(anchor="w")
        tk.Checkbutton(self.bias_frame, text="Chancellor liberal", variable=self.chan_var).pack(anchor="w")
        self.bias_frame.pack(pady=4)

        self.resolve_btn = tk.Button(sidebar, text="Resolve", command=self.resolve_step, state=tk.DISABLED)
        self.resolve_btn.pack(pady=4)

        # probability plots
        self.fig, self.axes = plt.subplots(2, 2, figsize=(5, 4))
        self.fig.subplots_adjust(hspace=0.5, wspace=0.4)
        self.fig.tight_layout(pad=2.0)
        self.fig_canvas = FigureCanvasTkAgg(self.fig, master=sidebar)
        self.fig_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- state -------------------------------------------------------
        self.player_items: Dict[int, int] = {}
        self.state = "idle"
        self.candidate: Optional[int] = None
        self.chancellor: Optional[int] = None
        self.target: Optional[int] = None
        self.vote_probs = None

        self._append_log("Game started.\n")
        self.draw_players()
        self.update_plots()

    # ------------------------------------------------------------------
    def _append_log(self, text: str) -> None:
        self.log.insert(tk.END, text)
        self.log.see(tk.END)

    def draw_players(self) -> None:
        self.canvas.delete("all")
        cx = cy = CANVAS_SIZE // 2
        for p in self.game.players:
            angle = 2 * math.pi * p.index / self.game.num_players
            x = cx + TABLE_RADIUS * math.cos(angle)
            y = cy + TABLE_RADIUS * math.sin(angle)
            color = "blue" if p.role == "liberal" else "red"
            if not p.alive:
                color = "gray"
            item = self.canvas.create_oval(
                x - PLAYER_RADIUS,
                y - PLAYER_RADIUS,
                x + PLAYER_RADIUS,
                y + PLAYER_RADIUS,
                fill=color,
                outline="gold" if p.index == self.game.president else "black",
                width=3 if p.index == self.game.president else 1,
            )
            self.canvas.create_text(x, y, text=str(p.index), fill="white")
            self.player_items[p.index] = item

    def highlight_candidate(self) -> None:
        for idx, item in self.player_items.items():
            if idx == self.candidate:
                self.canvas.itemconfigure(item, outline="green", width=3)
            else:
                width = 3 if idx == self.game.president else 1
                outline = "gold" if idx == self.game.president else "black"
                self.canvas.itemconfigure(item, outline=outline, width=width)

    def _on_canvas_click(self, event) -> None:
        idx = self._player_at(event.x, event.y)
        if idx is None:
            return
        if self.state == "select_chancellor":
            if idx == self.game.president or not self.game.players[idx].alive:
                return
            self.candidate = idx
            self.highlight_candidate()
            alive = self.game._alive_players()
            for p in alive:
                self.vote_vars[p.index].set(1 if p.role == self.game.players[idx].role else 0)
            self.instr.config(text="Adjust votes then click Resolve")
            self.resolve_btn.config(state=tk.NORMAL)
            self.state = "vote_ready"
        elif self.state == "bullet":
            if idx == self.game.president or not self.game.players[idx].alive:
                return
            self.target = idx
            self.resolve_step()

    def _player_at(self, x: int, y: int) -> Optional[int]:
        for idx, item in self.player_items.items():
            bb = self.canvas.bbox(item)
            if bb and bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3]:
                return idx
        return None

    # ------------------------------------------------------------------
    def start_round(self) -> None:
        self._append_log(f"\n--- Round {self.game.round + 1} ---\n")
        self.draw_players()
        self.update_plots()
        self.instr.config(text="Select chancellor by clicking a player")
        self.state = "select_chancellor"
        self.candidate = None
        self.chancellor = None
        self.target = None
        self.resolve_btn.config(state=tk.DISABLED)

    def resolve_step(self) -> None:
        if self.state == "vote_ready":
            alive = self.game._alive_players()
            votes = [self.vote_vars[p.index].get() for p in alive]
            buf = io.StringIO()
            with redirect_stdout(buf):
                chancellor, self.vote_probs = self.game._elect_chancellor(False, self.candidate, votes)
            self.chancellor = chancellor
            self._append_log(buf.getvalue())
            self.update_plots()
            if chancellor is None:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    self.game._enact_policy(None, False)
                self._append_log(buf.getvalue())
                self.end_round()
            else:
                self.instr.config(text="Set policy biases then click Resolve")
                self.resolve_btn.config(state=tk.NORMAL)
                self.pres_var.set(1 if self.game.players[self.game.president].role == "liberal" else 0)
                self.chan_var.set(1 if self.game.players[chancellor].role == "liberal" else 0)
                self.state = "policy_ready"

        elif self.state == "policy_ready":
            pres_bias = self.pres_var.get()
            chan_bias = self.chan_var.get()
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.game._enact_policy(self.chancellor, False, pres_bias, chan_bias)
            self._append_log(buf.getvalue())
            self.update_plots()
            if self.game.fascist_policies in (4, 5):
                self.instr.config(text="Click a player to shoot")
                self.state = "bullet"
                self.resolve_btn.config(state=tk.DISABLED)
            else:
                self.end_round()

        elif self.state == "bullet":
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.game._bullet_phase(False, self.target)
            self._append_log(buf.getvalue())
            self.update_plots()
            self.end_round()

    def end_round(self) -> None:
        winner = self.game._check_winner(self.chancellor)
        if winner:
            self._append_log(f"\n{winner} win the game!\n")
            self.update_plots()
            self.instr.config(text="Game over")
            self.next_btn.config(state=tk.DISABLED)
            self.resolve_btn.config(state=tk.DISABLED)
            return
        self.game._next_president()
        self.draw_players()
        self.update_plots()
        if self.game.fascist_policies >= 3:
            self._append_log("Fascists can win by electing Hitler.\n")
        self.instr.config(text="Round finished. Click 'Next Round'")
        self.state = "idle"
        self.resolve_btn.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    def update_plots(self) -> None:
        ax_hitler, ax_vote, ax_fail, ax_policies = self.axes.flatten()
        ax_hitler.clear()
        labels = [str(k) for k in self.game.hitler_dist.keys()]
        probs = [self.game.hitler_dist[k] for k in self.game.hitler_dist]
        ax_hitler.bar(labels, probs, color="orange")
        ax_hitler.set_ylim(0, 1)
        ax_hitler.set_title("Hitler dist", fontsize=8)
        ax_hitler.tick_params(labelsize=8)

        ax_vote.clear()
        if self.vote_probs is not None:
            ax_vote.bar(["Fail", "Success"], self.vote_probs, color="purple")
            ax_vote.set_ylim(0, 1)
        ax_vote.set_title("Vote prob", fontsize=8)
        ax_vote.tick_params(labelsize=8)

        ax_fail.clear()
        ax_fail.bar(["Fails"], [self.game.failed_elections], color="gray")
        ax_fail.set_ylim(0, 3)
        ax_fail.set_title("Failed elections", fontsize=8)
        ax_fail.tick_params(labelsize=8)

        ax_policies.clear()
        ax_policies.bar(["Lib", "Fas"], [self.game.liberal_policies, self.game.fascist_policies], color=["blue", "red"])
        ax_policies.set_ylim(0, max(constants.LIBERAL_WIN_POLICIES, constants.FASCIST_WIN_POLICIES))
        ax_policies.set_title("Policies", fontsize=8)
        ax_policies.tick_params(labelsize=8)

        self.fig.tight_layout(pad=2.0)
        self.fig_canvas.draw()


def main() -> None:
    app = SecretHitlerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
