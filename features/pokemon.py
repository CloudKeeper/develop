"""
Pokemon - INOPERABLE

#Typeclass
-Pokemon Object
-create commands

#Obtaining Pokemon
-Pokeball Object
-Pokemon Trading

#Team Management
-Computer
-Team Menu
"""
from typeclasses.objects import Object


# -----------------------------------------------------------------------------
#
# Pokemon Typeclass
#
# -----------------------------------------------------------------------------

class Pokemon(Object):
    """
    Typeclass for the Pokemon Object.
    """
    pass

# -----------------------------------------------------------------------------
#
# Obtaining Pokemon
#   -Use Command
#   -PokeBall
#
# -----------------------------------------------------------------------------

class CmdUse(COMMAND_DEFAULT_CLASS):
    """
    Use an object

    Usage:
        use <obj> [on <target>] =['say message][:pose message][:'say message]

    The command takes inspiration by the use command and hooks in the Muddery
    Evennia project. The command is used on items in the characters inventory.
    The command simply sanity checks arguments before calling the objects
    use_object() function. A string is returned by the function which is then
    passed on to the character.

    ** at this stage only in your inventory.
    """
    key = "use"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        """Use an object."""

        # Set up function variables.
        caller = self.caller
        args = self.lhs.split("on")
        obj = args[0].strip() if len(args) >= 1 else None
        target = args[1].strip() if len(args) > 1 else None
        rplist = self.rhs.split(":") if self.rhs else None

        # Find and confirm suitability of obj.
        if not obj:
            caller.msg("Use what?")
            return

        obj = caller.search(obj)
        if not obj:
            return

        if not getattr(obj, "use_object", None):
            caller.msg("You cannot use this object.")
            return

        # If target given: find target.
        if target:
            target = caller.search(target,
                                   nofound_string=_TGT_ERRMSG.format(target))
            if not target:
                return

        # Handle roleplay entries.
        if rplist:
            for text in rplist:
                if text[0] in ["'"]:
                    caller.execute_cmd("Say " + text[1:])
                else:
                    caller.execute_cmd("Pose " + text)

        # Call use_object hook on object.
        obj.use_object(caller, target)



















