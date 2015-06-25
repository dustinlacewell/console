from datetime import datetime
import json

import docker
import urwid
import subprocess
import os
import tempfile
import shutil

from twisted.internet import threads, reactor

from console.app import app
from console.ui.containers.inspect import ContainerInspector
from console.widgets.table import Table
from console.highlights import highlighter
from console.widgets.pane import Pane
from console.widgets.dialogs import Prompt, MessageListBox
from console.utils import catch_docker_errors


def split_repo_name(name):
    for idx in range(len(name)):
        c = name[-idx]
        if c == ':':
            return name[:-idx], name[-idx + 1:]
        elif c == '/':
            return name, ''
    return name, None


class AlwaysFocusedEdit(urwid.Edit):
    def render(self, size, focus=False):
        return super(AlwaysFocusedEdit, self).render(size, focus=True)

class ContainerPane(Pane):
    def __init__(self):
        self.container_data = []
        self.containers = {}
        self.edit = AlwaysFocusedEdit("filter: ", multiline=False)
        self.listing = self.init_listing()
        self.filter = ""
        self.commands = ""
        self.marked_containers = {}
        self.marked_ids = {}
        self.marking_down = True
        Pane.__init__(self, urwid.Frame(
            self.listing,
            self.edit,
        ))
        self.original_widget.focus_position = 'body'
        urwid.connect_signal(app.state.containers, 'container-list', self.set_containers)

    def init_listing(self):
        schema = (
            {'name': 'Id'},
            {'name': 'Image'},
            {'name': 'Command'},
            {'name': 'Status'},
            {'name': 'Names'},
        )
        return Table(schema, header=True)

    def make_container_row(self, container):
        row = self.listing.create_row({
            'Id': container['id'][:12],
            'Image': container['image'],
            'Command': container['command'],
            'Status': container['status'],
            'Names': container['names'],
        })
        row.image = container['image']
        row.container = container['id']
        self.containers[row.container] = row
        return row

    def set_containers(self, containers, force=False):
        # save the current position
        _, current_focus = self.listing.get_focus()

        if containers == self.container_data and not force:
            return

        self.listing.clear()
        self.old_containers = self.containers
        self.containers = {}

        running = [c for c in containers if 'Exited' not in c['status']]
        stopped = [c for c in containers if 'Exited' in c['status']]

        filter = self.filter.lower()

        def remove_highlight(row):
            highlighter.remove(row)

        for container in running:
            in_names = any(filter in name.lower() for name in container['names'])
            in_id = filter in container['id'].lower()
            in_status = filter in container['status'].lower()
            in_image = filter in container['image'].lower()
            row = self.make_container_row(container)
            if any((in_names, in_id, in_status, in_image)):
                self.listing.walker.append(row)
                if self.old_containers and row.container not in self.old_containers:
                    highlighter.apply(row, 'created', 'created')
                    reactor.callLater(1, highlighter.remove, row)


        for container in stopped:
            in_names = any(filter in name.lower() for name in container['names'])
            in_id = filter in container['id'].lower()
            in_status = filter in container['status'].lower()
            in_image = filter in container['image'].lower()
            row = self.make_container_row(container)
            if any((in_names, in_id, in_status, in_image)):
                self.listing.walker.append(row)
                if self.old_containers and row.container not in self.old_containers:
                    highlighter.apply(row, 'created', 'created')
                    reactor.callLater(1, highlighter.remove, row)

        self.container_data = containers
        self.listing.set_focus(current_focus)
        self.listing.fix_focus()
        app.draw_screen()

    def keypress(self, size, event):
        if self.dialog:
            if event == 'close-dialog':
                return self.close_dialog()
            else:
                return self.dialog.keypress(size, event)

        if self.listing.keypress(size, event):
            if self.handle_event(event):
                if not self.dialog and self.edit.keypress((size[0], ), event):
                    return super(ContainerPane, self).keypress(size, event)
                else:
                    self.filter = self.edit.edit_text
                    self.set_containers(self.container_data, force=True)

    def handle_event(self, event):
        if event == 'next-container':
            self.on_next()
        elif event == 'prev-container':
            self.on_prev()
        elif event == 'toggle-show-all':
            self.on_all()
        elif event == 'delete-container':
            self.dict_on_delete()
        elif event == 'commit-container':
            self.on_tag()
        elif event == 'inspect-details':
            self.on_inspect()
        elif event == 'set-mark':
            self.on_mark()
        elif event == 'run-container(s)':
            self.on_run()
        elif event == 'unmark-containers':
            self.on_unmark()
        else:
            return super(ContainerPane, self).handle_event(event)

    def read_file(self, filename, mode = "rt"):
        with open(filename, mode) as fin:
            return fin.read()

    def write_file(self, filename, contents, mode = "wt"):
        open("filename", "w").close() #clear file
        with open(filename, mode) as fout:
            fout.write(contents)

    def write_commands(self):
        path = "run_command" + os.sep + ".screenrc"
        if (not os.path.exists("run_command")):
            os.makedirs("run_command")
        if not os.path.exists(path) or self.read_file(path) == "":
            self.write_file(path, self.commands)
        elif (os.path.exists(path) and self.read_file(path) != self.commands):
            self.write_file(path, self.commands)

    def make_command(self):
        id = self.get_Id()
        row = 0
        self.commands += "screen %d docker exec -it %s bash\n" % (row, id)
        for x in xrange(self.marked_count - 1):
            row += 1
            if self.marking_down:
                self.on_prev()
            else:
                self.on_next()
            id = self.get_Id()
            self.commands += "screen %d docker exec -it %s bash\n" % (row, id) 
        self.write_commands()

    def get_Id(self):
        widget, idx = self.listing.get_focus()
        info = app.client.inspect_container(widget.container)
        id = info['Id']
        return id
    
    def make_command(self):
        row = 0
        for k, v in self.marked_ids.items():
            if v == "marked":
                self.commands += "screen %d docker exec -it %s bash\n" % (row, k)
        self.write_commands()

    def on_run(self):
        self.make_command()
        subprocess.call(["screen", "-c", "run_command/.screenrc"])
        #temp = tempfile.mkdtemp()
        #filename = os.path.join(temp, '.screenrc')
        #self.write_file(filename, self.commands)
        
        #temp = tempfile.NamedTemporaryFile()
        #temp.write(self.commands)
        #print temp.read()
        #temp.close() 
        #subprocess.call(["screen", "-c", "%s" % filename])
        #shutil.rmtree(temp)
        
        app.client.close()
        raise urwid.ExitMainLoop

    def on_next(self):
        self.listing.next()

    def on_prev(self):
        self.listing.prev()

    def mark_containers(self):
        self.listing.mark()

    def unmark_containers(self):
        self.listing.unmark()

    def get_widget(self):
        widget, idx = self.listing.get_focus()
        return widget

    def on_mark(self):
        marked_widget = self.get_widget()
        marked_id = self.get_Id()
        if marked_widget in self.marked_containers:
            self.marked_containers[marked_widget] = "unmarked"
            self.marked_ids[marked_id] = "unmarked"
            self.listing.unmark()
        else:
            self.marked_containers[marked_widget] = "marked"
            self.marked_ids[marked_id] = "marked"
            self.listing.mark()

    def on_unmark(self):
        for key, value in self.marked_containers.items():
            if value == "marked":
                self.marked_containers[key] = "unmarked"
                key.set_attr_map({None:None})

    def on_all(self):
        app.state.containers.all = not app.state.containers.all
    
    def dict_on_delete(self):
        for key, value in self.marked_containers.items():
            if value == "marked":
                widget = key
                self.on_delete(widget)
                del self.marked_containers[key]
        for k, v in self.marked_ids.items():
            if v == "marked":
                del self.marked_ids[k]
    
    @catch_docker_errors
    def on_delete(self, widget):
        highlighter.apply(widget, 'deleted', 'deleted')
        reactor.callLater(2.5, highlighter.remove, widget)
        return threads.deferToThread(app.client.remove_container, widget.container)

    @catch_docker_errors
    def perform_commit(self, container, repo_name):
        name, tag = split_repo_name(repo_name)
        repo_name = name + ":" + (tag or 'latest')
        self.close_dialog()
        return threads.deferToThread(app.client.commit, container, name, tag or 'latest')

    def on_commit(self):
        widget, idx = self.listing.get_focus()
        name, tag = split_repo_name(widget.tag)
        prompt = Prompt(lambda name: self.perform_tag(widget.container, name), title="Tag Container:", initial=name)
        self.show_dialog(prompt)

    @catch_docker_errors
    def on_inspect(self):
        widget, idx = self.listing.get_focus()
        d = threads.deferToThread(app.client.inspect_container, widget.container)
        d.addCallback(lambda data: self.show_dialog(ContainerInspector(data)))
        return d
