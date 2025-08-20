import pandas as pd
import tkinter as tk
from tkinter import ttk
import json



# === Load Player Data ===
df = pd.read_csv("Ark.csv")

# === Initialize Tkinter ===
root = tk.Tk()
root.title("Ark Team Balancer")

# === State Dictionaries ===
availability = {}
top_team_lock = {}
bottom_team_lock = {}
team_locks = {}
tp_priority = {}

# === Select All Toggle ===
def toggle_select_all():
    state = select_all_var.get()
    for var in availability.values():
        var.set(state)
    update_selection_count()

# === Enforce Mutual Lock Exclusion ===
def update_lockboxes(player_name):
    if top_team_lock[player_name].get():
        team_locks[player_name]["bottom"].config(state="disabled")
    else:
        team_locks[player_name]["bottom"].config(state="normal")

    if bottom_team_lock[player_name].get():
        team_locks[player_name]["top"].config(state="disabled")
    else:
        team_locks[player_name]["top"].config(state="normal")
def balance_teams(unassigned):
    sorted_players = unassigned.sort_values(by="Matchmaking", ascending=False)
    top_team, bottom_team = [], []
    top_total = bottom_total = 0

    for _, player in sorted_players.iterrows():
        if top_total <= bottom_total:
            top_team.append(player)
            top_total += player["Matchmaking"]
        else:
            bottom_team.append(player)
            bottom_total += player["Matchmaking"]

    return pd.DataFrame(top_team), pd.DataFrame(bottom_team)

def save_selection():
    selected = [name for name, var in availability.items() if var.get()]
    print(f"Saving {len(selected)} players...")  # Debug line
    with open("team_selection.json", "w") as f:
        json.dump({"selected": selected}, f)

def load_selection():
    try:
        with open("team_selection.json", "r") as f:
            data = json.load(f)
        for name in availability:
            availability[name].set(name in data.get("selected", []))
        update_selection_count()
    except FileNotFoundError:
        print("No saved selection found.")


def show_results(top_team, bottom_team, tp_players):
    def refresh():
        listbox_top.delete(0, tk.END)
        listbox_bottom.delete(0, tk.END)
        
        for name in top_team["Name"]:
            display = f"{name} 🟠Teleport Priority" if name in tp_players else name
            listbox_top.insert(tk.END, display)

        for name in bottom_team["Name"]:
            display = f"{name} 🟠Teleport Priority" if name in tp_players else name
            listbox_bottom.insert(tk.END, display)

        label_top.config(text=f"🏔️ Top Team ({top_team['Matchmaking'].sum()} pts)")
        label_bottom.config(text=f"🏕️ Bottom Team ({bottom_team['Matchmaking'].sum()} pts)")
        gap = abs(top_team["Matchmaking"].sum() - bottom_team["Matchmaking"].sum())
        gap_label.config(text=f"⚖️ Power Gap: {gap} pts")

    def move_left():
        selection = listbox_bottom.curselection()
        if not selection: return
        name = listbox_bottom.get(selection)
        player = bottom_team[bottom_team["Name"] == name]
        if not player.empty:
            bottom_team.drop(player.index, inplace=True)
            top_team.loc[len(top_team)] = player.iloc[0]
            refresh()

    def move_right():
        selection = listbox_top.curselection()
        if not selection: return
        name = listbox_top.get(selection)
        player = top_team[top_team["Name"] == name]
        if not player.empty:
            top_team.drop(player.index, inplace=True)
            bottom_team.loc[len(bottom_team)] = player.iloc[0]
            refresh()

    win = tk.Toplevel(root)
    win.title("Team Assignment Results")

    frame = ttk.Frame(win, padding=20)
    frame.grid()

    label_top = ttk.Label(frame, text="", font=("Segoe UI", 12, "bold"))
    label_top.grid(column=0, row=0, padx=10)
    label_bottom = ttk.Label(frame, text="", font=("Segoe UI", 12, "bold"))
    label_bottom.grid(column=2, row=0, padx=10)

    listbox_top = tk.Listbox(frame, height=15, width=30)
    listbox_top.grid(column=0, row=1)
    listbox_bottom = tk.Listbox(frame, height=15, width=30)
    listbox_bottom.grid(column=2, row=1)

    ttk.Button(frame, text="⬅️ Move to Top", command=move_left).grid(column=1, row=1)
    ttk.Button(frame, text="Move to Bottom ➡️", command=move_right).grid(column=1, row=2, pady=5)

    gap_label = ttk.Label(frame, text="", font=("Segoe UI", 10))
    gap_label.grid(column=0, row=3, columnspan=3, pady=(10, 0))

    refresh()

