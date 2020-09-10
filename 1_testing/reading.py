"""
Reading - TO BE TESTED

Read an in-game book.

Creates a book object. 'Use' of the book opens a EvMenu that displays the pages
of the book.

Usage - In-game:
    @create book:features.reading.Book
    read book

# -----------------------------------------------------------------------------
NOTES:
-Right now it'll trigger on look. I don't want that. I only want it to trigger
on "read"
-It'll also trigger on anything that's not a command.
-I'll need to add all the 'commands' to options and do a "skip" command or
something to go to a specific page.
# -----------------------------------------------------------------------------
"""

import time
from django.conf import settings
from evennia.utils import utils, evmenu
from evennia import CmdSet
from evennia.utils.create import create_object
from typeclasses.objects import Object

COMMAND_DEFAULT_CLASS = utils.class_from_module(settings.COMMAND_DEFAULT_CLASS)

_TGT_ERRMSG = "'{}' could not be located."

# ------------------------------------------------------------------------------
# General Read Command - Held by the Character
# ------------------------------------------------------------------------------


class ReadCmdSet(CmdSet):
    """
    Read Command Set held by the Character. 
    """
    key = "readcmdset"
    priority = 1

    def at_cmdset_creation(self):
        self.add(CmdRead())


class CmdRead(COMMAND_DEFAULT_CLASS):
    """
    Read target obj.

    Usage:
        read <subject>

    """
    key = "read"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        """Triggers an object's at_read() function"""
        caller = self.caller

        # No target given.
        if not self.args:
            caller.msg("Read what?")
            return

        # No target found.
        obj = caller.search(self.args)
        if not obj:
            return

        # Target not readable.
        if not getattr(obj, "at_read", None):
            caller.msg("You cannot read this object.")
            return

        # Read Target.
        obj.at_read(caller)

# ------------------------------------------------------------------------------
# Book Object - Holds readable content, triggered by at_read()
# ------------------------------------------------------------------------------


class Book(Object):

    def at_object_creation(self):
        super(Book, self).at_object_creation()
        self.db.screen_height = 23
        self.db.screen_width = 80
        self.db.text = ""
        self.db.pages = []
        self.db.current_page = 0

    def at_read(self, caller):

        if not self.db.pages:
            self.init_content()

        evmenu.EvMenu(caller, {"book_node":book_node},
                      startnode="book_node",
                      cmdset_mergetype="Union",
                      node_formatter=photograph_node_formatter,
                      options_formatter=photograph_options_formattter,
                      book=self)

    def init_content(self):
        # Fit text to width. Split into lines and reform into target height
        text = utils.wrap(self.db.text, width=self.db.screen_width,
                          indent=2).split("\n")
        self.db.pages = ["\n".join(text[i:i + self.db.screen_height])
                         for i in range(0, len(text), self.db.screen_height)]
        self.db.current_page = 0

# ------------------------------------------------------------------------------
# Book Menu - Read the pages of a book.
# ------------------------------------------------------------------------------


def photograph_node_formatter(nodetext, optionstext, caller=None):
    """
    A minimalistic node formatter, no lines or frames.
    """
    return nodetext + "\n" + optionstext


def photograph_options_formattter(optionlist, caller=None):
    """
    A minimalistic options formatter that mirrors a rooms content list.
    """
    if not optionlist:
        return ""

    return "You see: " + ", ".join([key for key, msg in optionlist])


def book_node(caller, input_string):
    menu = caller.ndb._menutree
    text = ""
    options = [{"key": "_default",
                "goto": "book_node"}]

    pages = menu.book.db.pages
    current_page = menu.book.db.current_page

    # Handle commands
    if input_string in ["n", "next", "next page"]:
        current_page = min(current_page+1, len(pages)-1)

    elif input_string in ["b", "back"]:
        current_page = max(0, current_page-1)

    elif input_string in ["f", "first", "first page"]:
        current_page = 0

    elif input_string in ["l", "last", "last page"]:
        current_page = len(pages)-1

    elif isinstance(input_string, int):
        current_page = max(0, min(int(input_string), len(pages)-1))

    # Display Text.
    text = pages[current_page]

    return text, options

