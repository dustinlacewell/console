import urwid

default_global_mode = {
    'ctrl c': ('quit', 'quit the application'),
    '?': ('help', 'show this help dialog'),
    ' ': ('close-dialog', 'close the current dialog'),
    'enter': ('submit-dialog', 'submit the current dialog'),
    'tab': ('next-tab', 'switch to next tab'),
    'shift tab': ('prev-tab', 'switch to previous tab'),
}

class ModeMap(object):
    def __init__(self, global_mode):
        self.global_mode = global_mode
        self.major_modes = {}
        self._mode = None

    def register_mode(self, name, bindmap):
        self.major_modes[name] = bindmap

    @property
    def mode(self):
        return self.major_modes.get(self._mode)

    @mode.setter
    def mode(self, name):
        if name not in self.major_modes:
            raise KeyError("No `{}` mode has been registered".format(name))
        self._mode = name

    def event_for(self, key):
        if key in self.mode:
            event = self.mode[key]
            if isinstance(event, tuple):
                event, help = event
            return event
        elif key in self.global_mode:
            event = self.global_mode[key]
            if isinstance(event, tuple):
                event, help = event
            return event
        return key

    def bind_for(self, event):
        for key, val in self.mode.items():
            if isinstance(val, tuple):
                val, help = val
            if val == event:
                return key

        for key, val in self.global_mode.items():
            if isinstance(val, tuple):
                val, help = val
            if val == event:
                return key

modemap = ModeMap(default_global_mode)

