#!/usr/bin/env python3

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
import sys

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


def _process(rows: list):
    print(len(rows))


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
