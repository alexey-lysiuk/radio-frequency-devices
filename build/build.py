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


def _cache_path(path: str) -> str:
    return path + '.csv'


def _load_cache(path: str) -> list:
    cache_path = _cache_path(path)

    if not os.path.exists(cache_path):
        return []

    source_time = os.stat(path).st_mtime
    cache_time = os.stat(cache_path).st_mtime

    if cache_time < source_time:
        return []

    with open(_cache_path(path), newline='') as f:
        reader = csv.reader(f)
        rows = [row for row in reader]

    return rows


def _load_excel(path: str) -> list:
    import openpyxl

    workbook = openpyxl.open(path)
    worksheet = workbook.worksheets[0]
    rows = [[cell.value for cell in row] for row in worksheet.rows]

    with open(_cache_path(path), 'w', newline='') as f:
        csv.writer(f).writerows(rows)

    return rows


_frequency_suffixes = {
    'М': Decimal('1'),
    'Г': Decimal('1000'),
    'к': Decimal('0.001'),
    'К': Decimal('0.001'),  # wrong character case
    'K': Decimal('0.001'),  # latin character
    'M': Decimal('1')  # latin character
}

_number_pattern = r'(\d+(?:[,.]\d+)?)'
_suffixes_string = ''.join(_frequency_suffixes.keys())
_suffix_pattern = f'([{_suffixes_string}])Гц'
_frequency_regexp = re.compile(fr'{_number_pattern}(?:(?:-|...){_number_pattern})?\s*{_suffix_pattern}')


class _StrDec(Decimal):
    def __repr__(self):
        return str(self)


def _tonumber(value: str, suffix: str):
    value = value.replace(',', '.')
    return _StrDec(Decimal(value) * _frequency_suffixes[suffix])


def _parse_frequencies(string: str) -> list:
    frequency_strings = [entry for entry in _frequency_regexp.findall(string)]
    frequencies = []

    for freqstr in frequency_strings:
        suffix = freqstr[2]

        # List because of string conversion to JavaScript array
        frequency = [_tonumber(freqstr[0], suffix)]

        if freqstr[1] != '':  # frequency range
            frequency.append(_tonumber(freqstr[1], suffix))

        frequencies.append(frequency)

    if len(frequencies) == 0:
        # TODO: support very bogus case with no suffix at all
        print(string)
    else:
        frequencies.sort()

    return frequencies


def _add_device(f, row):
    column_count = 14

    if len(row) != column_count:
        return

    frequencies_column = 7
    frequencies_string = row[frequencies_column]

    if not frequencies_string:
        return

    frequencies = _parse_frequencies(frequencies_string)

    if frequencies:
        name = row[1].replace('\n', ' ').strip().replace("'", r"\'")
        f.write(f"['{name}', {frequencies}],\n")


def _process(rows: list):
    self_path = pathlib.Path(__file__)
    output_path = self_path.parent.parent / 'dist/devices.js'

    with open(output_path, 'w') as f:
        f.write('let devices = [\n')

        for row in rows:
            _add_device(f, row)

        f.write('];\n')


def _main():
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} file.xlsx')
        sys.exit(1)

    path = sys.argv[1]
    rows = _load_cache(path) or _load_excel(path)
    _process(rows)

    sys.exit(0)


if __name__ == '__main__':
    _main()
