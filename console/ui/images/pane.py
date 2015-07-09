import urwid

import os
import json
import docker

from twisted.internet import threads, reactor

from console.app import app
from console.ui.images.inspect import ImageInspector
from console.widgets.extra import AlwaysFocusedEdit
from console.widgets.table import Table, TableCell
from console.highlights import highlighter
from console.widgets.pane import Pane
from console.widgets.dialogs import Prompt, MessageListBox, TableDialog
from console.utils import catch_docker_errors, split_repo_name
from console.state import ImageMonitor

class ImagePane(Pane):
    def __init__(self):
        self.monitored = ImageMonitor(docker.Client('unix://var/run/docker.sock', '1.18'))
        self.monitored.get_images()
        self.image_data = []
        self.images = {}
        self.edit = AlwaysFocusedEdit("filter: ", multiline=False)
        self.listing = self.init_listing()
        self.filter = ""
        self.marked_widgets = {}
        Pane.__init__(self, urwid.Frame(
            self.listing,
            self.edit,
        ))
        self.original_widget.focus_position = 'body'
        urwid.connect_signal(self.monitored, 'image-list', self.set_images)

    def init_listing(self):
        schema = (
            {'name': 'Tag', 'align':'right', 'weight':1},
            {'name': 'Id', 'align':'center'},
            {'name': 'Created'},
        )
        return Table(schema, header=True)

    def make_image_row(self, image):
        row = self.listing.create_row({
            'Tag': image['tag'],
            'Id': image['id'][:12],
            'Created': "%s days ago" % image['days_old'],
        })
        row.tag = image['tag']
        row.image = image['id']
        self.images[row.tag] = row
        return row

    def set_images(self, images, force=False):
        # save the current position
        _, current_focus = self.listing.get_focus()

        if images == self.image_data and not force:
            return

        self.listing.clear()
        self.old_images = self.images
        self.images = {}

        untagged = [i for i in images if i['tag'] == '<none>:<none>']
        tagged = [i for i in images if i['tag'] != '<none>:<none>']

        filter = self.filter.lower()

        def remove_highlight(row):
            highlighter.remove(row)

        for image in tagged:
            in_tag = filter in image['tag'].lower()
            in_id = filter in image['id'].lower()
            row = self.make_image_row(image)
            if in_tag or in_id:
                self.listing.walker.append(row)
                if self.old_images and row.tag not in self.old_images:
                    highlighter.apply(row, 'created', 'created')
                    reactor.callLater(1, highlighter.remove, row)


        for image in untagged:
            in_tag = filter in image['tag'].lower()
            in_id = filter in image['id'].lower()
            row = self.make_image_row(image)
            if in_tag or in_id:
                self.listing.walker.append(row)
                if self.old_images and row.tag not in self.old_images:
                    highlighter.apply(row, 'created', 'created')
                    reactor.callLater(1, highlighter.remove, row)

        self.image_data = images
        self.listing.set_focus(current_focus)
        self.listing.fix_focus()
        app.draw_screen()

    def keypress(self, size, event):
        if self.dialog:
            return super(ImagePane, self).keypress(size, event)

        if self.listing.keypress(size, event):
            if self.handle_event(event):
                if not self.dialog and self.edit.keypress((size[0], ), event):
                    return super(ImagePane, self).keypress(size, event)
                else:
                    self.filter = self.edit.edit_text
                    self.set_images(self.image_data, force=True)

    def handle_event(self, event):
        if event == 'next-image':
            self.on_next()
        elif event == 'prev-image':
            self.on_prev()
        elif event == 'toggle-show-all':
            self.on_all()
            self.monitored.get_images()
        elif event == 'delete-image':
            self.monitored.get_images()
            self.delete_marked()
        elif event == 'tag-image':
            self.on_tag()
            self.monitored.get_images()
        elif event == 'inspect-details':
            self.on_inspect()
        elif event == 'help':
            self.on_help()
        elif event == 'set-mark' and not self.monitored.all:
            self.on_marked()
        elif event == 'unmark-images':
            self.on_unmark()
        elif event == 'view-history':
            self.on_history()
        elif event == 'push-image':
            self.monitored.get_images()
            self.push()
        else:
            self.monitored.get_images()
            return super(ImagePane, self).handle_event(event)

    def on_next(self):
        self.listing.next()

    def on_prev(self):
        self.listing.prev()

    def on_all(self):
        self.monitored.all = not self.monitored.all

    def get_widget(self):
        widget, idx = self.listing.get_focus()
        return widget

    def on_marked(self):
        marked_widget = self.get_widget()
        if (marked_widget in self.marked_widgets and 
                self.marked_widgets[marked_widget] == "marked"):
            self.marked_widgets[marked_widget] = "unmarked"
            self.listing.unmark()
        else:
            self.marked_widgets[marked_widget] = "marked"
            self.listing.mark()

    def on_unmark(self):
        for key, value in self.marked_widgets.items():
            if value == "marked":
                self.marked_widgets[key] = "unmarked"
                key.set_attr_map({None:None})

    def _show_history(self, history_json, image_id):
        history = history_json
        histories = [(d.get('Id', '')[:12], d.get('CreatedBy', '')) for d in history]
        dialog = TableDialog(
            "History for %s" % image_id[:12],
            histories,
            [
                {'value':"image id", 'weight':1, 'align':'center'},
                {'value':"command", 'weight':4, 'align':'center'}
            ]
        )
        dialog.width = ('relative', 90)
        self.show_dialog(dialog, )

    @catch_docker_errors
    def on_history(self):
        widget, idx = self.listing.get_focus()
        d = threads.deferToThread(app.client.history, widget.image)
        d.addCallback(self._show_history, widget.image)
        d.addCallback(lambda r: app.draw_screen())
        return d

    def delete_marked(self):
        none_marked = True
        for key, value in self.marked_widgets.items():
            if value == "marked":
                widget = key
                self.on_delete(widget)
                del self.marked_widgets[key]
                none_marked = False
        if none_marked:
            widget, idx = self.listing.get_focus()
            self.on_delete(widget)

    @catch_docker_errors
    def on_delete(self, widget):
        highlighter.apply(widget, 'deleted', 'deleted')
        reactor.callLater(10, highlighter.remove, widget)
        if widget.tag == "<none>:<none>":
            widget.tag = widget.image
        d = threads.deferToThread(app.client.remove_image, widget.tag)
        d.addErrback(lambda _: highlighter.remove(widget) or _)
        return d

    @catch_docker_errors
    def perform_tag(self, image, repo_name):
        name, tag = split_repo_name(repo_name)
        repo_name = name + ":" + (tag or 'latest')
        self.close_dialog()
        return threads.deferToThread(app.client.tag, image, name, tag or 'latest')

    def on_tag(self):
        widget, idx = self.listing.get_focus()
        name, tag = split_repo_name(widget.tag)
        prompt = Prompt(lambda name: self.perform_tag(widget.image, name), title="Tag Image:", initial=name)
        self.show_dialog(prompt)

    @catch_docker_errors
    def push(self):
        widget, idx = self.listing.get_focus()
        name, tag = split_repo_name(widget.tag)
        highlighter.apply(widget, 'uploading', 'uploading_focus')
        d = threads.deferToThread(app.client.push, name)

        def handle_response(r):
            r = r.replace("}{", "},{")
            r = r.replace("1)\"}", "1)\"},")
            r = r.replace("2)\"}", "2)\"},")
            r = "[%s]" % r
            messages = [d.get('status') or d.get('error') for d in json.loads(r)]
            self.show_dialog(MessageListBox(messages, title='Push Response', width=100))
            reactor.callLater(5.0, highlighter.remove, widget)

        d.addCallback(handle_response)
        return d
    
    @catch_docker_errors
    def on_inspect(self):
        widget, idx = self.listing.get_focus()
        d = threads.deferToThread(app.client.inspect_image, widget.image)
        d.addCallback(lambda data: self.show_dialog(ImageInspector(data)))
        return d
