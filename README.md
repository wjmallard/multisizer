# multisizer

A parser for Beckman Coulter Multisizer data files.

## Install

To install into a uv project:

```
uv add git+https://github.com/wjmallard/multisizer
```

For development:

```
git clone git@github.com:wjmallard/multisizer.git
cd multisizer
uv sync
```

The project's `.envrc` puts `.venv/bin` on PATH via
[direnv](https://direnv.net) (`direnv allow` once), so inside this directory
the `uv run` prefix is unnecessary: `pytest` and `multisizer` just work.
Unlike `uv run`, bare commands don't auto-sync the venv — run `uv sync` after
changing dependencies or entry points.

## Usage

```python
from multisizer import MultisizerRun

run = MultisizerRun('sample.#M3')

# The histogram computed by the instrument's software.
edges, counts = run.histogram

# Everything else in the file, as strings, keyed by section.
run.fields['instrument']['Kd']   # '38.899'
run.arrays['#Bindiam'][:3]       # ['0.682', '0.689482', '0.697045']

# Multisizer 3 files optionally include every raw pulse.
if run.has_pulses:
    pulses = run.pulses                  # structured array; see PULSE_DTYPE for field names
    diameters = run.diameters            # microns
    volumes = run.volumes                # femtoliters
```

## Command line

`multisizer dump FILE...` writes tables beside each run file it is given:
`FILE.histogram.csv`, one `lower_um,upper_um,count` row per bin. If the
file includes raw pulses, it decodes them and writes them as a table in
`FILE.pulses.csv` with columns specified in `PULSE_DTYPE`.

```
multisizer dump runs/*.=#Z2
```

## License

MIT
