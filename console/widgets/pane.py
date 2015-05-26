import urwid

from console.app import app
from console.widgets.help import HelpDialog

class Pane(urwid.WidgetPlaceholder):
    """
    A widget which allows for easy display of dialogs.

    """

    def __init__(self, widget=urwid.SolidFill(' ')):
        urwid.WidgetPlaceholder.__init__(self, widget)
        self.widget = widget
        self.dialog = None

    def show_dialog(self, dialog):
        if not self.dialog:
            self.dialog = dialog
            self.original_widget = urwid.Overlay(
                urwid.LineBox(dialog),
                self.original_widget,
                align=getattr(dialog, 'align', 'center'),
                width=getattr(dialog, 'width', ('relative', 99)),
                valign=getattr(dialog, 'valign', 'middle'),
                height=getattr(dialog, 'height', 'pack'),
            )
            app.draw_screen()

    def close_dialog(self):
        if self.dialog:
            self.original_widget = self.widget
            self.dialog = None
            app.draw_screen()

    def keypress(self, size, event):
        if not self.handle_event(event):
            return self.original_widget.keypress(size, event)
        return super(Pane, self).keypress(size, event)

    def handle_event(self, event):
        if event == 'close-dialog':
            self.close_dialog()
        else:
            return event

    def get_help_dialog(self):
        return HelpDialog()

