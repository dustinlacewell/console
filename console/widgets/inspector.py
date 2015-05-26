import urwid

from console.app import app
from console.widgets.dialogs import PopupPile
from console.widgets.listbox import FancyListBox


class Inspector(PopupPile):
    title = "Inspection"

    def __init__(self, data):
        super(Inspector, self).__init__([
            urwid.BoxAdapter(
                FancyListBox(self.get_contents(data)),
                int(app.screen.get_cols_rows()[1] * 0.8)
            )
        ])

    def get_string_item(self, key, val, label_width):
        return urwid.Columns([
            (label_width, urwid.Padding(
                urwid.Text(key, align='right'),
                align='center', width=('relative', 80),
            )),
            urwid.Padding(
                urwid.Text(unicode(val), align='left'),
                align='center', width=('relative', 100),
            ),
        ])

    def get_list_item(self, key, vals, label_width):
        items = []
        for item in vals:
            if item:
                items.append(self.handle_item('', item, label_width))

        return urwid.Columns([
            (label_width, urwid.Padding(
                urwid.Text(key, align='right'),
                align='center', width=('relative', 80),
            )),
            urwid.Pile([urwid.Text('')] + items),
        ])

    def get_dict_item(self, name, data, label_width):
        longest = 1
        if data:
            longest = max(len(key) for key in data) + 4
        items = []
        for key, val in sorted(data.items()):
            if val:
                items.append(self.handle_item(key, val, longest))
        return urwid.Pile(items)

    def handle_item(self, key, val, longest):
        if val == '':
            val = "None"
        if val is None:
            val = "None"

        if val is "None":
            return self.get_string_item(key, 'None', longest)
        if (isinstance(val, unicode) or isinstance(val, str)) or isinstance(val, float) or isinstance(val, int):
            try:
                return self.get_string_item(key, val, longest)
            except UnicodeEncodeError:
                import pdb; pdb.set_trace()
        if isinstance(val, list) or isinstance(val, tuple):
            return self.get_list_item(key, val, longest)
        if isinstance(val, dict) and val:
            return self.get_dict_item(key, val, longest)
        return urwid.Pile([])


    def get_contents(self, data):
        contents = []
        longest = 0
        if data:
            longest = max(len(k) for k in data)
        contents.append(self.get_dict_item('data', data, 20))

        return contents

