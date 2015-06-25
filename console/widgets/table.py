import urwid

from console.widgets.listbox import FancyListBox

class TableCell(urwid.Text):
    def __init__(self, text, weight=1, align='center'):
        super(TableCell, self).__init__(text, align=align)
        self.weight = weight


class TableRow(urwid.AttrMap):
    """
    Widget representing a row in a Table. It accepts a list of dictionaries which
    should contain the following keys:

      value: the value of the cell
     weight: the weight of the cell in sizing
      align: the alignment of the cell
    """

    def __init__(self, cells):
        super(TableRow, self).__init__(urwid.Columns([]), None, 'reversed')
        for cell in cells:
            self.append_cell(cell)

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key

    def append_cell(self, cell):
        options = self.original_widget.options(
            'weight', width_amount=cell.get('weight', 1),
        )
        cell = TableCell(cell['value'], align=cell.get('align', 'left'))
        self.original_widget.contents.append((cell, options))


class Table(urwid.ListBox):
    """
    A Widget providing something resembling a table. The table's schema should be
    a list of dictionaries. Each dictionary represents a column in the table and
    should have the following keys:

        name - the name of the column
       align - the alignment of the column (default: left)
      weight - the weight of the column for sizing (default: 1)

    Rows should be provided as dictionaries, each key corresponding to a column
    in the table's schema.
    """

    def __init__(self, schema, rows=[], header=False):
        self.header = None
        self.schema = schema
        self.walker = urwid.SimpleListWalker([])
        super(Table, self).__init__(self.walker)
        if header:
            header = self.create_header()
            self.set_header(header)
        if rows:
            self.set_rows(rows)

    def clear(self):
        if self.header:
            self.walker[1:] = []
        else:
            self.walker[:] = []

    def create_header(self):
        row = TableRow([])
        for column in self.schema:
            row.append_cell({
                'value': column['name'],
                'weight': column.get('weight', 1),
                'align': column.get('align', 'left'),
            })
        line_break = urwid.BoxAdapter(urwid.SolidFill('-'), 1)
        return urwid.Pile([row, line_break])

    def create_row(self, rowdef):
        row = TableRow([])
        for column in self.schema:
            column_name = column['name']
            row.append_cell({
                'value': rowdef.get(column_name, 'n/a'),
                'weight': column.get('weight', 1),
                'align': column.get('align', 'left'),
            })
        return row

    def unset_header(self):
        if self.header:
            self.walker.pop(0)
            self.header = None

    def set_header(self, header):
        self.unset_header()
        self.walker.insert(0, header)
        self.header = header

    def set_rows(self, rows):
        self.clear()
        for rowdef in rows:
            row = self.create_row(rowdef)
            self.append_row(row)
            self.fix_focus()
        app.draw_screen()

    def append_row(self, rowdef):
        row = self.create_row(rowdef)
        self.walker.append(row)
        return row

    def insert_row(self, index, rowdef):
        row = self.create_row(rowdef)
        self.walker.insert(index, row)
        return row

    def fix_focus(self):
        widget, pos = self.get_focus()
        if self.header and pos == 0 and len(self.walker) > 1:
            self.set_focus(1)

    def set_focus(self, pos):
        super(Table, self).set_focus(max(0, min(pos, len(self.walker) - 1)))

    def at_edge(self, direction):
        widget, pos = self.get_focus()
        x = max(0, min(pos + 1, len(self.walker) - 1))
        if x == 3 and not direction:
            return True
        if x == len(self.walker) - 1 and direction:
            return True
        else:
            return False

    def update_edges(self, edges):
        top = edges[0]
        bottom = edges[1]
        widget, pos = self.get_focus()
        x = max(0, min(pos + 1, len(self.walker) - 1))
        if x == 0 or x == len(self.walker) - 1:
            if x == 0:
                top = True
            if x == len(self.walker) - 1:
                bottom = True
        else:
            top = False
            bottom = False
        return [top, bottom]

    def next(self):
        widget, pos = self.get_focus()
        self.set_focus(pos + 1)

    def prev(self):
        widget, pos = self.get_focus()
        if self.header and len(self.walker) > 1:
            self.set_focus(max(pos - 1, 1))
        else:
            self.set_focus(pos - 1)

    def mark(self):
        widget, pos = self.get_focus()
        widget.set_attr_map({None: 'reversed'})

    def unmark(self):
        widget, pos = self.get_focus()
        widget.set_attr_map({None: None})

    def keypress(self, *args, **kwargs):
        key = super(Table, self).keypress(*args, **kwargs)
        return key


class DeadTable(urwid.Pile):
    def __init__(self, rows=[]):
        self.header = False
        super(DeadTable, self).__init__(rows)

    def set_header(self, row):
        if self.header:
            self.contents.pop(0)
        self.insert_row(0, row)
        self.header = True

    def set_rows(self, rows):
        if self.header:
            self.contents[1:] = [(item, ('pack', None)) for item in rows]
        else:
            self.contents[:] = [(item, ('pack', None)) for item in rows]

    def unset_header(self, row):
        if self.header:
            self.contents.pop(0)
            self.header = False

    def append_row(self, row):
        self.contents.append((row, ('pack', None)))

    def insert_row(self, index, row):
        self.contents.insert(index, (row, ('pack', None)))


class FancyTable(FancyListBox):
    def get_listbox(self, items):
        class _FancyListBox(Table):
            def keypress(_self, size, key):
                key = super(_FancyListBox, _self).keypress(size, key)
                self.update_corners(_self.ends_visible(size))
                return key

            def render(_self, size, focus=False):
                self.update_corners(_self.ends_visible(size))
                return super(_FancyListBox, _self).render(size, focus)
        return _FancyListBox(items)

    def set_rows(self, *args, **kwargs):
        self.listbox.set_rows(*args, **kwargs)

    def set_next(self, *args, **kwargs):
        self.listbox.set_next(*args, **kwargs)

    def set_prev(self, *args, **kwargs):
        self.listbox.set_prev(*args, **kwargs)

    def get_focus(self, *args, **kwargs):
        self.listbox.get_focus(*args, **kwargs)

    def set_header(self, *args, **kwargs):
        self.listbox.set_header(*args, **kwargs)

