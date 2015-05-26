import urwid

from console.modes import default_global_mode, modemap

class HelpDialog(urwid.Pile):
    def __init__(self):
        items = []
        items += self.get_mode_help("Global Keys", default_global_mode)

        items.append(urwid.BoxAdapter(urwid.SolidFill(' '), 1))

        mode_title = "{} Keys".format(modemap._mode.capitalize())
        items += self.get_mode_help(mode_title, modemap.mode)
        urwid.Pile.__init__(self, items)


    def get_sorted_binds(self, mode):
        binds = []
        for key, bind in mode.items():
            if isinstance(bind, tuple):
                bind, help = bind
            else:
                help = ""
            binds.append((bind, key, help))
        return sorted(binds)

    def get_bind_rows(self, binds):
        rows = []
        for bind in binds:
            event, key, help = bind
            rows.append(urwid.Columns([
                ('weight', 1, urwid.Text(event)),
                ('weight', 1, urwid.Text(key)),
                ('weight', 4, urwid.Text(help)),
            ]))
        return rows

    def get_mode_title(self, label):
        return urwid.Columns([
            ('pack', urwid.Text(label)),
            (1, urwid.BoxAdapter(urwid.SolidFill(' '), 1)),
            ('weight', 1, urwid.BoxAdapter(urwid.SolidFill('-'), 1)),
        ])

    def get_mode_help(self, label, mode):
        items = [self.get_mode_title(label)]
        sorted_binds = self.get_sorted_binds(mode)
        bind_rows = self.get_bind_rows(sorted_binds)
        items += bind_rows
        return [urwid.Padding(i, left=2, right=2) for i in items]
