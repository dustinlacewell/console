import urwid

from console.app import app
from console.modes import modemap


class Tab(urwid.AttrMap):
    """
    Baseclass for tabs in a TabGroup.
    """

    label = "???"
    mode = {}
    content = None

    def __init__(self):
        modemap.register_mode(self.label, self.mode)
        text_widget = urwid.Text(self.label, align='center')
        urwid.AttrMap.__init__(self, text_widget, None)
        self.content = self.get_content()

    def on_focus(self):
        modemap.mode = self.label
        self.set_attr_map({None: 'reversed'})

    def on_blur(self):
        self.set_attr_map({None: None})

    def get_content(self):
        return urwid.SolidFill("/")


class TabGroup(urwid.Columns):
    def __init__(self, tabs):
        for tab in tabs:
            if not isinstance(tab, Tab):
                raise TypeError('All tabs must be Tab instances')
        super(TabGroup, self).__init__(tabs)
        self.focus.on_focus()

    @property
    def active_tab(self):
        return self.focus.content

    def next_tab(self):
        old_focus = self.focus
        self.focus_position = (self.focus_position + 1) % len(self.contents)
        if self.focus != old_focus:
            self.focus.on_focus()
            old_focus.on_blur()
        return self.active_tab

    def prev_tab(self):
        old_focus = self.focus
        self.focus_position = (self.focus_position - 1) % len(self.contents)
        if self.focus != old_focus:
            self.focus.on_focus()
            old_focus.on_blur()
        return self.active_tab


class TabFrame(urwid.Frame):
    def __init__(self, tabs):
        self._tabs = TabGroup(tabs)
        self._header = self.make_header(self._tabs)
        self._help_dialog = None
        urwid.Frame.__init__(self, urwid.LineBox(self.active_tab), self._header)

    def make_header(self, tabs):
        return tabs

    @property
    def active_tab(self):
        return self._tabs.active_tab

    def next_tab(self):
        self.body = urwid.LineBox(self._tabs.next_tab())

    def prev_tab(self):
        self.body = urwid.LineBox(self._tabs.prev_tab())

    def handle_event(self, event):
        if event == 'quit':
            app.client.close()
            raise urwid.ExitMainLoop
        elif event == 'next-tab':
            self.next_tab()
        elif event == 'prev-tab':
            self.prev_tab()
        elif event == 'help':
            help_dialog = self.active_tab.get_help_dialog()
            self.active_tab.show_dialog(help_dialog)
        else:
            return event

    def keypress(self, size, key):
        event = modemap.event_for(key)
        if self.handle_event(event):
            return self.active_tab.keypress(size, event)
        return super(TabFrame, self).keypress(size, key)
