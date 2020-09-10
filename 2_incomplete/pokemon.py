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

# -----------------------------------------------------------------------------
#
# Party Handler
#
# -----------------------------------------------------------------------------


"""
Party handler module.

The `PartyHandler` provides an interface to manipulate a Trainer's party
whilst respecting the various hooks and calls required. The handler is
instantiated as a property on the Trainer typeclass, with the trainer passed
as an argument. It looks for the party and box properties in the Trainer's db
attributes handler to initialize itself and provide persistence.

Config Properties:
    list (list): List of current Pokemon objects in party.

Config Requirements:
    obj.db.party (list): List of current Pokemon objects in party.
    obj.db.box (list): List of Pokemon owned but not currently in party.

Setup:
    To use the PartyHandler, add it to a Trainer typeclass as follows:

    from typeclass.hander_party import PartyHandler
      ...
    @property
    def party(self):
        return PartyHandler(self)

Use:
    Health is added and subtracted using the `heal` and `dmg` methods or
    regular arithmetic operators.

Example usage:
    > self.party.list
    [<Pokemon>, <Pokemon>]
    > self.party.add(<Pokemon>)
    [<Pokemon>, <Pokemon>, <Pokemon>]
    > len(self.party)
    3
    > self.party.alive
    [<Pokemon>]
    > len(self.party.alive)
    1
    >self.party.fainted
    [<Pokemon>, <Pokemon>]

"""
from world.rules import calculate_health
from typeclasses.objects_pokemon import Pokemon


class PartyException(Exception):
    """
    Base exception class for HealthHandler.

        Args:
            msg (str): informative error message
    """
    def __init__(self, msg):
        self.msg = msg


