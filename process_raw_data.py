#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
import re

FILENAME = 'test.#M3'

def parse_M3_file(filename):
    '''
    Parse a Beckman Coulter Multisizer 3 data file.
    '''
    data = {}
    section = None
    
    p_section = re.compile('^\[(.*)\]')
    p_field = re.compile('^(.*)=(.*)')
    
    with open(filename) as fid:
        for line in fid:

            m_section = p_section.match(line)
            m_field = p_field.match(line)

            if m_section:
                section = m_section.groups()[0]
                data[section] = {}
                continue
            elif m_field:
                k, v = m_field.groups()
                data[section][k] = v.strip()
            else:
                if 'Values' not in data[section]:
                    data[section]['Values'] = []
                data[section]['Values'].append(line.strip())

    return data

def decode_pulse(pulse_array):
    return [int(n, 16) for n in pulse_array.split(',')]

def extract_pulses(M3_data):
    '''
    Pulse hex format:
    - MaxHeight
    - MidHeight
    - Width
    - Area
    - Gain
    '''
    Pulses = M3_data['#Pulses5hex']['Values']
    return np.array([decode_pulse(p) for p in Pulses])

def extract_diameters(M3_data):

    Instrument = M3_data['instrument']

    Kd = float(Instrument['Kd'])
    MaxHtCorr = int(Instrument['MaxHtCorr'])
    CountsPerVolt = 838861  # 1/V
    Current = int(Instrument['Current']) / 1000  # mA
    Resistance = 25 * int(Instrument['Gain'])  # kohm

    Pulses = extract_pulses(M3_data)
    Height = Pulses[:, 0] + MaxHtCorr
    Diameter = Kd * (Height / (CountsPerVolt * Current * Resistance)) ** (1/3)

    return Diameter

def extract_volumes(M3_data):

    Diameter = extract_diameters(M3_data)
    Volume = np.pi / 6 * Diameter ** 3

    return Volume

M3_data = parse_M3_file(FILENAME)
Diameter = extract_diameters(M3_data)

plt.close('all')
plt.hist(np.log10(Diameter), bins=25, histtype='step')

tick_labels = np.arange(1, np.ceil(Diameter.max() + 1), dtype=int)
tick_locs = np.log10(tick_labels)
plt.xticks(tick_locs, tick_labels)

plt.xlabel('Particle Diameter (um)')
plt.ylabel('Number')
plt.title('Differential Number')
