import shutil
from pathlib import Path

import pytest

from multisizer import MultisizerRun
from multisizer.cli import OVERVIEW, main, write_histogram_csv

DATA = Path(__file__).parent / 'data'
M3_FILE = DATA / 'example.#M3'
Z2_FILE = DATA / 'example.=#Z2'
FIXTURES = [M3_FILE, Z2_FILE]


def copy_into(tmp_path, fixture):
    return Path(shutil.copy(fixture, tmp_path))


def test_bare_command_prints_the_overview(capsys):
    assert main([]) == 0
    assert capsys.readouterr().out == OVERVIEW


@pytest.mark.parametrize('fixture', FIXTURES, ids=lambda p: p.name)
def test_histogram_csv_copies_the_file_strings(fixture, tmp_path):
    run = MultisizerRun(copy_into(tmp_path, fixture))
    out = write_histogram_csv(run)
    assert out == tmp_path / (fixture.name + '.histogram.csv')
    edges = run.arrays['#Bindiam']
    counts = run.arrays['#Binheight']
    lines = out.read_text().splitlines()
    assert lines[0] == 'lower_um,upper_um,count'
    assert len(lines) == len(edges)  # header + one row per bin
    assert lines[1] == f'{edges[0]},{edges[1]},{counts[0]}'
    assert lines[-1] == f'{edges[-2]},{edges[-1]},{counts[-2]}'


def test_dump_writes_the_pulse_table_only_when_there_are_pulses(tmp_path, capsys):
    m3 = copy_into(tmp_path, M3_FILE)
    z2 = copy_into(tmp_path, Z2_FILE)
    assert main(['dump', str(m3), str(z2)]) == 0
    out, err = capsys.readouterr()
    assert out.splitlines() == [
        f'{m3}.histogram.csv',
        f'{m3}.pulses.csv',
        f'{z2}.histogram.csv',
    ]
    assert err == ''
    lines = Path(f'{m3}.pulses.csv').read_text().splitlines()
    assert lines[0] == 'MaxHeight,MidHeight,Width,Area,Gain,MaxGainStage,MidGainStage,Flagged'
    assert lines[1] == '1555,1492,72,418,17,1,1,False'
    assert len(lines) == 1 + 4604
    assert not Path(f'{z2}.pulses.csv').exists()


def test_dump_reports_a_nonzero_trailing_count(tmp_path, capsys):
    path = tmp_path / 'trailing.=#Z2'
    path.write_text('[#Bindiam]\r\n0\r\n1\r\n2\r\n[#Binheight]\r\n5\r\n6\r\n7\r\n')
    assert main(['dump', str(path)]) == 0
    table = path.with_name('trailing.=#Z2.histogram.csv').read_text()
    assert table == 'lower_um,upper_um,count\n0,1,5\n1,2,6\n'
    assert 'trailing #Binheight entry is 7' in capsys.readouterr().err


def test_bad_files_are_reported_and_the_rest_still_run(tmp_path, capsys):
    missing = tmp_path / 'missing.#M3'
    text = tmp_path / 'notes.txt'
    text.write_text('not a run file\n')
    good = copy_into(tmp_path, Z2_FILE)
    assert main(['dump', str(missing), str(text), str(good)]) == 1
    assert good.with_name(good.name + '.histogram.csv').exists()
    err = capsys.readouterr().err
    assert 'missing.#M3' in err
    assert 'notes.txt' in err
