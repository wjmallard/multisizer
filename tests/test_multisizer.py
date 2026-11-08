from pathlib import Path

import numpy as np
import pytest

from multisizer import PULSE_DTYPE, MultisizerRun

DATA = Path(__file__).parent / 'data'
M3_FILE = DATA / 'example.#M3'
Z2_FILE = DATA / 'example.=#Z2'


@pytest.fixture(scope='module')
def m3():
    return MultisizerRun(M3_FILE)


@pytest.fixture(scope='module')
def z2():
    return MultisizerRun(Z2_FILE)


def test_sections_land_in_fields_and_arrays(m3, z2):
    for run in (m3, z2):
        assert 'multisizer' in run.fields['common']['Program'].lower()
        assert '#Bindiam' in run.arrays
        assert '#Binheight' in run.arrays


def test_repr_summarizes_the_file(m3, z2, tmp_path):
    assert repr(m3) == '<MultisizerRun example.#M3: 300 bins, 4604 pulses>'
    assert repr(z2) == '<MultisizerRun example.=#Z2: 256 bins>'
    bare = tmp_path / 'bare.=#Z2'
    bare.write_text('[common]\r\n')
    assert repr(MultisizerRun(bare)) == '<MultisizerRun bare.=#Z2>'


def test_value_may_contain_equals_sign(z2):
    # The Z2 extension itself contains '=': values split on the first one only.
    assert z2.fields['common']['Filename'] == 'example.=#Z2'


def test_data_before_first_section_is_an_error(tmp_path):
    path = tmp_path / 'bad.=#Z2'
    path.write_text('stray=1\r\n[common]\r\n')
    with pytest.raises(ValueError):
        MultisizerRun(path)


def test_histogram_has_nbins_plus_one_entries(m3, z2):
    for run in (m3, z2):
        n_bins = int(run.fields['instrument']['nBins'])
        edges, counts = run.histogram
        assert len(edges) == len(counts) == n_bins + 1
        assert np.all(np.diff(edges) > 0)
        assert run.histogram is run.histogram


def test_z2_bins_are_linear_in_volume(z2):
    edges, _ = z2.histogram
    i = np.arange(1, len(edges))
    assert np.allclose(edges[1:], edges[1] * i ** (1 / 3), rtol=1e-3)


def test_z2_has_no_pulses(z2):
    assert not z2.has_pulses
    with pytest.raises(ValueError):
        z2.pulses


def test_z2_histogram_is_the_replicate_average(z2):
    _, counts = z2.histogram
    reps = int(z2.fields['Z2']['Reps'])
    totals = [int(z2.fields['Z2'][f'ThCnts{r}'].split(',')[1]) for r in range(reps)]
    assert counts.sum() == pytest.approx(np.mean(totals), rel=0.005)


def test_m3_pulses(m3):
    assert m3.has_pulses
    pulses = m3.pulses
    assert pulses.dtype == PULSE_DTYPE
    assert len(pulses) == int(m3.fields['instrument']['nPulses']) == 4604
    assert pulses[0].tolist() == (1555, 1492, 72, 418, 17, 1, 1, False)
    assert pulses['Flagged'].sum() == 4
    assert m3.pulses is pulses


def test_heights_are_quantized_by_gain_stage(m3):
    pulses = m3.pulses
    for stage, quantum in [(1, 1), (2, 4), (3, 16), (4, 64)]:
        heights = pulses['MaxHeight'][pulses['MaxGainStage'] == stage]
        assert np.gcd.reduce(heights) == quantum


def test_diameters_reproduce_the_instrument_histogram(m3):
    edges, official = m3.histogram
    diameters = m3.diameters
    counts, _ = np.histogram(diameters, bins=edges)
    assert np.corrcoef(official[:-1], counts)[0, 1] > 0.9997
    # The file records the one pulse below the smallest edge as Smalls= 1.
    assert (diameters < edges[0]).sum() == int(m3.fields['instrument']['Smalls'])
    stats = m3.fields['SizeStats']
    inside = diameters[diameters >= edges[0]]
    assert inside.mean() == pytest.approx(float(stats['Mean']), rel=2e-3)
    assert np.percentile(inside, 90) == pytest.approx(float(stats['D90']), rel=2e-3)


def test_volumes_follow_from_diameters(m3):
    good = ~m3.pulses['Flagged']
    diameters = m3.diameters[good]
    assert len(diameters) == 4600
    assert np.allclose(m3.volumes[good], np.pi / 6 * diameters ** 3)
    assert m3.diameters is m3.diameters
