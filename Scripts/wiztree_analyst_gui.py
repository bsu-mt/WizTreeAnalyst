#!/usr/bin/env python3
"""Small GUI: export a WizTree report, pick two reports, compare, save the result."""
import os
import subprocess
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_reports import summarize

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "WizTreeReports"
WIZTREE_EXE = "wiztree64.exe"  # ponytail: assumes it's on PATH; hardcode full path here if not


def existing_drives():
    if not REPORTS_DIR.exists():
        return []
    return sorted(d.name for d in REPORTS_DIR.iterdir() if d.is_dir())


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WizTree Analyst")
        self.geometry("620x680")

        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        self.drives = existing_drives() or ["C"]
        self.drive = tk.StringVar(value=self.drives[0])
        ttk.Label(top, text="Drive:").pack(side="left")
        self.drive_menu = ttk.OptionMenu(top, self.drive, self.drives[0], *self.drives, command=lambda _: self.refresh_list())
        self.drive_menu.pack(side="left", padx=5)
        ttk.Button(top, text="Add drive", command=self.add_drive).pack(side="left", padx=5)
        ttk.Button(top, text="Export report", command=self.export_report).pack(side="left", padx=5)
        ttk.Button(top, text="Refresh list", command=self.refresh_list).pack(side="left", padx=5)

        ttk.Label(self, text="Double click to choose files (up to 2):").pack(anchor="w", padx=10)
        self.listbox = tk.Listbox(self, selectmode="browse", height=6)
        self.listbox.pack(fill="both", padx=10, pady=5)
        self.listbox.bind("<Double-Button-1>", lambda e: self.add_to_compare())

        pick = ttk.Frame(self, padding=(10, 0))
        pick.pack(fill="x")
        self.slot_a = tk.StringVar(value="(none)")
        self.slot_b = tk.StringVar(value="(none)")
        ttk.Label(pick, text="Compare:").pack(side="left")
        ttk.Label(pick, textvariable=self.slot_a, width=28, relief="sunken").pack(side="left", padx=5)
        ttk.Label(pick, text="vs").pack(side="left")
        ttk.Label(pick, textvariable=self.slot_b, width=28, relief="sunken").pack(side="left", padx=5)
        ttk.Button(pick, text="Clear", command=self.clear_slots).pack(side="left", padx=5)

        self._slots = []  # selected filenames, max 2
        self._result_file = None
        ttk.Button(self, text="Compare", command=self.run_compare).pack(pady=5)

        result_header = ttk.Frame(self, padding=(10, 0))
        result_header.pack(fill="x")
        ttk.Label(result_header, text="Comparison result:").pack(side="left")
        ttk.Button(result_header, text="Open result file", command=self.open_result_file).pack(side="right")

        self.output = tk.Text(self, height=20)
        self.output.pack(fill="both", expand=True, padx=10, pady=5)

        self.refresh_list()

    def drive_dir(self):
        d = REPORTS_DIR / self.drive.get()
        d.mkdir(parents=True, exist_ok=True)
        return d

    def add_drive(self):
        letter = simpledialog.askstring("Add drive", "Drive letter (e.g. R):", parent=self)
        if not letter:
            return
        letter = letter.strip().rstrip(":").upper()
        if len(letter) != 1 or not letter.isalpha():
            messagebox.showerror("Invalid drive", "Enter a single drive letter, e.g. R")
            return

        (REPORTS_DIR / letter / "results").mkdir(parents=True, exist_ok=True)
        if letter not in self.drives:
            self.drives.append(letter)
            self.drives.sort()
            menu = self.drive_menu["menu"]
            menu.delete(0, "end")
            for d in self.drives:
                menu.add_command(label=d, command=lambda v=d: (self.drive.set(v), self.refresh_list()))
        self.drive.set(letter)
        self.refresh_list()

    def refresh_list(self):
        self.listbox.delete(0, "end")
        for f in sorted(self.drive_dir().glob("*.csv")):
            self.listbox.insert("end", f.name)
        self.clear_slots()

    def add_to_compare(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("No selection", "Select a report in the list first.")
            return
        name = self.listbox.get(sel[0])
        if name in self._slots:
            return
        if len(self._slots) >= 2:
            messagebox.showwarning("Already have 2", "Clear a slot before adding another.")
            return
        self._slots.append(name)
        (self.slot_a if len(self._slots) == 1 else self.slot_b).set(name)

    def clear_slots(self):
        self._slots = []
        self.slot_a.set("(none)")
        self.slot_b.set("(none)")

    def export_report(self):
        drive = self.drive.get()
        out_file = self.drive_dir() / f"WizTree_{time.strftime('%Y%m%d%H%M%S')}.csv"
        try:
            subprocess.run(
                [WIZTREE_EXE, f"{drive}:", f"/export={out_file}",
                 "/admin=1", "/exportfolders=1", "/exportfiles=0"],
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as e:
            messagebox.showerror("Export failed", str(e))
            return
        # /admin=1 relaunches WizTree elevated and returns immediately, before
        # the elevated process finishes writing the file — so poll for it.
        self._wait_for_export(out_file)

    def _wait_for_export(self, out_file, attempts=20):
        if out_file.exists() or attempts <= 0:
            self.refresh_list()
            return
        self.after(500, lambda: self._wait_for_export(out_file, attempts - 1))

    def run_compare(self):
        if len(self._slots) != 2:
            messagebox.showwarning("Select 2 files", "Double-click two reports in the list to compare.")
            return
        old_name, new_name = sorted(self._slots)  # older filename sorts first
        old_path = self.drive_dir() / old_name
        new_path = self.drive_dir() / new_name

        lines = summarize(str(old_path), str(new_path))
        self.output.delete("1.0", "end")
        self.output.insert("end", "\n".join(lines))

        results_dir = self.drive_dir() / "results"
        results_dir.mkdir(exist_ok=True)
        result_file = results_dir / f"compare_{old_path.stem}_vs_{new_path.stem}.txt"
        result_file.write_text("\n".join(lines), encoding="utf-8")
        self._result_file = result_file
        messagebox.showinfo("Done", f"Saved to {result_file}")

    def open_result_file(self):
        if not self._result_file or not self._result_file.exists():
            messagebox.showwarning("No result yet", "Run a comparison first.")
            return
        os.startfile(self._result_file)


if __name__ == "__main__":
    App().mainloop()