class PartyHandler(object):
    """Handler for a characters health.

    Args:
        obj (Character): parent character object. see module docstring
            for character attribute configuration info.

    Properties
        party (list): Hold current party, up to 6 Pokemon.
        box (list): Holds the remainder of owners Pokemon.

    Methods:

        add (str): add a condition to the character's condition list.
        remove (str): remove a condition to the character's condition list.
    """

    def __init__(self, obj):
        """
        Save reference to the parent typeclass and check appropriate attributes

        Args:
            obj (typeclass): Pokemon typeclass.
        """
        self.obj = obj

        if not self.obj.attributes.has("party"):
            msg = '`PartyHandler` requires `db.party` attribute on `{}`.'
            raise PartyException(msg.format(obj))

        if not self.obj.attributes.has("box"):
            msg = '`PartyHandler` requires `db.box` attribute on `{}`.'
            raise PartyException(msg.format(obj))

    @property
    def list(self):
        """
        Returns current party.

        Returns:
            party (list): List of current Pokemon objects in party.

        Returned if:
            obj.party.list
        """
        return self.obj.db.party

    def __str__(self):
        """
        Returns current party.

        Returns:
            party (list): List of current Pokemon objects in party.

        Returned if:
            str(obj.party)
        """
        return ', '.join(pokemon.key for pokemon in self.obj.db.party)

    def __iter__(self):
        """
        Iterates through party.

        Returns:
            pokemon (<Pokemon>): Values of party iterated through.

        Returned if:
            for pokemon in obj.party
        """
        return self.obj.db.party.__iter__()

    def __len__(self):
        """
        Returns current party length.

        Returns:
            length (int): Number of Pokemon objects in current party.

        Returned if:
            len(obj.party)
        """
        return len(self.obj.db.party)

    @property
    def alive(self):
        """
        Returns live Pokemon in current party.

        Returns:
            party (list): List of current alive Pokemon objects in party.

        Returned if:
            obj.party.alive
        """
        return [pokemon for pokemon in self.obj.db.party if pokemon.health]

    @property
    def fainted(self):
        """
        Returns fainted Pokemon in current party.

        Returns:
            party (list): List of current fainted Pokemon objects in party.

        Returned if:
            obj.party.fainted
        """
        return [pokemon for pokemon in self.obj.db.party if not pokemon.health]

    @property
    def box(self):
        """
        Returns Pokemon in box.

        Returns:
            box (list): List of Pokemon objects stored in box.

        Returned if:
            obj.party.box
        """
        return self.obj.db.box

    def add(self, pokemon):
        """
        Add Pokemon to party. If at party maximum, Pokemon will be sent to box.

        Returns:
            True (Boolean): Pokemon was added to party successfully.
            False (Boolean): Pokemon was sent to box.

        Returned if:
            obj.party.add(<Pokemon>)
        """
        if len(self.obj.db.party) < 6:
            self.obj.db.party.append(pokemon)
            return True
        else:
            self.obj.db.box.append(pokemon)
            return False

    def __add__(self, pokemon):
        """
        Add Pokemon to party. If at party maximum, Pokemon will be sent to box.

        Returns:
            True (Boolean): Pokemon was added to party successfully.
            False (Boolean): Pokemon was sent to box.

        Returned if:
            obj.party + <Pokemon>
        """
        if len(self.obj.db.party) < 6:
            self.obj.db.party.append(pokemon)
            return True
        else:
            self.obj.db.box.append(pokemon)
            return False

    def remove(self, pokemon):
        """
        Remove Pokemon from party. If party would equal zero it fails.

        Returns:
            True (Boolean): Pokemon was removed from party successfully.
            False (Boolean): Pokemon could not be removed.

        Returned if:
            obj.party.remove(<Pokemon>)
        """
        if len(self.obj.db.party) > 1:
            self.obj.db.party.remove(pokemon)
            return True
        else:
            return False

    def __sub__(self, pokemon):
        """
        Remove Pokemon from party. If party would equal zero it fails.

        Returns:
            True (Boolean): Pokemon was removed from party successfully.
            False (Boolean): Pokemon could not be removed.

        Returned if:
            obj.party - <Pokemone>
        """
        if len(self.obj.db.party) > 1:
            self.obj.db.party.remove(pokemon)
            return True
        else:
            return False

    def swap(self, pokemon1, pokemon2):
        """
        Swap Pokemon positions within party.

        Returns:

        Returned if:
            obj.party.swap(<Pokemon>, <Pokemon>)
        """
        party = self.list
        pokemon1, pokemon2 = party.index(pokemon1), party.index(pokemon2)
        party[pokemon2], party[pokemon1] = party[pokemon1], party[pokemon2]

    def cast(self, pokemon, quiet=False):
        """
        Choose a Pokemon to let out of it's Pokeball.

        Returns:

        Returned if:
            obj.party.cast(<Pokemon>)
        """
        pokemon.move_to(self.obj.location, quiet=True)
        if not quiet:
            self.obj.location.msg_contents(
                pokemon.key + " was released from it's "
                + pokemon.db.pokeball + ".")

    def recall(self, pokemon, quiet=False):
        """
        Choose a Pokemon to return to it's Pokeball.

        Returns:

        Returned if:
            obj.party.retrieve(<Pokemon>)
        """
        pokemon.move_to(None, to_none=True)
        if not quiet:
            self.obj.location.msg_contents(
                pokemon.key + " was returned to it's "
                + pokemon.db.pokeball + ".")

    # release

    def __nonzero__(self):
        """
        Support Boolean comparison for living party members.

        Returns:
            Boolean: True if living party members, False if none.

        Returned if:
            if obj.party
        """
        return bool(self.alive)

    def __eq__(self, value):
        """
        Support equality comparison for party length.

        Returns:
            Boolean: True if equal, False if not.

        Returned if:
            obj.party == 5
        """
        if isinstance(value, int):
            return len(self.obj.db.party) == value
        else:
            return NotImplemented

    def __ne__(self, value):
        """
        Support non-equality comparison for party length.

        Returns:
            Boolean: True if not equal, False if equal.

        Returned if:
            obj.party != 5
        """
        if isinstance(value, int):
            return len(self.obj.db.party) != value
        else:
            return NotImplemented

    def __lt__(self, value):
        """
        Support less than comparison for party length.

        Returns:
            Boolean: True if less than, False if not.

        Returned if:
            obj.heatlh < 5
        """
        if isinstance(value, int):
            return len(self.obj.db.party) < value
        else:
            return NotImplemented

    def __le__(self, value):
        """
        Support less than or equal to comparison for party length.

        Returns:
            Boolean: True if less than or equal, False if not.

        Returned if:
            obj.party <= 5
        """
        if isinstance(value, int):
            return len(self.obj.db.party) <= value
        else:
            return NotImplemented

    def __gt__(self, value):
        """
        Support greater than comparison for party length.

        Returns:
            Boolean: True if greater than, False if not.

        Returned if:
            obj.party > 5
        """
        if isinstance(value, int):
            return len(self.obj.db.party) > value
        else:
            return NotImplemented

    def __ge__(self, value):
        """
        Support greater than or equal to comparison for party length.

        Returns:
            Boolean: True if greater than or equal, False if not.

        Returned if:
            obj.party >= 5
        """
        if isinstance(value, int):
            return len(self.obj.db.party) >= value
        else:
            return NotImplemented
