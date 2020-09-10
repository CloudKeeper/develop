"""
Containers and Player Stash - TO BE TESTED

This provides the ability to get objects from other objects, allowing any
object to become a container.

This also provides a Player Stash implementation, a container object who's
'contents' are available to be obtained from any one of possible multiple 
Player Stash objects in the world.

The 'Get', 'Give' and 'Drop' commands have been edited to support this
behaviour and a custom CommandSet is provided.
"""

import evennia
from typeclasses.objects import Object
COMMAND_DEFAULT_CLASS = utils.class_from_module(settings.COMMAND_DEFAULT_CLASS)
from evennia.utils.utils import (list_to_string)


class CmdGet(COMMAND_DEFAULT_CLASS):
    """
    Take object from your location [or target object]
    
    Usage:
        get <obj> [<= or from> obj]
        
    Example:
        get wooden sword
        get big book from old bookshelf
    """
    key = "get"
    aliases = ["grab", "take"]
    rhs_split = ("=", " from ")  # Allow " from " usage.
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def func(self):
        """implements the command."""

        caller = self.caller
        # If no args
        if not self.args:
            caller.msg("Get what?")
            return

        # 1. lhs = "wooden sword"; rhs = ""
        # 2. lhs = "Big book"; rhs = "old bookshelf"
        if self.rhs:
            location = caller.search(self.rhs)
        else:
            location = caller.location
        if not location:
            return
        
        # TO DO Add some sort of check that you can get objects from target

        # Get Object. We have to allow for Player Stash
        if isinstance(location, Stash):
            obj = caller.search(self.lhs,
                                candidates=evennia.search_tag(caller.dbref,
                                                              category="stash"))
        else:
            obj = caller.search(self.lhs, location=location)
        if not obj:
            return
        if caller == obj:
            caller.msg("You can't get yourself.")
            return
        if not obj.access(caller, 'get'):
            if obj.db.get_err_msg:
                caller.msg(obj.db.get_err_msg)
            else:
                caller.msg("You can't get that.")
            return

        # calling at_before_get hook method
        if not obj.at_before_get(caller):
            return

        obj.move_to(caller, quiet=True)
        if self.rhs:
            caller.msg("You pick up %s from %s." % (obj.name, location.name))
            caller.location.msg_contents("%s picks up %s from %s." % 
                                         (caller.name, obj.name, location.name),
                                         exclude=caller)
        else:
            caller.msg("You pick up %s." % obj.name)
            caller.location.msg_contents("%s picks up %s." %
                                         (caller.name, obj.name),
                                         exclude=caller)

        # calling at_get hook method
        obj.at_get(caller)


class CmdDrop(COMMAND_DEFAULT_CLASS):
    """
    drop something at your location [or target location.]

    Usage:
      drop <obj> [<= or in> obj]

    Example:
        drop wooden sword
        drop big book in old bookshelf
    """

    key = "drop"
    rhs_split = ("=", " in ")  # Allow " in " usage.
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def func(self):
        """Implement command"""

        caller = self.caller
        # If no args
        if not self.args:
            caller.msg("Drop what?")
            return

        # 1. lhs = "wooden sword"; rhs = ""
        # 2. lhs = "Big book"; rhs = "old bookshelf"
        if self.rhs:
            location = caller.search(self.rhs)
        else:
            location = caller.location
        if not location:
            return
        # TO DO Add some sort of check that you can drop objects in target

        # Because the DROP command by definition looks for items
        # in inventory, call the search function using location = caller
        obj = caller.search(self.lhs, location=caller,
                            nofound_string="You aren't carrying %s." % self.lhs,
                            multimatch_string="You carry more than one %s:" % self.lhs)
        if not obj:
            return

        # Call the object script's at_before_drop() method.
        if not obj.at_before_drop(caller):
            return

        obj.move_to(location, quiet=True)
        if self.rhs:
            caller.msg("You drop %s in %s." % (obj.name, location.name))
            caller.location.msg_contents("%s drops %s in %s." %
                                         (caller.name, obj.name, location.name),
                                         exclude=caller)
        else:
            caller.msg("You drop %s." % obj.name)
            caller.location.msg_contents("%s drops %s." %
                                         (caller.name, obj.name),
                                         exclude=caller)

        # Call the object script's at_drop() method.
        obj.at_drop(caller)


