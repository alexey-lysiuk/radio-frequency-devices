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
import pathlib
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


def _apply_frequencies_fixes(string: str) -> str:
    if string == '2400-2483,5\n\n\n':
        # Missing units in HYUNDAI MOBIS ADB11H8EE
        return string.replace('\n\n\n', 'МГц')
    elif '137,585-137-825' in string:
        # Wrong decimal separator in two ORBCOMM devices
        return string.replace('137-825', '137,825')

    return string


def _parse_frequencies(string: str) -> list:
    string = _apply_frequencies_fixes(string)
    frequency_strings = [entry for entry in _frequency_regexp.findall(string)]
    frequencies = []

    for freqstr in frequency_strings:
        unit_prefix = freqstr[2]

        # List because of string conversion to JavaScript array
        frequency = [_tonumber(freqstr[0], unit_prefix)]

        if freqstr[1] != '':  # frequency range
            frequency.append(_tonumber(freqstr[1], unit_prefix))

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


class Device:
    def __init__(self, name: str, technology: str, purpose: str, frequencies: list):
        self.name = name.replace('\n', ' ').strip().replace("'", r"\'")
        self.technology = _format_multiline_string(technology)
        self.purpose = _format_multiline_string(purpose)
        self.frequencies = frequencies

    def write(self, f):
        f.write(f"['{self.name}', '{self.technology}', '{self.purpose}', {self.frequencies}],\n")


class DeviceList:
    def __init__(self, path: str):
        self.path = path
        self.devices = []

        if not self._load_cache():
            self._load_excel()

    def export(self):
        self_path = pathlib.Path(__file__)
        output_path = self_path.parent.parent / 'dist/devices.js'

        with open(output_path, 'w') as f:
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
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} file.xlsx')
        sys.exit(1)

    DeviceList(sys.argv[1]).export()

    sys.exit(0)


if __name__ == '__main__':
    _main()
