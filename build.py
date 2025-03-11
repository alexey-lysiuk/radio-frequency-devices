#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
#    Copyright (C) 2025 Alexey Lysiuk
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import csv
import os
import re
import sys
from decimal import Decimal

sys.dont_write_bytecode = True


_unit_prefixes = {
    'М': Decimal('1'),
    'Г': Decimal('1000'),
    'к': Decimal('0.001'),
    'К': Decimal('0.001'),  # wrong character case
    'K': Decimal('0.001'),  # latin character
    'M': Decimal('1')  # latin character
}

_number_pattern = r'(\d+(?:[,.]\d+)?)'
_unit_prefixes_string = ''.join(_unit_prefixes.keys())
_unit_prefix_pattern = f'([{_unit_prefixes_string}])Гц'
_frequency_regexp = re.compile(fr'{_number_pattern}(?:(?:-|...){_number_pattern})?\s*{_unit_prefix_pattern}')


class _StrDec(Decimal):
    def __repr__(self):
        return str(self)


def _tonumber(value: str, unit_prefix: str):
    value = value.replace(',', '.')
    return _StrDec(Decimal(value) * _unit_prefixes[unit_prefix])


def _is_446_extra_space(string: str) -> bool:
    suffixes = (
        # Puxing PX-800/PX-820
        '446,3-446, 4 МГц',
        # Puxing PX-V9
        '446,3-446, 4 МГц \n\n\n\n---\n430-440 МГц',
        # Hytera MD785
        '446,3-446, 4 МГц   ',
        # Hytera PD405 U(1)
        '446,3-446, 4 МГц '
    )

    for suffix in suffixes:
        if string.endswith(suffix):
            return True

    return False


def _apply_frequencies_fixes(string: str) -> str:
    if string == '2400-2483,5\n\n\n':
        # Missing units in HYUNDAI MOBIS ADB11H8EE
        return string[:-3] + 'МГц'
    elif string == '27, 140-27,150 МГц\n':
        # Erroneous space after decimal separator in MAISTO 82066/81322
        return '27,140-27,150 МГц\n'
    elif string == '13,56-13,56 МГц\n\n':
        # Same starting and ending frequencies in Ridango DV15SE
        return '13,56МГц'
    elif string == '868,6-868,6 МГц':
        # Same starting and ending frequencies in HDL-MCIP-RF.../HDL-MP...
        return '868,6МГц'
    elif string.endswith('5-137-825 МГц\n150-150,05 МГц    '):
        # Wrong decimal separator in two ORBCOMM devices
        return string.replace('137-825', '137,825')
    elif string.endswith('6-467-1 МГц\n'):
        # Wrong decimal separator in ATEL ADA-C450 and WeTelecom WM-D300
        return string.replace('467-1', '467,1')
    elif string.endswith('1477-1497б5 МГц'):
        # Wrong decimal separator in two Airspan AS Wipll 1,5 devices
        return string.replace('-1497б5', '-1497,5')
    elif string.endswith('423-420 МГц\n440-442,125 МГц\n442,525-446 МГц\n446,4-447,725 МГц\n448,15-450 МГц'):
        # Mixed starting and ending frequencies in Satelline-EASy
        return string.replace('---\n413-430 МГц/\n423-420 МГц\n440-442,125 МГц\n', '')  # remove duplicates
    elif string.endswith('\n18,3; 21,881;25,; 40,662; 43,756 кГц'):
        # Missing units in SONY SVD112...
        return string[:string.rfind('\n')] + ' 18,3кГц;21,881кГц;25кГц;40,662кГц;43,756кГц'
    elif string.startswith('5250-5250 МГц'):
        # Incorrect starting frequency in SkyMAN R5000-Sc/5L.54.63.22
        return string.replace('5250-', '5150-')
    elif string.startswith('8247-842,97 МГц'):
        # Incorrect starting frequencies in Samsung SM-B311V (Gusto 3),
        # LG LGL18VC (Classic), LG LG-VS425LPP (Optimus Zone 3)
        return string.replace('8247-', '824,07-').replace('8697-', '869,07-')
    elif _is_446_extra_space(string):
        # Erroneous space after decimal separator
        return string.replace('3-446, 4', '3-446,4')

    return string


