import urwid

class AlwaysFocusedEdit(urwid.Edit):
    """
    This Edit widget is convinced that it is always in focus. This is so that
    it will respond to input events even if it isn't.'
    """
    def render(self, size, focus=False):
        return super(AlwaysFocusedEdit, self).render(size, focus=True)

