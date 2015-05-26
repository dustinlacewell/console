from .app import app

class Highlighter(object):
    def __init__(self, default_attr='highlight', default_focus='highlight_focus'):
        self.highlights = {}
        self.default_attr = default_attr
        self.default_focus = default_focus

    def apply(self, row, attr_style=None, focus_style=None):
        attr_style = attr_style or self.default_attr
        focus_style = focus_style or self.default_focus

        self.highlights[row] = [row, (row._attr_map, row._focus_map), (attr_style, focus_style)]

        row.set_attr_map({None: attr_style})
        row.set_focus_map({None: focus_style or attr_style})
        app.draw_screen()

    def remove(self, row):
        if row in self.highlights:
            row, original_style, applied_style = self.highlights.pop(row)
            attr_map, focus_map = original_style
            row.set_attr_map(attr_map)
            row.set_focus_map(focus_map)
            app.draw_screen()

highlighter = Highlighter()