def _parse_frequencies(string: str) -> list:
    string = _apply_frequencies_fixes(string)
    frequency_strings = [entry for entry in _frequency_regexp.findall(string)]
    frequencies = []

    for freqstr in frequency_strings:
        unit_prefix = freqstr[2]
        start = _tonumber(freqstr[0], unit_prefix)
        frequency = [start]

        if freqstr[1]:  # frequency range
            end = _tonumber(freqstr[1], unit_prefix)

            if start >= end:
                print(f'Bad frequency range, {start} >= {end}')
                continue

            frequency.append(end)

        frequencies.append(frequency)

    frequencies.sort()

    return frequencies


def _format_multiline_string(source: str):
    if not source:
        return ''

    string = source.strip()
    string = string.replace('---', '')
    string = re.sub(r'\n\n+', '\n', string)
    string = string.replace('\n', '<br>')
    return string.replace("'", r"\'")


class Column:
    NAME = 1
    TECHNOLOGY = 5
    PURPOSE = 6
    FREQUENCIES = 7


class ValuePool(dict):
    def __missing__(self, key):
        value = len(self)
        self[key] = value
        return value

    def write(self, f, name):
        f.write(f'{name}=[\n')

        for key in self.keys():
            f.write(f"'{key}',\n")

        f.write('];\n')


class Device:
    _technologies = ValuePool()
    _purposes = ValuePool()
    _frequencies = ValuePool()

    def __init__(self, name: str, technology: str, purpose: str, frequencies: list):
        self.name = name.replace('\n', ' ').strip().replace("'", r"\'")

        technology = _format_multiline_string(technology)
        self.technology = Device._technologies[technology]

        purpose = _format_multiline_string(purpose)
        self.purpose = Device._purposes[purpose]

        frequency_values = []

        for frequency in frequencies:
            frequency_key = tuple(frequency)
            frequency_value = Device._frequencies[frequency_key]
            frequency_values.append(frequency_value)

        self.frequencies = frequency_values

    def write(self, f):
        f.write(f"['{self.name}',t[{self.technology}],p[{self.purpose}],[")

        for frequency in self.frequencies:
            f.write(f'f[{frequency}],')

        f.write(']],\n')

    @staticmethod
    def write_pools(f):
        Device._technologies.write(f, 't')
        Device._purposes.write(f, 'p')

        f.write(f'f=[\n')

        for frequency in Device._frequencies:
            f.write(f'[{frequency[0]}')

            if len(frequency) > 1:
                f.write(f',{frequency[1]}')

            f.write('],')

        f.write('];\n')


class DeviceList:
    def __init__(self, path: str):
        self.path = path
        self.devices = []

        if not self._load_cache():
            self._load_excel()

    def export(self):
        self_path = os.path.dirname(__file__)
        output_path = os.path.join(self_path, 'dist', 'devices.js')
        output_path = os.path.realpath(output_path)

        with open(output_path, 'w') as f:
            Device.write_pools(f)

            f.write('let devices = [\n')

            for device in self.devices:
                device.write(f)

            f.write('];\n')

    def _add_device(self, row: list):
        column_count = len(row)

        # There are two .xslx files with the same data but different number of columns
        if column_count == 14 or column_count == 256:
            if frequencies_string := row[Column.FREQUENCIES]:
                if frequencies := _parse_frequencies(frequencies_string):
                    device = Device(
                        row[Column.NAME],
                        row[Column.TECHNOLOGY],
                        row[Column.PURPOSE],
                        frequencies)
                    self.devices.append(device)

    def _cache_path(self) -> str:
        return self.path + '.csv'

    def _load_cache(self):
        cache_path = self._cache_path()

        if not os.path.exists(cache_path):
            return False

        source_time = os.stat(self.path).st_mtime
        cache_time = os.stat(cache_path).st_mtime

        if cache_time < source_time:
            return False

        with open(cache_path, newline='') as f:
            reader = csv.reader(f)

            for row in reader:
                self._add_device(row)

        return True

    def _load_excel(self):
        # noinspection PyUnresolvedReferences
        import openpyxl

        workbook = openpyxl.open(self.path)
        worksheet = workbook.worksheets[0]

        with open(self._cache_path(), 'w', newline='') as f:
            cache_writer = csv.writer(f)

            for excel_row in worksheet.rows:
                row = [cell.value for cell in excel_row]
                cache_writer.writerow(row)
                self._add_device(row)


def _main():
    argc = len(sys.argv)
    devices_path = sys.argv[1] if argc >= 2 else 'devices.xlsx'

    DeviceList(devices_path).export()


if __name__ == '__main__':
    _main()
