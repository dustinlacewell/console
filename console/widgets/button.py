import urwid


class CleanButton(urwid.Button):
    button_left =  button_right = urwid.Text('')

    def __init__(self, label, on_press=None, user_data=None):
        """
        :param label: markup for button label
        :param on_press: shorthand for connect_signal()
                         function call for a single callback
        :param user_data: user_data for on_press

        Signals supported: ``'click'``

        Register signal handler with::

          urwid.connect_signal(button, 'click', callback, user_data)

        where callback is callback(button [,user_data])
        Unregister signal handlers with::

          urwid.disconnect_signal(button, 'click', callback, user_data)

        >>> Button(u"Ok")
        <Button selectable flow widget 'Ok'>
        >>> b = Button("Cancel")
        >>> b.render((15,), focus=True).text # ... = b in Python 3
        [...'< Cancel      >']
        """
        self._label = urwid.Text("")
        cols = urwid.Columns([
            self._label],
            dividechars=1)
        super(urwid.Button, self).__init__(cols)

        # The old way of listening for a change was to pass the callback
        # in to the constructor.  Just convert it to the new way:
        if on_press:
            urwid.connect_signal(self, 'click', on_press, user_data)

        self.set_label(label)


