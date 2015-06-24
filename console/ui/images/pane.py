import urwid

import os

from twisted.internet import threads, reactor

from console.app import app
from console.ui.images.inspect import ImageInspector
from console.widgets.extra import AlwaysFocusedEdit
from console.widgets.table import Table
from console.highlights import highlighter
from console.widgets.pane import Pane
from console.widgets.dialogs import Prompt, MessageListBox
from console.utils import catch_docker_errors, split_repo_name


class ImagePane(Pane):
    def __init__(self):
        self.image_data = []
        self.images = {}
        self.edit = AlwaysFocusedEdit("filter: ", multiline=False)
        self.listing = self.init_listing()
        self.filter = ""
	self.marked = False 
	self.marked_count = 0
        self.marking_down = True
        self.at_edge = False
        self.edges = [True, False]
        Pane.__init__(self, urwid.Frame(
            self.listing,
            self.edit,
        ))
        self.original_widget.focus_position = 'body'
        urwid.connect_signal(app.state.images, 'image-list', self.set_images)

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
        elif event == 'delete-image':
	    if self.marked:
                self.delete_marked()
            else:
                self.on_delete()
        elif event == 'tag-image':
            self.on_tag()
        elif event == 'inspect-details':
            self.on_inspect()
        elif event == 'help':
            self.on_help()
	elif event == 'set-mark' and not app.state.images.all:
	    self.on_marked()
        else:
            return super(ImagePane, self).handle_event(event)

    def on_next(self):
	if self.marked_count == 1:
	    self.marking_down = True
	if self.marked:
       	    if self.marking_down:
                if self.at_edge:
                    return super(ImagePane, self).handle_event(' ')
	        self.mark_image()
            else:
	        self.unmark_image()
        self.at_edge = self.listing.at_edge(self.marking_down)
        self.listing.next()

    def on_prev(self):
	if self.marked_count == 1:
	    self.marking_down = False
	if self.marked: 
            if not self.marking_down:
                if self.at_edge:
                    return super(ImagePane, self).handle_event(' ')
	        self.mark_image()
	    else:
	        self.unmark_image()
        self.at_edge = self.listing.at_edge(self.marking_down)
        self.listing.prev()

    def mark_image(self):
        self.at_edge = self.listing.at_edge(self.marking_down)
        self.marked_count += 1
        if self.marked_count >= 1:
            self.listing.mark()

    def unmark_image(self):
        self.marked_count -= 1
        self.listing.unmark()

    def on_all(self):
        if self.marked:
            self.on_marked()
        app.state.images.all = not app.state.images.all

    def on_marked(self):
	self.marked = not self.marked
	if self.marked:
	    self.marked_count += 1
	    self.listing.mark()
	else:
	    self.marked = True
	    marked_rows = self.marked_count
	    for x in xrange(marked_rows - 1):
		if marked_rows != 1:
      	            if self.marking_down:
		        self.handle_event('prev-image') 			
		    else:
		        self.handle_event('next-image') 			
	    self.marked = False
 	    self.marked_count = 0
	    self.listing.unmark()

    # def _show_history(self, history_json, image_id):
    #     history = json.loads(history_json)
    #     histories = [(d.get('Id', '')[:12], d.get('CreatedBy', '')) for d in history]
    #     dialog = TableDialog(
    #         "History for %s" % image_id[:12],
    #         histories,
    #         [
    #             TableCell("image id", align='center'),
    #             TableCell("command", align='left', weight=4)
    #         ]
    #     )
    #     dialog.width = ('relative', 90)
    #     self.show_dialog(dialog, )

    # @catch_docker_errors
    # def on_history(self):
    #     widget, idx = self.listing.get_focus()
    #     d = threads.deferToThread(app.client.history, widget.image)
    #     d.addCallback(self._show_history, widget.image)
    #     d.addCallback(lambda r: app.draw_screen())
    #     return d

    def delete_marked(self):
	marked_rows = self.marked_count
	self.on_marked()
        for x in xrange(marked_rows - 1):
            self.on_delete()
	    self.marked_count -= 1
	    if self.marking_down:
                self.handle_event('next-image')
            else:
                self.handle_event('prev-image')
	self.on_delete()

    @catch_docker_errors
    def on_delete(self):
        widget, idx = self.listing.get_focus()
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
