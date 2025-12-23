import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
from collections import defaultdict

# Prevent animation garbage collection
anim_object = None


#CACHE LOGIC 

class CacheSim:
    def __init__(self, size, seq):
        self.size = size
        self.seq = seq

    def run(self, update_func):
        cache = []
        log = []
        freq = defaultdict(int)

        for i, x in enumerate(self.seq):
            freq[x] += 1
            hit = x in cache
            old_cache = cache.copy()
            cache = update_func(cache, x, i, freq)
            log.append((x, old_cache, cache.copy(), hit))

        return log

    #  LRU 
    def LRU(self):
        def up(c, x, i, f):
            if x in c:
                c.remove(x)
            else:
                if len(c) == self.size:
                    c.pop(0)
            c.append(x)
            return c
        return self.run(up)

    #  MRU 
    def MRU(self):
        def up(c, x, i, f):
            if x in c:
                c.remove(x)
            else:
                if len(c) == self.size:
                    c.pop()
            c.append(x)
            return c
        return self.run(up)

    # FIFO 
    def FIFO(self):
        def up(c, x, i, f):
            if x not in c:
                if len(c) == self.size:
                    c.pop(0)
                c.append(x)
            return c
        return self.run(up)

    #  LFU 
    def LFU(self):
        def up(c, x, i, f):
            if x not in c:
                if len(c) == self.size:
                    victim = min(c, key=lambda k: f[k])
                    c.remove(victim)
                c.append(x)
            return c
        return self.run(up)

    #  LIFO 
    def LIFO(self):
        def up(c, x, i, f):
            if x not in c:
                if len(c) == self.size:
                    c.pop()  
                c.append(x)
            return c
        return self.run(up)


#  ANIMATION + TIMELINE 

def animate_cache(log, cache_size):
    global anim_object

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.set_title("Cache Animation Timeline")
    ax.set_xlim(0, cache_size)
    ax.set_ylim(-1, len(log))
    ax.set_xlabel("Cache Blocks")
    ax.set_ylabel("Timeline Steps")

    colors = {
        "hit": "#00ff66",
        "normal": "#1e90ff",
        "evicted": "#ffaa00"
    }

    frames = []

    for step, (access, old_cache, new_cache, hit) in enumerate(log):
        row = [""] * cache_size
        color_row = ["#333"] * cache_size

        for j, val in enumerate(new_cache):
            row[j] = val
            color_row[j] = colors["hit"] if hit else colors["normal"]

        for val in old_cache:
            if val not in new_cache:
                idx = old_cache.index(val)
                if idx < cache_size:
                    row[idx] = val
                    color_row[idx] = colors["evicted"]

        frames.append((step, access, row, color_row))

    def update(frame_id):
        step, access, row, color_row = frames[frame_id]
        ax.clear()
        ax.set_title(f"Access: {access} | Step {step}")
        ax.set_xlim(0, cache_size)
        ax.set_ylim(-1, len(log))
        ax.set_xlabel("Cache Blocks")
        ax.set_ylabel("Timeline Steps")

        for j in range(cache_size):
            ax.add_patch(
                plt.Rectangle((j, step), 1, 1, color=color_row[j])
            )
            if row[j] != "":
                ax.text(
                    j + 0.5, step + 0.5, str(row[j]),
                    ha="center", va="center",
                    fontsize=12, color="white"
                )

        ax.invert_yaxis()
        ax.grid(True)

    anim_object = FuncAnimation(
        fig, update,
        frames=len(frames),
        interval=600,
        repeat=False
    )

    return fig


#  GUI LOGIC 

def run_policy(policy):
    global canvas_widget

    output.delete("1.0", "end")

    try:
        seq = list(map(int, entry_seq.get().split(",")))
        size = int(entry_size.get())
    except:
        output.insert("end", "Invalid input format\n")
        return

    sim = CacheSim(size, seq)

    func = {
        "LRU": sim.LRU,
        "MRU": sim.MRU,
        "FIFO": sim.FIFO,
        "LFU": sim.LFU,
        "LIFO": sim.LIFO
    }[policy]

    log = func()

    output.insert("end", f"--- {policy} ---\n")
    output.insert("end", "Access | Cache | HIT/MISS\n")
    output.insert("end", "--------------------------\n")

    for access, old, new, hit in log:
        output.insert(
            "end",
            f"{access:<6} | {new} | {'HIT' if hit else 'MISS'}\n"
        )

    fig = animate_cache(log, size)

    if canvas_widget:
        canvas_widget.get_tk_widget().destroy()

    canvas_widget = FigureCanvasTkAgg(fig, app)
    canvas_widget.draw()
    canvas_widget.get_tk_widget().pack(pady=10)


#  WINDOW UI 

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Cache Replacement")
app.geometry("1100x800")

title = ctk.CTkLabel(
    app,
    text="Cache Replacement",
    font=("Arial", 26, "bold")
)
title.pack(pady=10)

frame = ctk.CTkFrame(app)
frame.pack(fill="x", padx=20, pady=10)

ctk.CTkLabel(frame, text="Cache Size:").grid(row=0, column=0, padx=10)
entry_size = ctk.CTkEntry(frame, width=80)
entry_size.insert(0, "3")
entry_size.grid(row=0, column=1)

ctk.CTkLabel(frame, text="Access Sequence:").grid(row=1, column=0, padx=10)
entry_seq = ctk.CTkEntry(frame, width=400)
entry_seq.insert(0, "1,2,3,2,1,4,5,1")
entry_seq.grid(row=1, column=1)

btns = ctk.CTkFrame(app)
btns.pack(pady=10)

policies = ["LRU", "MRU", "FIFO", "LFU", "LIFO"]

for p in policies:
    ctk.CTkButton(
        btns,
        text=p,
        width=140,
        height=40,
        command=lambda pol=p: run_policy(pol)
    ).pack(side="left", padx=8)

output = ctk.CTkTextbox(app, width=1000, height=200)
output.pack(pady=10)

canvas_widget = None

app.mainloop()
