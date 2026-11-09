'''
Top-level command `multisizer`: write a run file's tables beside it.
'''

import argparse
import csv
import sys
from pathlib import Path

from .run import MultisizerRun

OVERVIEW = '''\
multisizer: tables from Beckman Coulter run files (.#M3, .=#Z2)

  multisizer dump FILE...   Write FILE.histogram.csv beside each run file, one
                            lower_um,upper_um,count row per bin, plus
                            FILE.pulses.csv when the file has pulses (M3)
  multisizer                Show this overview

Commands take --help for options. Install and usage notes are in
README.md.
'''


def sibling(run: MultisizerRun, suffix: str) -> Path:
    '''
    An output path beside the run file: its full name plus a suffix.
    '''
    return run.path.with_name(run.path.name + suffix)


def write_histogram_csv(run: MultisizerRun) -> Path:
    '''
    Write FILE.histogram.csv: one lower_um,upper_um,count row per bin.

    The numbers are copied from the run file as-is, so nothing is re-rounded.
    The trailing #Binheight entry has no upper edge and is not written; it is
    zero in every file seen, so a warning goes to stderr if it is not.
    '''
    if '#Bindiam' not in run.arrays or '#Binheight' not in run.arrays:
        raise ValueError('no histogram sections found')

    edges = run.arrays['#Bindiam']
    counts = run.arrays['#Binheight']

    path = sibling(run, '.histogram.csv')
    with path.open('w', newline='') as fh:
        writer = csv.writer(fh, lineterminator='\n')
        writer.writerow(['lower_um', 'upper_um', 'count'])
        writer.writerows(zip(edges[:-1], edges[1:], counts[:-1]))

    trailing = float(counts[-1])
    if trailing:
        print(
            f'warning: {run.path.name}: trailing #Binheight entry is {trailing:g}, not 0; it was not written',
            file=sys.stderr,
        )

    return path


def write_pulses_csv(run: MultisizerRun) -> Path:
    '''
    Write FILE.pulses.csv: the decoded pulse table, one row per pulse,
    columns per PULSE_DTYPE.
    '''
    pulses = run.pulses

    path = sibling(run, '.pulses.csv')
    with path.open('w', newline='') as fh:
        writer = csv.writer(fh, lineterminator='\n')
        writer.writerow(pulses.dtype.names)
        writer.writerows(pulses.tolist())

    return path


def dump(run: MultisizerRun) -> list[Path]:
    '''
    Write the histogram table, plus the pulse table when the file has pulses.
    Returns the paths written.
    '''
    written = [write_histogram_csv(run)]
    if run.has_pulses:
        written.append(write_pulses_csv(run))
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog='multisizer',
        description=OVERVIEW,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='command', metavar='COMMAND')
    dump_parser = subparsers.add_parser(
        'dump',
        help='write FILE.histogram.csv, plus FILE.pulses.csv when the file has pulses',
        description='Write FILE.histogram.csv, plus FILE.pulses.csv when the file has pulses.',
    )
    dump_parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        metavar='FILE',
        help='a .#M3 or .=#Z2 run file',
    )
    args = parser.parse_args(argv)

    if args.command is None:
        print(OVERVIEW, end='')
        return 0

    failures = 0
    for path in args.files:
        try:
            for written in dump(MultisizerRun(path)):
                print(written)
        except (OSError, ValueError) as exc:
            print(f'error: {path}: {exc}', file=sys.stderr)
            failures += 1

    return 1 if failures else 0
