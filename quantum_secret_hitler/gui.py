"""Simple Tkinter interface for the Quantum Secret Hitler game."""
from __future__ import annotations

import io
import tkinter as tk
from contextlib import redirect_stdout

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from .simulate import QuantumSecretHitlerGame
from . import constants


class SecretHitlerGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Quantum Secret Hitler")
        self.game = None

        self.text = tk.Text(self, width=80, height=20)
        self.text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        button_frame = tk.Frame(self)
        button_frame.pack(side=tk.TOP, fill=tk.X)
        self.next_btn = tk.Button(button_frame, text="Next Round", command=self.next_round)
        self.next_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.quit_btn = tk.Button(button_frame, text="Quit", command=self.destroy)
        self.quit_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # matplotlib figure for policy counts
        self.fig, self.ax = plt.subplots(figsize=(4, 3))
        self.ax.set_ylim(0, max(constants.LIBERAL_WIN_POLICIES, constants.FASCIST_WIN_POLICIES))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._start_game()

    def _start_game(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.game = QuantumSecretHitlerGame()
        self._append(buf.getvalue())
        self._update_plot()

    def _append(self, text: str) -> None:
        self.text.insert(tk.END, text)
        self.text.see(tk.END)

    def _update_plot(self) -> None:
        self.ax.clear()
        self.ax.bar([
            "Liberal",
            "Fascist",
        ], [self.game.liberal_policies, self.game.fascist_policies], color=["blue", "red"])
        self.ax.set_ylim(0, max(constants.LIBERAL_WIN_POLICIES, constants.FASCIST_WIN_POLICIES))
        self.ax.set_title(f"Round {self.game.round}")
        self.canvas.draw()

    def next_round(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            winner = self.game.play_round(interactive=False)
        self._append(buf.getvalue())
        self._update_plot()
        if winner:
            self._append(f"\n{winner} win the game!\n")
            self.next_btn.config(state=tk.DISABLED)


def main() -> None:
    app = SecretHitlerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
