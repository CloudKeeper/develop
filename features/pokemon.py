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
from typeclasses.objects import Object, Character
from evennia.utils import lazy_property
import random

# -----------------------------------------------------------------------------
#
# Trainer Typeclass
#
# -----------------------------------------------------------------------------


class Trainer(Character):
    """
    Typeclass for trainer characters.
    """
    @lazy_property
    def party(self):
        """Handler for Pokemon Party."""
        return PartyHandler(self)

    def at_object_creation(self):
        """
        Called only once, when object is first created
        """
        super(Trainer, self).at_object_creation()

        # Values for the PartyHandler
        self.db.party = []  # [<Pokemon>, <Pokemon>]
        self.db.box = []  # [<Pokemon>, <Pokemon>]

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

        # Only allow use of objects in your inventory.
        obj = caller.search(obj, location=caller)
        if not obj:
            return

        if not getattr(obj, "at_use", None):
            caller.msg("You cannot use this object.")
            return

        # If target given: find target.
        if target:
            target = caller.search(target)  # TO DO Add Pokemon in your party.
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
        obj.at_use(caller, target)


class Pokeball(Object):
    """

    """
    def at_use(self, caller, target, quiet=False):
        """

        """
        # Assist Functions.

        def calculate_catch(count):
            """

            """
            value = random.randint(0, 65535)
            if value >= breakout_value:
                caller.location.msg_contents(target.key + " broke free!")
                caller.msg(fail_msg[count])
                return
            else:
                if count == 3:
                    successful_catch()
                    return
                else:
                    caller.location.msg_contents(random.choice(shake_msg).
                                                 format(self.key))
                    utils.delay(3, calculate_catch, count+1)

            # -----------------------------------------------------------------

        def successful_catch():
            """

            """
            caller.party.add(target)
            target.location = None
            target.db.trainer = caller
            target.db.pokeball = self.key
            target.db.owner.insert(0, caller)

            caller.msg("You caught %s." % target.name)
            caller.location.msg_contents("%s caught %s." % (caller.name,
                                                            target.name),
                                         exclude=caller)
            self.delete()
            # -----------------------------------------------------------------

        # Game Messages
        caller.msg("You throw a %s at %s." % (self.key, target.key))
        msg = "%s throws a %s at %s." % (caller.key, self.key, target.key)
        caller.location.msg_contents(msg, exclude=caller)
        msg = "The %s contacts %s with a flash of red light." % (self.key, target.key)
        caller.location.msg_contents(msg)

        # Fail if target not Pokemon or Pokemon has owner.
        if not isinstance(target, Pokemon) or target.db.trainer:
            caller.location.msg_contents("The %s fails!" % self.key)
            caller.msg("You return the %s to your inventory." % self.key)
            return

        # Calculate if immediately captured.
        if self.key in ["Masterball"]:
            successful_catch()
            return

        # catch_rate = rules.calculate_catchrate(target)
        catch_rate = random.randint(255, 259)

        if catch_rate >= 255:
            successful_catch()
            return

        # Otherwise calculate if Pokemon breaks out of Pokeball
        # breakout_value = rules.calculate_wobblerate(catch_rate)
        breakout_value = random.randint(32765, 32769)

        shake_msg = ["The {} shakes violently!",
                     "The {} wobbles from side to side!",
                     "The {} shudders harshly!",
                     "The {} strains to keep closed!"]

        fail_msg = ["Oh no! The Pokemon broke free!",
                    "Aww! It appeared to be caught!",
                    "Aargh! Almost had it!",
                    "Shoot! It was so close, too!"]

        utils.delay(3, calculate_catch, 0)

