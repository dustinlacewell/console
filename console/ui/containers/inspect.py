import urwid

from console.widgets.inspector import Inspector

class ContainerInspector(Inspector):
    title = "Container Information"

    def get_env_item(self, envs, label_width):
        envs = envs or []
        envs = [e.split('=', 1) for e in envs]
        if envs:
            longest = max(len(name) for name, val in envs)
            template = "{0:>%d} = {1}" % longest
            envs = urwid.Pile([urwid.Text(template.format(name, val)) for name, val in envs])
        else:
            envs = urwid.Text('')
        return urwid.Columns([
            (label_width, urwid.Text("Env  ", align='right')),
            envs,
        ])

    def get_vol_item(self, vols, label_width):
        if vols:
            longest = max(len(name) for name, val in vols.items())
            template = "{0:>%d} = {1}" % longest
            vols = urwid.Pile([urwid.Text(template.format(name, val)) for name, val in vols.items()])
        else:
            vols = urwid.Text('')
        return urwid.Columns([
            (label_width, urwid.Text("Volumes  ", align='right')),
            vols,
        ])

    def handle_item(self, key, val, longest):
        if key == "Env":
            return self.get_env_item(val, longest)
        if key == "Volumes":
            return self.get_vol_item(val, longest)
        if key == 'Cmd' or key == 'Entrypoint':
            if isinstance(val, list):
                return self.get_string_item(key, " ".join(val), longest)
        if (isinstance(val, str) or isinstance(val, unicode)) and '=' in val:
            one, two = val.split('=', 1)
            return self.get_string_item(one, two, longest)
        return super(ContainerInspector, self).handle_item(key, val, longest)

    def get_contents(self, data):
#        import pdb; pdb.set_trace()
        contents = []

        contents.append(self.get_string_item("ID", data['Id'], 19))

        contents.append(self.get_string_item("Created", data['Created'], 19))

        longest = max(len(k) for k in data['Config'])
        contents.append(self.get_dict_item('Config', data['Config'], 19))
        longest = max(len(k) for k in data['HostConfig'])
        contents.append(self.get_dict_item('HostConfig', data['HostConfig'], 19))

        return contents


