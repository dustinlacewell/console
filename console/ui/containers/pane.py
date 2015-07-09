from datetime import datetime
import json

import docker
import urwid
import subprocess
import os
import tempfile
import sys
import time

from twisted.internet import threads, reactor

from console.app import app
from console.ui.containers.inspect import ContainerInspector
from console.widgets.table import Table
from console.highlights import highlighter
from console.widgets.pane import Pane
from console.widgets.dialogs import Prompt, MessageListBox, TableDialog
from console.utils import catch_docker_errors
from console.state import ContainerMonitor, ImageMonitor

def split_repo_name(name):
    for idx in range(len(name)):
        c = name[-idx]
        if c == ':':
            return name[:-idx], name[-idx + 1:]
        elif c == '/':
            return name, ''
    return name, None

def clean_name(name):
    name = name.replace("u","")
    name = name.replace("'","")
    return name

class AlwaysFocusedEdit(urwid.Edit):
    def render(self, size, focus=False):
        return super(AlwaysFocusedEdit, self).render(size, focus=True)

class ContainerPane(Pane):
    def __init__(self):
        self.monitored = ContainerMonitor(docker.Client('unix://var/run/docker.sock', '1.18'))
        self.monitored.get_containers()
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
        urwid.connect_signal(self.monitored, 'container-list', self.set_containers)
    
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
        row.name = container['names']
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
            return super(ContainerPane, self).keypress(size, event)

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
            self.monitored.get_containers()
        elif event == 'delete-container':
            self.monitored.get_containers()
            self.dict_on_delete()
        elif event == 'commit-container':
            self.on_commit()
        elif event == 'inspect-details':
            self.on_inspect()
        elif event == 'set-mark':
            self.on_mark()
        elif event == 'run-container(s)' and not self.monitored.all:
            self.on_run()
        elif event == 'unmark-containers':
            self.on_unmark()
        elif event == 'rename-container':
            self.on_rename()
            self.monitored.get_containers()
        elif event == 'inspect-changes':
            self.on_diff()
        elif event == 'restart-container':
            self.monitored.get_containers()
            self.on_restart()
        elif event == 'kill-container':
            self.monitored.get_containers()
            self.on_kill()
        elif event == 'pause-container':
            self.monitored.get_containers()
            self.on_pause()
        elif event == 'unpause-container':
            self.monitored.get_containers()
            self.on_unpause()
        elif event == 'start-container':
            self.monitored.get_containers()
            self.on_start()
        elif event == 'stop-container':
            self.monitored.get_containers()
            self.on_stop()
        else:
            return super(ContainerPane, self).handle_event(event)

    def marked_exists(self):
        for k, v in self.marked_ids.items():
            if v == "marked":
                return True
        return False

    def make_command(self):
        row = 0
        none_marked = True
        for k, v in self.marked_containers.items():
            if v == "marked":
                self.commands += "screen %d docker exec -it %s bash\n" % (row, k.container)
                self.commands += "title %s\n" % k.image
                row += 1
                none_marked = False
        if none_marked:
            widget, idx = self.listing.get_focus()
            self.commands += "screen 0 docker exec -it %s bash\n" % widget.container
            self.commands += "title %s\n" % widget.image
        self.commands += "caption always\n"

    def on_run(self):
        self.make_command()
        temp = tempfile.NamedTemporaryFile()
        name = temp.name
        with open(name, "wt") as fout:
            fout.write(self.commands)
        subprocess.call(["screen", "-c", "%s" % name])
        temp.close()
        app.client.close()
        raise urwid.ExitMainLoop

    def on_next(self):
        self.listing.next()

    def on_prev(self):
        self.listing.prev()

    def on_mark(self):
        marked_widget, marked_id = self.listing.get_focus()
        if (marked_widget in self.marked_containers and 
                self.marked_containers[marked_widget] == "marked"):
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
        for key, value in self.marked_ids.items():
            if value == "marked":
                self.marked_ids[key] = "unmarked"

    def on_all(self):
        self.on_unmark()
        self.monitored.all = not self.monitored.all
    
    def dict_on_delete(self):
        none_marked = True
        for key, value in self.marked_containers.items():
            if value == "marked":
                widget = key
                self.on_delete(widget)
                del self.marked_containers[key]
                none_marked = False
        for k, v in self.marked_ids.items():
            if v == "marked":
                del self.marked_ids[k]
        if none_marked:
            widget, idx = self.listing.get_focus()
            self.on_delete(widget)

    @catch_docker_errors
    def on_delete(self, widget):
        highlighter.apply(widget, 'deleted', 'deleted')
        reactor.callLater(2.5, highlighter.remove, widget)
        return threads.deferToThread(app.client.remove_container, widget.container)

    @catch_docker_errors
    def perform_pause(self, widget):
        return threads.deferToThread(app.client.pause, widget)
        
    def on_pause(self):
        none_marked = True
        if len(self.marked_ids) > 0:
            for key, value in self.marked_ids.items():
                if value == "marked":
                    self.perform_pause(key)                
                    none_marked = False
        if none_marked:
            widget, idx = self.listing.get_focus()
            self.perform_pause(widget.container)
        else:
            self.on_unmark()

    @catch_docker_errors
    def perform_start(self, widget):
        return threads.deferToThread(app.client.start, widget)

    def on_start(self):
        none_marked = True
        for key, value in self.marked_ids.items():
            if value == "marked":
                self.perform_start(key)
                none_marked = False
        if none_marked:
            widget, idx = self.listing.get_focus()
            self.perform_start(widget.container)
        else:
            self.on_unmark()

    @catch_docker_errors
    def perform_stop(self, widget):
        return threads.deferToThread(app.client.stop, widget)

    def on_stop(self):
        none_marked = True
        for key, value in self.marked_ids.items():
            if value == "marked":
                self.perform_stop(key)
                none_marked = False
        if none_marked:
            widget, idx = self.listing.get_focus()
            self.perform_stop(widget.container)
        else:
            self.on_unmark()

    @catch_docker_errors
    def perform_unpause(self, widget):
        return threads.deferToThread(app.client.unpause, widget)

    def on_unpause(self):
        none_marked = True
        for key, value in self.marked_ids.items():
            if value == "marked":
                self.perform_unpause(key)
                none_marked = False
        if none_marked:
            widget, idx = self.listing.get_focus()
            self.perform_unpause(widget.container)
        else:
            self.on_unmark()
    
    @catch_docker_errors
    def perform_kill(self, widget):
        return threads.deferToThread(app.client.kill, widget)

    def on_kill(self):
        none_marked = True
        for key, value in self.marked_ids.items():
            if value == "marked":
                self.perform_kill(key)
                none_marked = False
        if none_marked:
            widget, idx = self.listing.get_focus()
            self.perform_kill(widget.container)
        else:
            self.on_unmark()

    @catch_docker_errors
    def perform_commit(self, container, repo_name):
        name, tag = split_repo_name(repo_name)
        repo_name = name + ":" + (tag or 'latest')
        self.close_dialog()
        return threads.deferToThread(app.client.commit, container, name, tag or 'latest')

    def on_commit(self):
        widget, idx = self.listing.get_focus()
        name, tag = split_repo_name(widget.image)
        prompt = Prompt(lambda name: self.perform_commit(widget.container, name), title="Tag Container:", initial=name)
        self.show_dialog(prompt)

    @catch_docker_errors
    def perform_restart(self, widget):
        return threads.deferToThread(app.client.restart, widget)

    def on_restart(self):
        none_marked = True
        for key, value in self.marked_ids.items():
            if value == "marked":
                self.perform_restart(key)
                none_marked = False
        if none_marked:
            widget, idx = self.listing.get_focus()
            self.perform_restart(widget.container)
        else:
            self.on_unmark()

    @catch_docker_errors
    def perform_rename(self, container, name):
        self.close_dialog()
        return threads.deferToThread(app.client.rename, container, name)
        
    def on_rename(self):
        widget, idx = self.listing.get_focus()
        name = clean_name(widget.name[0])
        prompt = Prompt(lambda name: self.perform_rename(widget.container, name), title="Rename Container:", initial=name)
        self.show_dialog(prompt)

    @catch_docker_errors
    def on_inspect(self):
        widget, idx = self.listing.get_focus()
        d = threads.deferToThread(app.client.inspect_container, widget.container)
        d.addCallback(lambda data: self.show_dialog(ContainerInspector(data)))
        return d

    def _show_diff(self, diff_json, container_id):
        for d in diff_json:
            if d['Kind'] == 0:
                d['Kind'] = 'Change'
            elif d['Kind'] == 1:
                d['Kind'] = 'Add'
            elif d['Kind'] == 2:
                d['Kind'] = 'Delete'
        diffs = [(d.get('Kind',''), d.get('Path','')) for d in diff_json]
        dialog = TableDialog(
            "Changes in %s" % container_id[:12],
            diffs,
            [
                {'value':"kind", 'weight':1, 'align':'center'},
                {'value':"path", 'weight':4, 'align':'center'}
            ]
        )
        dialog.width = ('relative', 90)
        self.show_dialog(dialog, )

    @catch_docker_errors
    def on_diff(self):
        widget, idx = self.listing.get_focus()
        d = threads.deferToThread(app.client.diff, widget.container)
        d.addCallback(self._show_diff, widget.container)
        d.addCallback(lambda r: app.draw_screen())
        return d
