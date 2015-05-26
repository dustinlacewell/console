import urwid

from console.widgets.table import TableCell, TableRow, DeadTable
from console.widgets.listbox import FancyListBox


class PopupPile(urwid.Pile):
    width = ('relative', 80)
    height = 'pack'
    align = 'center'
    valign = 'middle'
    title = ''

    callback = lambda *args, **kwargs: None

    def set_callback(self, callback):
        self.callback = callback

    def on_submit(self):
        self.callback(None)

    def keypress(self, size, event):
        if event == 'close-dialog':
            self.callback(None)
        elif event == 'submit-dialog':
            self.on_submit()
        else:
            return super(PopupPile, self).keypress((size[0],),  event)



class MessageBox(PopupPile):
    def __init__(self, message, title='', text_align='left'):
        self.title = title
        super(MessageBox, self).__init__([
            urwid.Text(message, align=text_align)
        ])


class MessageListBox(PopupPile):
    def __init__(self, messages, title='', text_align='left', width=80):
        self.width = ('relative', width)
        self.title = title
        super(MessageListBox, self).__init__([
            urwid.BoxAdapter(
                FancyListBox([
                    urwid.Text(message, align=text_align)
                    for message in messages
                ]),
                min(len(messages) + 2, int(app.screen.get_cols_rows()[1] * .8))
            )
        ])

class Prompt(PopupPile):
    def __init__(self, callback, message='', title='', text_align='left', initial=''):
        if not (message or title):
            raise RuntimeError("Prompt must be initialized with either message or title.")
        self.callback = callback
        self.title=title
        self.edit = urwid.Edit(edit_text=initial)
        items = [self.edit]
        if message:
            items.insert(0, urwid.Text(message, align=text_align))
        super(Prompt, self).__init__(items)

    def on_submit(self):
        self.callback(self.edit.edit_text)

    def keypress(self, size, event):
        if event == 'submit-dialog':
            self.on_submit()
        else:
            return self.edit.keypress(size, event)

class TableDialog(PopupPile):
    def __init__(self, title, binds, headers=None):
        self.title = title
        super(TableDialog, self).__init__([
            self.generate_table(title, binds, headers),
        ])

    def generate_table(self, title, binds, headers):
        rows = []
        for row in binds:
            cells = []
            for idx, cell in enumerate(row):
                if headers:
                    cells.append(
                        TableCell(
                            cell,
                            weight=headers[idx].weight,
                            align=headers[idx].align,
                        )
                    )
                else:
                    cells.append(TableCell(cell))
            rows.append(TableRow(cells))

        table = DeadTable()
        if headers:
            table.set_header(
                urwid.Pile([
                    TableRow(headers),
                    urwid.BoxAdapter(
                        urwid.SolidFill('-'),
                        1,
                    )
                ])
            )
        table.set_rows(rows)

        return urwid.WidgetDisable(table)