def submit():
    available_players = df[df["Name"].isin([n for n in df["Name"] if availability[n].get()])]

    top_locked = [n for n in df["Name"] if top_team_lock[n].get()]
    bottom_locked = [n for n in df["Name"] if bottom_team_lock[n].get()]

    top_team = available_players[available_players["Name"].isin(top_locked)].copy()
    bottom_team = available_players[available_players["Name"].isin(bottom_locked)].copy()

    tp_players = [n for n in df["Name"] if tp_priority[n].get()]

    unassigned = available_players[
        ~available_players["Name"].isin(top_locked + bottom_locked)
    ]

    balanced_top, balanced_bottom = balance_teams(unassigned)
    top_team = pd.concat([top_team, balanced_top], ignore_index=True)
    bottom_team = pd.concat([bottom_team, balanced_bottom], ignore_index=True)

    show_results(top_team, bottom_team, tp_players)

def update_selection_count():
    count = sum(var.get() for var in availability.values())
    selection_count_label.config(text=f"Selected: {count} players")

# === GUI Layout (continued) ===
frame = ttk.Frame(root, padding=20)
frame.grid()

select_all_var = tk.BooleanVar()
ttk.Checkbutton(frame, text="Select All", variable=select_all_var,
                command=toggle_select_all).grid(column=0, row=0, sticky="w", pady=(0, 10))

ttk.Label(frame, text="Select Available Players", font=("Segoe UI", 12, "bold")).grid(column=0, row=1, pady=(0, 10))

for idx, name in enumerate(df["Name"], start=2):
    availability[name] = tk.BooleanVar()
    ttk.Label(frame, text=name).grid(column=0, row=idx, sticky="w")
    ttk.Checkbutton(frame, variable=availability[name], command=update_selection_count).grid(column=1, row=idx, sticky="w")

ttk.Label(frame, text="Lock Players to Teams", font=("Segoe UI", 12, "bold")).grid(column=2, row=1, pady=(0, 10))
ttk.Label(frame, text="TP Priority", font=("Segoe UI", 12, "bold")).grid(column=4, row=1, pady=(0, 10))

for idx, name in enumerate(df["Name"], start=2):
    top_team_lock[name] = tk.BooleanVar()
    bottom_team_lock[name] = tk.BooleanVar()

    top_cb = ttk.Checkbutton(frame, text="Top", variable=top_team_lock[name],
                             command=lambda n=name: update_lockboxes(n))
    bottom_cb = ttk.Checkbutton(frame, text="Bottom", variable=bottom_team_lock[name],
                                command=lambda n=name: update_lockboxes(n))

    top_cb.grid(column=2, row=idx)
    bottom_cb.grid(column=3, row=idx)

    tp_priority[name] = tk.BooleanVar()
    tp_cb = ttk.Checkbutton(frame, text="TP", variable=tp_priority[name])
    tp_cb.grid(column=4, row=idx)  # New 5th column

    team_locks[name] = {"top": top_cb, "bottom": bottom_cb}

ttk.Button(frame, text="Confirm", command=submit).grid(column=0, row=len(df) + 3, columnspan=4, pady=15)

selection_count_label = ttk.Label(frame, text="Selected: 0 players")
selection_count_label.grid(column=0, row=len(df) + 2, columnspan=4, pady=(10, 0))

ttk.Button(frame, text="💾 Save Selection", command=save_selection).grid(column=0, row=len(df) + 4, pady=(10, 0))
ttk.Button(frame, text="📂 Load Selection", command=load_selection).grid(column=1, row=len(df) + 4, pady=(10, 0))

root.mainloop()