# SQL Dump File Navigator - A Simple SQL Dump Parser and Navigator
# Copyright (C) 2024 Kirk Bowe.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import re
import sys
import os
import curses
from curses import wrapper
import argparse

class SQLDumpParser:
    def __init__(self, filepath, verbose=False):
        self.filepath = filepath
        self.tables = {}  # Dictionary to hold table data
        self.verbose = verbose

    def parse(self):
        """
        Parses the SQL dump file to extract table schemas and data from CREATE TABLE and INSERT statements.
        """
        # Regex patterns
        create_table_regex = re.compile(
            r"CREATE TABLE\s+`?(\w+)`?\s*\((.*?)\)\s*ENGINE=",
            re.IGNORECASE | re.DOTALL
        )
        insert_into_regex = re.compile(
            r"INSERT INTO\s+`?(\w+)`?\s*(?:\(([^)]+)\))?\s+VALUES\s+(.+?);",
            re.IGNORECASE | re.DOTALL
        )

        try:
            with open(self.filepath, 'r', encoding='utf-8') as file:
                content = file.read()
        except FileNotFoundError:
            print(f"Error: File '{self.filepath}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)

        # Parse CREATE TABLE statements to get column names
        for match in create_table_regex.finditer(content):
            table_name = match.group(1)
            columns_def = match.group(2)
            columns = self._extract_columns(columns_def)
            if columns:
                self.tables[table_name] = {
                    'columns': columns,
                    'rows': []
                }
                if self.verbose:
                    print(f"Found table: {table_name} with columns: {columns}")
            else:
                if self.verbose:
                    print(f"Warning: No columns found for table '{table_name}'.")

        # Parse INSERT INTO statements
        for match in insert_into_regex.finditer(content):
            table_name = match.group(1)
            columns_str = match.group(2)
            values_str = match.group(3)

            if table_name not in self.tables:
                if self.verbose:
                    print(f"Warning: INSERT statement for unknown table '{table_name}'. Skipping.")
                continue

            # Determine columns
            if columns_str:
                columns = [col.strip(" `") for col in columns_str.split(",")]
            else:
                columns = self.tables[table_name]['columns']

            # Validate columns length with the table's columns if columns are specified
            if columns_str and len(columns) != len(self.tables[table_name]['columns']):
                if self.verbose:
                    print(f"Warning: Column count mismatch in INSERT INTO '{table_name}'. Expected {len(self.tables[table_name]['columns'])}, got {len(columns)}. Skipping these inserts.")
                continue

            # Split and parse values
            values = self._split_values(values_str)
            for val in values:
                parsed_row = self._parse_values(val)
                if parsed_row:
                    # If columns are specified in INSERT, map them accordingly
                    if columns_str:
                        row = {col: val for col, val in zip(columns, parsed_row)}
                        # Reorder according to table's column order
                        ordered_row = [row.get(col, None) for col in self.tables[table_name]['columns']]
                        self.tables[table_name]['rows'].append(ordered_row)
                    else:
                        self.tables[table_name]['rows'].append(parsed_row)
            if self.verbose:
                print(f"Inserted {len(values)} rows into table '{table_name}'.")

        if self.verbose:
            print(f"Parsing completed. Total tables parsed: {len(self.tables)}.")

    def _extract_columns(self, columns_def):
        """
        Extracts column names from the columns definition part of CREATE TABLE statement.
        """
        columns = []
        # Split the columns_def by commas, but ignore commas inside parentheses (e.g., enum types)
        column_lines = re.split(r",\s*(?![^()]*\))", columns_def)
        for line in column_lines:
            line = line.strip()
            # Match column definitions (exclude PRIMARY KEY, KEY, etc.)
            col_match = re.match(r"`?(\w+)`?\s+[^,]*", line)
            if col_match and not line.upper().startswith(('PRIMARY KEY', 'KEY', 'UNIQUE KEY', 'CONSTRAINT')):
                column_name = col_match.group(1)
                columns.append(column_name)
        return columns

    def _split_values(self, values_str):
        """
        Splits the VALUES string into individual tuples.
        Handles commas within strings and parentheses correctly.
        """
        values = []
        current = ''
        depth = 0
        in_string = False
        escape = False

        for char in values_str:
            if char == "'" and not escape:
                in_string = not in_string
            if char == "\\" and in_string:
                escape = not escape
            else:
                escape = False

            if char == '(' and not in_string:
                depth += 1
            elif char == ')' and not in_string:
                depth -= 1

            if char == ',' and depth == 0 and not in_string:
                if current.strip():
                    values.append(current.strip())
                    current = ''
                continue
            current += char

        if current.strip():
            values.append(current.strip())
        return values

    def _parse_values(self, val_str):
        """
        Parses a single VALUES tuple into a list of values.
        Handles SQL escaping and NULLs.
        """
        # Remove the surrounding parentheses
        val_str = val_str.strip('()')

        # Split by commas not within quotes
        pattern = re.compile(r"""
            '(?:\\'|[^'])*' |  # Single quoted strings, handling escaped quotes
            NULL |            # NULL
            [^,]+             # Other values
        """, re.VERBOSE | re.IGNORECASE)

        raw_values = pattern.findall(val_str)
        values = []
        for raw in raw_values:
            raw = raw.strip()
            if not raw:
                continue
            if raw.upper() == 'NULL':
                values.append(None)
            elif raw.startswith("'") and raw.endswith("'"):
                # Remove surrounding quotes and handle escaped quotes
                val = raw[1:-1].replace("\\'", "'").replace("\\\\", "\\")
                values.append(val)
            else:
                # Try to convert to int or float
                if re.match(r'^-?\d+$', raw):
                    try:
                        values.append(int(raw))
                    except ValueError:
                        values.append(raw)
                elif re.match(r'^-?\d+\.\d*$', raw):
                    try:
                        values.append(float(raw))
                    except ValueError:
                        values.append(raw)
                else:
                    values.append(raw)
        return values

class SpreadsheetNavigator:
    def __init__(self, tables):
        self.tables = tables
        self.current_table = None
        self.page_size = 20  # Number of rows per page
        self.current_page = 0
        self.col_page_size = 5  # Number of columns per column page
        self.current_col_page = 0
        self.table_page_size = 20  # Number of tables per table list page
        self.current_table_page = 0
        self.all_rows = []  # To store all rows for searching
        self.filtered_rows = []  # To store filtered rows after search
        self.search_active = False  # Flag to indicate if search filter is active

    def list_tables_curses(self, stdscr, table_page):
        """
        Lists tables for the current table list page using curses.
        """
        stdscr.addstr(0, 0, "Available Tables:")
        total_tables = len(self.tables)
        total_table_pages = (total_tables // self.table_page_size) + (1 if total_tables % self.table_page_size else 0)

        start_idx = table_page * self.table_page_size
        end_idx = start_idx + self.table_page_size
        tables_on_page = list(self.tables.keys())[start_idx:end_idx]

        for idx, table in enumerate(tables_on_page, start=1):
            table_num = start_idx + idx
            try:
                stdscr.addstr(idx, 2, f"{idx}. {table}")
            except curses.error:
                # Handle cases where the terminal window is too small
                pass

        # Display table page information
        table_info = f"Table Pages: {table_page + 1}/{total_table_pages}"
        try:
            stdscr.addstr(curses.LINES - 2, 0, table_info)
        except curses.error:
            pass

        # Display navigation instructions
        nav_instructions = "Commands: [n] Next Tables | [p] Previous Tables | [s] Search | [q] Quit"
        try:
            stdscr.addstr(curses.LINES - 1, 0, nav_instructions)
        except curses.error:
            pass

    def select_table_curses(self, stdscr):
        """
        Prompts the user to select a table using curses with table list pagination and search.
        """
        while True:
            stdscr.clear()
            self.list_tables_curses(stdscr, self.current_table_page)
            stdscr.refresh()
            curses.echo()
            # Prompt user for table number or navigation command
            prompt = f"Enter a command or a table number to view (Page {self.current_table_page + 1}): "
            try:
                stdscr.addstr(curses.LINES - 3, 0, prompt)
            except curses.error:
                pass
            input_str = ""
            try:
                input_str = stdscr.getstr(curses.LINES - 3, len(prompt), 30).decode().strip()
            except:
                pass
            curses.noecho()

            if input_str.lower() == 'q':
                sys.exit(0)
            elif input_str.lower() == 'n':
                # Next table list page
                total_tables = len(self.tables)
                total_table_pages = (total_tables // self.table_page_size) + (1 if total_tables % self.table_page_size else 0)
                if (self.current_table_page + 1) < total_table_pages:
                    self.current_table_page += 1
                else:
                    self.show_message(stdscr, "You are on the last table page.")
            elif input_str.lower() == 'p':
                # Previous table list page
                if self.current_table_page > 0:
                    self.current_table_page -= 1
                else:
                    self.show_message(stdscr, "You are on the first table page.")
            elif input_str.lower() == 's':
                # Enter search mode
                self.search_table_curses(stdscr)
                # After search, if a table is selected, break out to display data
                if self.current_table is not None:
                    # Initialize row search variables
                    self.all_rows = self.current_table['rows']
                    self.filtered_rows = self.all_rows.copy()
                    self.search_active = False
                    break
            elif input_str.isdigit():
                selection = int(input_str)
                # Calculate the actual table index
                start_idx = self.current_table_page * self.table_page_size
                end_idx = start_idx + self.table_page_size
                tables_on_page = list(self.tables.keys())[start_idx:end_idx]
                if 1 <= selection <= len(tables_on_page):
                    table_name = tables_on_page[selection - 1]
                    self.current_table = self.tables[table_name]
                    self.current_page = 0
                    self.current_col_page = 0
                    self.current_table_page = 0  # Reset table list page after selection
                    self.all_rows = self.current_table['rows']
                    self.filtered_rows = self.all_rows.copy()
                    self.search_active = False
                    self.show_message(stdscr, f"Selected table: {table_name}. Press any key to continue.")
                    stdscr.getch()
                    break
                else:
                    self.show_message(stdscr, "Invalid table number. Try again.")
            else:
                self.show_message(stdscr, "Invalid input. Use table number, 'n'/'p' for navigation, 's' to search.")

    def search_table_curses(self, stdscr):
        """
        Implements an autocomplete search for tables using curses.
        """
        search_query = ""
        filtered_tables = list(self.tables.keys())
        max_display = curses.LINES - 5  # Reserve lines for prompt and messages

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "Search Tables (Type and press Enter to select, ESC to cancel):")
            stdscr.addstr(1, 0, f"Search: {search_query}")
            # Filter tables based on search_query
            if search_query:
                filtered_tables = [table for table in self.tables if search_query.lower() in table.lower()]
            else:
                filtered_tables = list(self.tables.keys())

            # Display filtered tables
            for idx, table in enumerate(filtered_tables[:max_display], start=2):
                try:
                    stdscr.addstr(idx, 2, f"{idx - 1}. {table}")
                except curses.error:
                    pass

            # Instructions
            try:
                stdscr.addstr(curses.LINES - 1, 0, "Type to search, Enter to select, ESC to cancel.")
            except curses.error:
                pass

            stdscr.refresh()

            # Capture user input
            key = stdscr.getch()

            if key in [27]:  # ESC key to cancel search
                break
            elif key in [curses.KEY_BACKSPACE, 127, 8]:
                search_query = search_query[:-1]
            elif key in [curses.KEY_ENTER, 10, 13]:
                if filtered_tables:
                    # Select the first match or prompt if multiple
                    if len(filtered_tables) == 1:
                        table_name = filtered_tables[0]
                        self.current_table = self.tables[table_name]
                        self.current_page = 0
                        self.current_col_page = 0
                        self.current_table_page = 0  # Reset table list page after selection
                        self.all_rows = self.current_table['rows']
                        self.filtered_rows = self.all_rows.copy()
                        self.search_active = False
                        self.show_message(stdscr, f"Selected table: {table_name}. Press any key to continue.")
                        stdscr.getch()
                        return
                    else:
                        # If multiple matches, allow user to select
                        self.select_from_filtered_curses(stdscr, filtered_tables)
                        return
                else:
                    self.show_message(stdscr, "No tables match your search.")
            elif 32 <= key <= 126:  # Printable characters
                search_query += chr(key)
            # Ignore other keys

    def select_from_filtered_curses(self, stdscr, filtered_tables):
        """
        Allows the user to select from multiple filtered tables.
        """
        selected = 0
        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "Select a Table from the Search Results:")
            for idx, table in enumerate(filtered_tables, start=1):
                try:
                    if idx - 1 == selected:
                        # Highlight the selected table
                        stdscr.attron(curses.A_REVERSE)
                        stdscr.addstr(idx, 2, f"{idx}. {table}")
                        stdscr.attroff(curses.A_REVERSE)
                    else:
                        stdscr.addstr(idx, 2, f"{idx}. {table}")
                except curses.error:
                    pass
            # Instructions
            try:
                stdscr.addstr(curses.LINES - 1, 0, "Use Up/Down arrows to navigate, Enter to select, ESC to cancel.")
            except curses.error:
                pass

            stdscr.refresh()

            key = stdscr.getch()

            if key in [27]:  # ESC key to cancel
                break
            elif key in [curses.KEY_UP]:
                if selected > 0:
                    selected -= 1
            elif key in [curses.KEY_DOWN]:
                if selected < len(filtered_tables) - 1:
                    selected += 1
            elif key in [curses.KEY_ENTER, 10, 13]:
                table_name = filtered_tables[selected]
                self.current_table = self.tables[table_name]
                self.current_page = 0
                self.current_col_page = 0
                self.current_table_page = 0  # Reset table list page after selection
                self.all_rows = self.current_table['rows']
                self.filtered_rows = self.all_rows.copy()
                self.search_active = False
                self.show_message(stdscr, f"Selected table: {table_name}. Press any key to continue.")
                stdscr.getch()
                break

    def display_page_curses(self, stdscr):
        """
        Displays the current page of the selected table within the curses window.
        Handles column pagination and row search filtering.
        """
        stdscr.clear()
        if self.current_table is None:
            return

        # Determine which rows to display
        total_rows = len(self.filtered_rows)
        total_pages = (total_rows // self.page_size) + (1 if total_rows % self.page_size else 0)
        start_row = self.current_page * self.page_size
        end_row = start_row + self.page_size
        page_data = self.filtered_rows[start_row:end_row]
        columns = self.current_table['columns']

        # Calculate total column pages
        total_col_pages = (len(columns) // self.col_page_size) + (1 if len(columns) % self.col_page_size else 0)

        # Determine which columns to display based on current_col_page
        start_col = self.current_col_page * self.col_page_size
        end_col = start_col + self.col_page_size
        display_columns = columns[start_col:end_col]
        display_data = [row[start_col:end_col] for row in page_data]

        # Calculate column widths
        col_widths = {}
        for idx, col in enumerate(display_columns):
            max_len = len(col)
            for row in display_data:
                if idx >= len(row):
                    continue
                val = row[idx]
                val_str = 'NULL' if val is None else str(val)
                if len(val_str) > max_len:
                    max_len = min(len(val_str), 30)  # Limit to 30 for readability
            col_widths[col] = max_len + 2  # Add padding

        # Prepare header
        header = ""
        for col in display_columns:
            header += f"{col.ljust(col_widths[col])}| "
        header = header.rstrip("| ")

        # Prepare separator
        separator = ""
        for col in display_columns:
            separator += f"{'-' * col_widths[col]}+ "
        separator = separator.rstrip("+ ")

        # Display header and separator
        try:
            stdscr.addstr(0, 0, header)
            stdscr.addstr(1, 0, separator)
        except curses.error:
            pass  # Handle cases where the terminal window is too small

        # Display rows
        for i, row in enumerate(display_data, start=2):
            row_str = ""
            for idx, val in enumerate(row):
                if idx >= len(display_columns):
                    continue
                val_str = 'NULL' if val is None else str(val)
                # Highlight search matches if search is active
                if self.search_active:
                    # Find all occurrences of the search query in the row
                    matches = self.search_query.lower().split()
                    for match in matches:
                        if match and match in val_str.lower():
                            # Find start indices of matches
                            start = 0
                            while True:
                                start = val_str.lower().find(match, start)
                                if start == -1:
                                    break
                                # Highlight the match
                                try:
                                    stdscr.addstr(i, 0, row_str)  # Display accumulated string
                                    stdscr.attron(curses.A_STANDOUT)
                                    stdscr.addstr(i, len(row_str), val_str[start:start+len(match)])
                                    stdscr.attroff(curses.A_STANDOUT)
                                except curses.error:
                                    pass
                                start += len(match)
                if len(val_str) > 30:
                    val_str = val_str[:27] + "..."
                row_str += f"{val_str.ljust(col_widths[display_columns[idx]])}| "
            row_str = row_str.rstrip("| ")
            try:
                stdscr.addstr(i, 0, row_str)
            except curses.error:
                # Handle cases where the terminal window is too small
                pass

        # Display page information at the bottom
        page_info = f"Rows: {start_row + 1}-{min(end_row, total_rows)} of {total_rows} | Pages: {self.current_page + 1}/{total_pages}"
        col_info = f"Columns: {start_col + 1}-{min(end_col, len(columns))} of {len(columns)} | Column Pages: {self.current_col_page + 1}/{total_col_pages}"
        search_info = f"Search: {'Active' if self.search_active else 'Inactive'}"
        try:
            stdscr.addstr(curses.LINES - 4, 0, page_info)
            stdscr.addstr(curses.LINES - 3, 0, col_info)
            stdscr.addstr(curses.LINES - 2, 0, search_info)
            stdscr.addstr(curses.LINES - 1, 0, "Commands: [n] Next Page | [p] Previous Page | [l] Left Columns | [r] Right Columns | [s] Select Another Table | [/ ] Search Rows | [c] Clear Search | [q] Quit")
        except curses.error:
            pass  # Handle cases where the terminal window is too small

    def navigate_with_curses(self, stdscr):
        """
        Main loop to navigate through the spreadsheet using curses.
        """
        curses.curs_set(0)  # Hide cursor
        while True:
            self.select_table_curses(stdscr)
            while True:
                self.display_page_curses(stdscr)
                stdscr.refresh()
                key = stdscr.getch()

                if key in [ord('q'), ord('Q')]:
                    sys.exit(0)
                elif key in [ord('n'), ord('N')]:
                    # Next row page
                    if (self.current_page + 1) * self.page_size < len(self.filtered_rows):
                        self.current_page += 1
                elif key in [ord('p'), ord('P')]:
                    # Previous row page
                    if self.current_page > 0:
                        self.current_page -= 1
                elif key in [ord('r'), curses.KEY_RIGHT]:
                    # Right column page
                    total_col_pages = (len(self.current_table['columns']) // self.col_page_size) + (1 if len(self.current_table['columns']) % self.col_page_size else 0)
                    if (self.current_col_page + 1) < total_col_pages:
                        self.current_col_page += 1
                elif key in [ord('l'), curses.KEY_LEFT]:
                    # Left column page
                    if self.current_col_page > 0:
                        self.current_col_page -= 1
                elif key in [ord('s'), ord('S')]:
                    # Select another table
                    self.current_table = None
                    self.current_table_page = 0  # Reset table list page
                    break
                elif key in [ord('/'), ord('?')]:
                    # Initiate row search
                    self.row_search_curses(stdscr)
                elif key in [ord('c'), ord('C')]:
                    # Clear row search
                    if self.search_active:
                        self.clear_row_search()
                        self.show_message(stdscr, "Search filter cleared. Displaying all rows.")
                        stdscr.getch()
                else:
                    pass  # Ignore other keys

    def row_search_curses(self, stdscr):
        """
        Prompts the user to enter a search query to filter table rows.
        """
        curses.echo()
        prompt = "Enter search query (searches all columns): "
        try:
            stdscr.addstr(curses.LINES - 5, 0, prompt)
        except curses.error:
            pass
        search_query = ""
        try:
            search_query = stdscr.getstr(curses.LINES - 5, len(prompt), 100).decode().strip()
        except:
            pass
        curses.noecho()

        if search_query:
            self.apply_row_search(search_query)
            if not self.filtered_rows:
                self.show_message(stdscr, "No rows match the search query.")
                stdscr.getch()
        else:
            self.show_message(stdscr, "Empty search query. No changes made.")
            stdscr.getch()

    def select_table(self):
        """
        Prompts the user to select a table.
        """
        while True:
            print("\nAvailable Tables:")
            total_tables = len(self.tables)
            total_table_pages = (total_tables // self.table_page_size) + (1 if total_tables % self.table_page_size else 0)
            start_idx = self.current_table_page * self.table_page_size
            end_idx = start_idx + self.table_page_size
            tables_on_page = list(self.tables.keys())[start_idx:end_idx]
            for idx, table in enumerate(tables_on_page, start=1):
                print(f"{idx}. {table}")
            print(f"Table Pages: {self.current_table_page + 1}/{total_table_pages}")
            print("Commands: [n] Next Tables | [p] Previous Tables | [s] Search | [q] Quit")
            selection = input("Enter a command or a table number to view: ").strip().lower()
            if selection == 'q':
                sys.exit(0)
            elif selection == 'n':
                if (self.current_table_page + 1) < total_table_pages:
                    self.current_table_page += 1
                else:
                    print("You are on the last table page.")
            elif selection == 'p':
                if self.current_table_page > 0:
                    self.current_table_page -= 1
                else:
                    print("You are on the first table page.")
            elif selection == 's':
                self.search_table()
                if self.current_table is not None:
                    break
            elif selection.isdigit():
                table_num = int(selection)
                if 1 <= table_num <= len(tables_on_page):
                    table_name = tables_on_page[table_num - 1]
                    self.current_table = self.tables[table_name]
                    self.current_page = 0
                    self.current_col_page = 0
                    self.current_table_page = 0
                    self.all_rows = self.current_table['rows']
                    self.filtered_rows = self.all_rows.copy()
                    self.search_active = False
                    break
                else:
                    print("Invalid table number. Please try again.")

    def display_page(self):
        """
        Displays the current page of the selected table.
        """
        if self.current_table is None:
            return

        total_rows = len(self.filtered_rows)
        total_pages = (total_rows // self.page_size) + (1 if total_rows % self.page_size else 0)
        start_row = self.current_page * self.page_size
        end_row = start_row + self.page_size
        page_data = self.filtered_rows[start_row:end_row]
        columns = self.current_table['columns']

        total_col_pages = (len(columns) // self.col_page_size) + (1 if len(columns) % self.col_page_size else 0)
        start_col = self.current_col_page * self.col_page_size
        end_col = start_col + self.col_page_size
        display_columns = columns[start_col:end_col]
        display_data = [row[start_col:end_col] for row in page_data]

        # Calculate column widths
        col_widths = {}
        for idx, col in enumerate(display_columns):
            max_len = len(col)
            for row in display_data:
                if idx >= len(row):
                    continue
                val = row[idx]
                val_str = 'NULL' if val is None else str(val)
                if len(val_str) > max_len:
                    max_len = min(len(val_str), 30)
            col_widths[col] = max_len + 2

        # Prepare header
        header = ""
        for col in display_columns:
            header += f"{col.ljust(col_widths[col])}| "
        header = header.rstrip("| ")

        # Prepare separator
        separator = ""
        for col in display_columns:
            separator += f"{'-' * col_widths[col]}+ "
        separator = separator.rstrip("+ ")

        # Display header and separator
        print(header)
        print(separator)

        # Display rows
        for row in display_data:
            row_str = ""
            for idx, val in enumerate(row):
                if idx >= len(display_columns):
                    continue
                val_str = 'NULL' if val is None else str(val)
                if len(val_str) > 30:
                    val_str = val_str[:27] + "..."
                row_str += f"{val_str.ljust(col_widths[display_columns[idx]])}| "
            print(row_str.rstrip("| "))
        print(separator)

        # Display page information
        print(f"Rows: {start_row + 1}-{min(end_row, total_rows)} of {total_rows} | Pages: {self.current_page + 1}/{total_pages}")
        print(f"Columns: {start_col + 1}-{min(end_col, len(columns))} of {len(columns)} | Column Pages: {self.current_col_page + 1}/{total_col_pages}")
        print(f"Search: {'Active' if self.search_active else 'Inactive'}")

    def apply_row_search(self, query):
        """
        Filters rows based on the search query.
        """
        self.filtered_rows = []
        query_lower = query.lower()
        for row in self.all_rows:
            for cell in row:
                if cell is not None and query_lower in str(cell).lower():
                    self.filtered_rows.append(row)
                    break  # Move to next row after first match
        self.search_active = True
        self.search_query = query

    def clear_row_search(self):
        """
        Clears the current row search filter.
        """
        self.filtered_rows = self.all_rows.copy()
        self.search_active = False
        self.search_query = ""

    def show_message(self, stdscr, message):
        """
        Displays a temporary message to the user.
        """
        try:
            stdscr.addstr(curses.LINES - 1, 0, message)
            stdscr.clrtoeol()
            stdscr.refresh()
        except curses.error:
            pass  # Handle cases where the terminal window is too small

    def navigate(self):
        """
        Fallback non-curses navigation.
        """
        while True:
            self.select_table()
            while True:
                self.display_page()
                print("\nCommands: [n] Next Page | [p] Previous Page | [l] Left Columns | [r] Right Columns | [s] Select Another Table | [/ ] Search Rows | [c] Clear Search | [q] Quit")
                cmd = input("Enter command: ").strip().lower()
                if cmd == 'n':
                    if (self.current_page + 1) * self.page_size >= len(self.filtered_rows):
                        print("You are on the last page.")
                    else:
                        self.current_page += 1
                elif cmd == 'p':
                    if self.current_page == 0:
                        print("You are on the first page.")
                    else:
                        self.current_page -= 1
                elif cmd == 'l':
                    if self.current_col_page > 0:
                        self.current_col_page -= 1
                    else:
                        print("You are on the first column page.")
                elif cmd == 'r':
                    total_col_pages = (len(self.current_table['columns']) // self.col_page_size) + (1 if len(self.current_table['columns']) % self.col_page_size else 0)
                    if (self.current_col_page + 1) < total_col_pages:
                        self.current_col_page += 1
                    else:
                        print("You are on the last column page.")
                elif cmd == 's':
                    self.current_table = None
                    break
                elif cmd == '/':
                    # Initiate row search
                    search_query = input("Enter search query (searches all columns): ").strip()
                    if search_query:
                        self.apply_row_search(search_query)
                        if not self.filtered_rows:
                            print("No rows match the search query.")
                    else:
                        print("Empty search query. No changes made.")
                elif cmd == 'c':
                    # Clear row search
                    if self.search_active:
                        self.clear_row_search()
                        print("Search filter cleared. Displaying all rows.")
                elif cmd == 'q':
                    sys.exit(0)
                else:
                    print("Invalid command. Please try again.")

def main_curses(stdscr, navigator):
    """
    Initializes curses and starts the navigation.
    """
    navigator.navigate_with_curses(stdscr)

def main():
    parser = argparse.ArgumentParser(description="Parse SQL dump files.")
    parser.add_argument("filepath", help="Path to the SQL dump file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--nocurses", action="store_true", help="Disable curses-based navigation")
    args = parser.parse_args()

    if not os.path.isfile(args.filepath):
        print(f"Error: File '{args.filepath}' does not exist.")
        sys.exit(1)

    # Print brief GPL notice
    print (f"SQL Dump File Navigator Copyright (C)2024 Kirk Bowe.")
    print (f"This program comes with ABSOLUTELY NO WARRANTY; for details see the included LICENCE file.\n")    

    sql_parser = SQLDumpParser(args.filepath, verbose=args.verbose)
    sql_parser.parse()

    if not sql_parser.tables:
        print("No tables found in the SQL dump.")
        sys.exit(0)

    navigator = SpreadsheetNavigator(sql_parser.tables)

    if args.nocurses:
        navigator.navigate()
    else:
        wrapper(main_curses, navigator)

if __name__ == "__main__":
    main()