class CmdGive(COMMAND_DEFAULT_CLASS):
    """
    give away something to someone

    Usage:
      give <inventory obj> <to||=> <target>

    Gives an items from your inventory to another character,
    placing it in their inventory.
    """
    key = "give"
    rhs_split = ("=", " to ")  # Prefer = delimiter, but allow " to " usage.
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def func(self):
        """Implement give"""

        caller = self.caller
        if not self.args or not self.rhs:
            caller.msg("Usage: give <inventory object> = <target>")
            return
        to_give = caller.search(self.lhs, location=caller,
                                nofound_string="You aren't carrying %s." % self.lhs,
                                multimatch_string="You carry more than one %s:" % self.lhs)
        target = caller.search(self.rhs)
        if not (to_give and target):
            return
        if target == caller:
            caller.msg("You keep %s to yourself." % to_give.key)
            return
        if not to_give.location == caller:
            caller.msg("You are not holding %s." % to_give.key)
            return

        # calling at_before_give hook method
        if not to_give.at_before_give(caller, target):
            return

        # give object
        caller.msg("You give %s to %s." % (to_give.key, target.key))
        to_give.move_to(target, quiet=True)
        target.msg("%s gives you %s." % (caller.key, to_give.key))
        # Call the object script's at_give() method.
        to_give.at_give(caller, target)


class Container(Object):
    """
    This is the default Container Object.
    Any object of any typeclass can be a container by default. This typeclass
    just adjusts the return_appearance to make the 'look' command show the 
    objects contents in a more instructive format.
    """

    def return_appearance(self, looker, **kwargs):
        """
        This formats a description. It is the hook a 'look' command
        should call.
        
        The Container object should not have characters or exits inside of it.
        We provide a list of objects and a brief description so players can 
        decide to retrieve the objects or not.
        
        Args:
            looker (Object): Object doing the looking.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).
        """
        if not looker:
            return ""
        # get and identify all objects
        visible = (con for con in self.contents if con != looker and
                   con.access(looker, "view"))
                   
        string = "|c%s|n\n" % self.get_display_name(looker)
        desc = self.db.desc
        if desc:
            string += "%s" % desc
        if visible:
            string += "\n|wContents:|n "
            for obj in visible:
                string += "%s - %s" % (obj.name, obj.db.desc.strip('\n')[0:80-(len(obj.name)+6)] + "...")
        
        
class Stash(Container):
    """
    This is a basic personal stash for players.

    The stash gives objects a player tag and stores it in None.
    Objs taken from stash by the player are retrieved with the tag from none.
    """

    def return_appearance(self, looker, **kwargs):
        """
        This formats a description. It is the hook a 'look' command
        should call.
        
        The Stash will not have any objects stored inside it. We collect all
        the objects the Player currently has in it's Stash by pulling the tag
        and presents it as the Stash's contents.
        
        Args:
            looker (Object): Object doing the looking.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).
        """
        if not looker:
            return ""
        # get and identify all objects
        tagged_objs = evennia.search_tag(looker.dbref, category="stash")
                   
        string = "|c%s|n\n" % self.get_display_name(looker)
        desc = self.db.desc
        if desc:
            string += "%s" % desc
        if tagged_objs:
            string += "\n|wContents:|n "
            for obj in tagged_objs:
                string += "%s - %s" % (obj.name, obj.db.desc.strip('\n')[0:80-(len(obj.name)+6)] + "...")
    
    def at_object_receive(self, moved_obj, source_location, **kwargs):
        """
        Called after an object has been moved into this object.
        Args:
            moved_obj (Object): The object moved into this one
            source_location (Object): Where `moved_object` came from.
                Note that this could be `None`.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).
        """
        if source_location:
            moved_obj.tags.add(source_location.dbref, category="stash")
            moved_obj.location = None
