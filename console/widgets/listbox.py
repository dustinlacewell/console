# -*- coding: utf-8 -*-

import urwid


class FancyListBox(urwid.LineBox):
    def get_listbox(self, items):
        class _FancyListBox(urwid.ListBox):
            def keypress(_self, size, key):
                key = super(_FancyListBox, _self).keypress(size, key)
                self.update_corners(_self.ends_visible(size))
                return key

            def render(_self, size, focus=False):
                self.update_corners(_self.ends_visible(size))
                return super(_FancyListBox, _self).render(size, focus)

        return _FancyListBox(urwid.SimpleListWalker(items))

    def __init__(self, items, title="",
                 tlcorner=u'┌', tline=u' ', lline=u' ',
                 trcorner=u'┐', blcorner=u'└', rline=u' ',
                 bline=u' ', brcorner=u'┘'):

        self.length = len(items[2].contents) + 5
        self.listbox = self.get_listbox(items)

        tline, bline = urwid.Divider(tline), urwid.Divider(bline)
        lline, rline = urwid.SolidFill(lline), urwid.SolidFill(rline)
        self.tlcorner, self.trcorner = urwid.Text(tlcorner), urwid.Text(trcorner)
        self.blcorner, self.brcorner = urwid.Text(blcorner), urwid.Text(brcorner)

        title_widget = urwid.Text(self.format_title(title))
        tline_widget = urwid.Columns([
            tline,
            ('flow', title_widget),
            tline,
        ])

        top = urwid.Columns([
            ('fixed', 1, self.tlcorner),
            tline_widget,
            ('fixed', 1, self.trcorner),
        ])

        middle = urwid.Columns([
            ('fixed', 1, lline),
            self.listbox,
            ('fixed', 1, rline),
        ], box_columns=[0, 2], focus_column=1)

        bottom = urwid.Columns([
            ('fixed', 1, self.blcorner), bline, ('fixed', 1, self.brcorner),
        ])

        pile = urwid.Pile([('flow', top), middle, ('flow', bottom)], focus_item=1)

        urwid.WidgetDecoration.__init__(self, self.listbox)
        urwid.WidgetWrap.__init__(self, pile)

    def top_scroll(self):
        self.trcorner.set_text(u"⇧")
        self.tlcorner.set_text(u"⇧")

    def top_noscroll(self):
        self.trcorner.set_text(u"┐")
        self.tlcorner.set_text(u"┌")

    def bottom_scroll(self):
        self.brcorner.set_text(u"⇩")
        self.blcorner.set_text(u"⇩")

    def bottom_noscroll(self):
        self.brcorner.set_text(u"┘")
        self.blcorner.set_text(u"└")

    def update_corners(self, ends):
        if 'top' in ends:
            self.top_noscroll()
        else:
            self.top_scroll()

        if 'bottom' in ends:
            self.bottom_noscroll()
        else:
            self.bottom_scroll()


