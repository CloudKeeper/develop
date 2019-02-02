"""


"""

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
            location = caller.search(self.rhs, location=caller.location)
        else:
            location = caller.location
        if not location:
            return
        # TO DO Add some sort of check that you can get objects from target
        
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
            location = caller.search(self.rhs, location=caller.location)
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
    A Mixin that allows taking and putting objects inside this object.
    """

    def return_appearance(self, looker, **kwargs):
        """
        This formats a description. It is the hook a 'look' command
        should call.
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
        exits, users, things = [], [], defaultdict(list)
        for con in visible:
            key = con.get_display_name(looker)
            if con.destination:
                exits.append(key)
            elif con.has_account:
                users.append("|c%s|n" % key)
            else:
                # things can be pluralized
                things[key].append(con)
        # get description, build string
        string = "|c%s|n\n" % self.get_display_name(looker)
        desc = self.db.desc
        if desc:
            string += "%s" % desc
        if exits:
            string += "\n|wExits:|n " + list_to_string(exits)
        if users or things:
            # handle pluralization of things (never pluralize users)
            thing_strings = []
            for key, itemlist in sorted(things.iteritems()):
                nitem = len(itemlist)
                if nitem == 1:
                    key, _ = itemlist[0].get_numbered_name(nitem, looker, key=key)
                else:
                    key = [item.get_numbered_name(nitem, looker, key=key)[1] for item in itemlist][0]
                thing_strings.append(key)

            string += "\n|wYou see:|n " + list_to_string(users + thing_strings)

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
        pass
        
    def at_before_get(self, getter, **kwargs):
        """
        Called by the default `get` command before this object has been
        picked up.
        Args:
            getter (Object): The object about to get this object.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).
        Returns:
            shouldget (bool): If the object should be gotten or not.
        Notes:
            If this method returns False/None, the getting is cancelled
            before it is even started.
        """
        return True

    def at_get(self, getter, **kwargs):
        """
        Called by the default `get` command when this object has been
        picked up.
        Args:
            getter (Object): The object getting this object.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).
        Notes:
            This hook cannot stop the pickup from happening. Use
            permissions or the at_before_get() hook for that.
        """
        pass


class Stash(Object):
    """
    This is a players personal stash.

    The stash gives objects a player tag and stores it in None.
    Objs taken from stash by the player are retrieved with the tag from none.
    """

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
        pass

    def at_before_get(self, getter, **kwargs):
        """
        Called by the default `get` command before this object has been
        picked up.
        Args:
            getter (Object): The object about to get this object.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).
        Returns:
            shouldget (bool): If the object should be gotten or not.
        Notes:
            If this method returns False/None, the getting is cancelled
            before it is even started.
        """
        return True

    def at_get(self, getter, **kwargs):
        """
        Called by the default `get` command when this object has been
        picked up.
        Args:
            getter (Object): The object getting this object.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).
        Notes:
            This hook cannot stop the pickup from happening. Use
            permissions or the at_before_get() hook for that.
        """
        pass
