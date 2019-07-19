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

def parse_pulse(pulse_array):
    return [int(n, 16) for n in pulse_array.split(',')]

def extract_volumes(raw_data):
    '''
    Pulse hex format:
    - MaxHeight
    - MidHeight
    - Width
    - Area
    - Gain
    '''
    Instrument = raw_data['instrument']

    Kd = float(Instrument['Kd'])
    MaxHtCorr = int(Instrument['MaxHtCorr'])
    CountsPerVolt = 838861  # 1/V
    Current = int(Instrument['Current']) / 1000  # mA
    Resistance = 25 * int(Instrument['Gain'])  # kohm

    Pulses = raw_data['#Pulses5hex']['Values']
    MaxHeight_iter = (parse_pulse(p)[0] for p in Pulses)
    MaxHeight = np.fromiter(MaxHeight_iter, dtype=int)

    Height = MaxHeight + MaxHtCorr
    Diameter = Kd * (Height / (CountsPerVolt * Current * Resistance)) ** (1/3)
    Volume = np.pi / 6 * Diameter ** 3

    return Diameter

raw_data = parse_M3_file(FILENAME)
Volume = extract_volumes(raw_data)

plt.close('all')
plt.hist(Volume, bins=101, histtype='step')
plt.xlabel('Particle Diameter (um)')
plt.ylabel('Number')
plt.title('Differential Number')
