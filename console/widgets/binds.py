import urwid


class BindWidget(urwid.WidgetWrap):

    def __init__(self, widget, binds):
        self.binds = binds
        urwid.WidgetWrap.__init__(self, widget)

    def keypress(self, size, key):
        """
        Translate keypress events into Console events.
        """
        event = self.binds.get(key, key)
        return super(BindWidget, self).keypress(size, event)
