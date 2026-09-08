# सभा · SABHĀ

Several AI members sit together and work on one task. One of them chairs.

Standard library only — no pip install, nothing to vendor. Members can be
local Ollama models, any CLI agent, or fakes for testing.

## Two ways to run it

**Terminal:**

```bash
python3 sabha.py nakli      # a fake session, needs nothing installed
python3 sabha.py jaancho    # which members are alive
python3 sabha.py chalao "what you want done"
python3 sabha.py hisaab     # what past sessions cost
```

**A window:**

```bash
python3 sabha.py darpan
```

दर्पण shows the members and whether each is ready, every task with its state
in colour, and the log as it fills. Work runs in the background, so the window
stays responsive and can be asked to stop — it finishes the task in hand
rather than being killed mid-write.

It is tkinter, which ships with Python, so the stdlib-only promise holds. On
Debian and Ubuntu tkinter is packaged separately: `sudo apt install python3-tk`.

## The members

Edit `niyukti.json`. Three kinds:

| kind | what it is |
|---|---|
| `ollama` | a local model — give its name in `model` |
| `aujaar` | any CLI agent — give the command in `hukum` |
| `nakli` | a fake. Runs nothing. For testing the machinery. |

Set `"chalu": false` to bench a member without deleting it.

Each member has a budget in `adhiktam_akshar` (roughly four characters per
token). Start low — around 50,000 — confirm the session behaves, then raise it.
Leaving a large budget running overnight gets expensive.

## What is in here

```
sabha.py              the command line
sabha/sabhapati.py    the chair: splits work, picks who does what, checks results
sabha/sadasya.py      a member
sabha/karyasuchi.py   the task list, dependencies and states
sabha/sandesh.py      messages between members
sabha/raksha.py       budget and permission limits
sabha/nireekshan.py   the log
sabha/darpan.py       the window
tools/sab_jaancho.py  51 checks
tools/darpan_jaancho.py  23 checks for the window
```

## Test

```bash
python3 tools/sab_jaancho.py       # 51 checks
python3 tools/darpan_jaancho.py    # 23 checks, needs a display
```

The window tests build a real `Tk` and read real `Treeview` rows — nothing is
mocked. Without a display they say they were skipped rather than passing
quietly.

Longer notes, in Hindi: [`PADHO.txt`](PADHO.txt).

## Status

Working. `nakli` runs with nothing installed; real sessions need Ollama or a
CLI agent configured in `niyukti.json`.
