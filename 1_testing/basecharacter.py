"""
This provides the fundemental functionality that all other features assume.

The file contains the base object class with new base hooks:
    return_appearance
    at_read
    at_use
    at_smell
    
The file contains the base commands which utilise these hooks.

"""
from evennia.utils.utils import class_from_module
from django.conf import settings
from evennia import CmdSet, DefaultObject
COMMAND_DEFAULT_CLASS = class_from_module(settings.COMMAND_DEFAULT_CLASS)

# ----------------------------------------------------------------------------
# 
# Reference CmdSet & Typeclass
# 
# These contain all the commands and hooks.
# 
# ----------------------------------------------------------------------------

# class BaseCmdSet

# class BaseObjectMixin


# ----------------------------------------------------------------------------
# 
# at_use() and use command.
# 
# These contain all the commands and hooks.
# 
# ----------------------------------------------------------------------------


class CmdUse(COMMAND_DEFAULT_CLASS):
    """
    Use an object with the at_use() hook.

    Usage:
        use <obj> [on <target>, <target>] =['say message][:pose message][:'say message]

    The command simply sanity checks arguments before calling the objects
    at_use() function.
    """
    key = "use"
    aliases = ["read"]
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        """Use an object."""

        # Set up function variables.
        caller = self.caller
        args = self.lhs.split("on")
        obj = args[0].strip() if len(args) >= 1 else None
        targets = [arg.strip() for arg in args[1](",")] if len(args) > 1 else None

        # No target
        if not obj:
            caller.msg("Use what?")
            return

        # Can't find target
        obj = caller.search(obj)
        if not obj:
            return

        # Unsuitable target
        if not getattr(obj, "at_use", None):
            caller.msg("You cannot use this object.")
            return

        # If targets given: find targets.
        if targets:
            subjectlist = []
            for target in targets:
                subject = self.caller.search(target)
                if not subject:
                    caller.msg("'{}' could not be located.".format(target))
                    return
                subjectlist.append(subject)

        # Handle roleplay
        if self.rhs:
            _roleplay(self, caller, self.rhs.split(":"))

        # Call use_object hook on object.
        obj.at_use(caller, subjectlist)


class Object_at_use(DefaultObject):

    def at_use(self, caller, targets=[], quiet=False):
        """
        Triggered by the 'use' command used on this object.
        """
        pass


# ----------------------------------------------------------------------------
# 
# at_read() and read command.
# 
# These contain all the commands and hooks.
# 
# ----------------------------------------------------------------------------


class CmdRead(COMMAND_DEFAULT_CLASS):
    """
    Read an object

    Usage:
        read <obj> = ['say message][:pose message][:'say message]

    The command simply sanity checks arguments before calling the objects
    at_read() function.

    ** at this stage only in your inventory.
    """
    key = "use"
    aliases = ["read"]
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        """Use an object."""

        # Set up function variables.
        caller = self.caller
        obj = self.lhs
        rplist = self.rhs.split(":") if self.rhs else None

        # Find and confirm suitability of obj.
        if not obj:
            caller.msg("Read what?")
            return

        obj = caller.search(obj)
        if not obj:
            return

        if not getattr(obj, "at_read", None):
            caller.msg("You cannot read that object.")
            return

        # Handle roleplay
        if self.rhs:
            _roleplay(self, caller, self.rhs.split(":"))

        # Call use_object hook on object.
        obj.at_read(caller)
        
        
class Object_at_read(DefaultObject):

    def at_read(self, caller):
        """
        Triggered by the 'read' command used on this object.
        """
        pass


# ----------------------------------------------------------------------------
# 
# Reference CmdSet & Typeclass
# 
# These contain all the commands and hooks.
# 
# ----------------------------------------------------------------------------

class BaseCmdSet(CmdSet):
    """CmdSet for base commands."""
    key = "basecmdset"
    priority = 1

    def at_cmdset_creation(self):
        self.add(CmdUse())


class BaseObjectMixin(Object_at_use, Object_at_read):
    """
    The

    """
    pass


# ----------------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------------


def _roleplay(self, caller, actions):
    """
    Causes the caller to enact a number of roleplay actions.

    Args:
        caller (Account): The account which will act the roleplay actions.
        actions (List): The actions to be undertaken.
                        Strings starting with ' will be say messages.
                        Strings without ' will be emotes/poses.
                        eg. ["'Nice to meet you!", "Bows gracefully"]
    """
    for action in actions:
        if action[0] in ["'"]:
            caller.execute_cmd("Say " + action[1:])
        else:
            caller.execute_cmd("Pose " + action)
