"""
Places - NEEDS TESTING

CloudKeeper

Places are objects that create areas that players can join and take part in 
convrsations with other joinees in a larger room. It does not restrict a 
players ability to take part in the larger room.

Places are interacted with by a command based on the objects name - like exits.

Examples:
    place/join Hi Guys!
        >Player joins the Place
        >Player says to group, "Hi Guys!"
    place How are you?
        >Player says to group, "How are you?"
    place/leave Bye Guys!
        >Player says to group, "Bye Guys!"
        >Player leaves the group
    place/join/leave I just want to tell you both good luck. We're all counting on you.
        >Player joins the Place
        >Player says to the group, "I just want to tell you both good luck. We'reall counting on you."
        >Player leaves the Place

Expansion:
-SET A PLAYER LIMIT
-look at place give you a list of the occupants.
-Using an exit wipes you from places.
"""
from evennia.commands.default.muxcommand import MuxCommand
from evennia.commands.cmdset import CmdSet
from evennia.utils import evtable, create
from typeclasses.objects import Object
from django.conf import settings
from evennia.utils import search

_DEFAULT_WIDTH = settings.CLIENT_DEFAULT_WIDTH


class PlaceCommand(MuxCommand):
    """
    Speak only to players who have 'joined' the 'Place' object.

    Usage:
        place[/switch] <message>

    Examples:
        place/join Hi Guys!
            >Player joins the Place
            >Player says to group, "Hi Guys!"
        place How are you?
            >Player says to group, "How are you?"
        place/leave Bye Guys!
            >Player says to group, "Bye Guys!"
            >Player leaves the group

    Swtich:
        /join - Recieve messages being spoken in the 'place'.
        /leave - Stop receiving messages spoken in the 'place'.

    """
    obj = None

    def func(self):
        """Implement Function"""
        caller = self.caller
        place = self.obj
        occupants = place.db.occupants

        if 'join' in self.switches:
            place.join_occupants(caller)

        # Catch non-occupant messages
        if caller not in occupants:
            caller.msg("You are not able to join the conversation at the moment.")
            return

        # Send message to occupants.
        if self.args:
            place.say_to_occupants(caller, self.args)

        if 'leave' in self.switches:
            place.leave_occupants(caller)



class PlaceObj(Object):
    """
    The Place object acts as a localised channel, allowing players to join,
    listen to and contribute to the conversation of the subscribers.

    The join, say and leave messages are stored on the Place so that they
    can be configured by builders to match the aesthetic of the Place.
    """
    place_command = PlaceCommand
    priority = 101

    lockstring = "get:false()"
    occupants = []

    join_feedback = "You have joined the %s"
    join_msg = "%s has joined the %s"
    say_feedback = 'You say to the group, "%s"'
    say_msg = '%s says to the group, "%s"'
    leave_feedback = "You have left the %s"
    leave_msg = "%s has left the %s"

    def join_occupants(self, caller):
        """Called when a player joins the 'place'"""
        # Remove caller from other spaces
        for place in [place for place in caller.location.contents
                      if place.is_typeclass(PlaceObj)]:
            if caller in place.db.occupants:
                place.leave_occupants(caller)

        # Add caller to occupants and alert occupants.
        caller.msg(self.join_feedback % self.key)
        self.message_occupants(self.join_msg % (caller.key, self.key))
        self.occupants.append(caller)

    def say_to_occupants(self, caller, msg):
        """Speak to occupants of 'place'"""
        # Give feedback to caller and prep message to occupants.
        caller.msg(self.say_feedback % msg)
        self.message_occupants(self.say_msg % (caller.key, msg), exclude=[caller])

    def message_occupants(self, msg, exclude=[]):
        """Called to message all occupants of 'place'"""
        # Remove stale occupants and exclude specified.
        for occupant in self.db.occupants:
            if not occupant.location == self.location:
                self.db.occupants.remove(occupant)
            if occupant not in exclude:
                occupant.msg(msg)

    def leave_occupants(self, caller):
        """Called when a player leaves a 'place'"""

        self.db.occupants.remove(caller)
        caller.msg(self.leave_feedback % self.key)
        self.message_occupants(self.leave_msg % (caller.key, self.key))

    # Place Cmd Set up Functions.
    def create_place_cmdset(self, exidbobj):
        """
        Helper function for creating an exit command set + command.
        The command of this cmdset has the same name as the Exit
        object and allows the exit to react when the account enter the
        exit's name, triggering the movement between rooms.
        Args:
            exidbobj (Object): The DefaultExit object to base the command on.
        """

        # create the place command. We give the properties here,
        # to always trigger metaclass preparations
        cmd = self.place_command(key=exidbobj.db_key.strip().lower(),
                                 aliases=exidbobj.aliases.all(),
                                 locks=str(exidbobj.locks),
                                 auto_help=False,
                                 destination=exidbobj.db_destination,
                                 arg_regex=r"^$",
                                 is_exit=True,
                                 obj=exidbobj)
        # create a cmdset
        exit_cmdset = CmdSet(None)
        exit_cmdset.key = 'PlaceCmdSet'
        exit_cmdset.priority = self.priority
        exit_cmdset.duplicates = True
        # add command to cmdset
        exit_cmdset.add(cmd)
        return exit_cmdset

    def at_cmdset_get(self, **kwargs):
        """
        Called just before cmdsets on this object are requested by the
        command handler. If changes need to be done on the fly to the
        cmdset before passing them on to the cmdhandler, this is the
        place to do it. This is called also if the object currently
        has no cmdsets.
        Kwargs:
          force_init (bool): If `True`, force a re-build of the cmdset
            (for example to update aliases).
        """

        if "force_init" in kwargs or not self.cmdset.has_cmdset("PlaceCmdSet", must_be_default=True):
            # we are resetting, or no exit-cmdset was set. Create one dynamically.
            self.cmdset.add_default(self.create_place_cmdset(self), permanent=False)

    def at_init(self):
        """
        This is called when this objects is re-loaded from cache. When
        that happens, we make sure to remove any old ExitCmdSet cmdset
        (this most commonly occurs when renaming an existing exit)
        """
        self.cmdset.remove_default()

###############################################################################
#
# Builder Commands
#
###############################################################################


class CmdPlace(MuxCommand):
    """
    Create places to share private conversations within a location.
    Deleting and Describing Places after creation is handled by the
    @del and @desc respectively.

    Usage:
        @place[/create] <objname>[, alias, alias...][= desc]

    """
    key = "@place"
    switch_options = "create"
    help_category = "Building"
    locks = "cmd:perm(create) or perm(Builder)"

    def func(self):
        """Implement function"""
        caller = self.caller

        # SWITCHES ------------------------------------------------------------
        # @place/create <objname>[, alias, alias...][= desc]
        if 'create' in self.switches:

            # Handle improper use.
            if not self.args:
                string = "Usage: @place/create <objname>[, alias, alias...][= desc]"
                caller.msg(string)
                return

            # Parse arguments
            key = self.lhslist.pop(0)
            aliases = self.lhslist
            desc = self.rhs

            # Prevent repeats
            if caller.search(key):
                caller.msg("Object with name '%s' already exists." % key)
                return

            # Create Object
            place = create.create_object(PlaceObj, key, caller.location,
                                         aliases=aliases)
            place.db.desc = desc if desc else "A place to talk with others."

            # Message Caller
            if aliases:
                string = "You create a new Place: %s (aliases: %s)."
                string = string % (key, ", ".join(aliases))
            else:
                string = "You create a new Place: %s."
                string = string % place.name
            caller.msg(string)
            return

        # NO SWITCHES ---------------------------------------------------------
        # @place <Ignored>  # Return list of places at current location.
        places = [place for place in caller.location.contents
                  if place.is_typeclass(PlaceObj)]
        if not places:
            caller.msg("No Places available.")
            return

        # If Places located: Organise EvTable for display
        table = evtable.EvTable("|wplace|n", "|waliases|n",
                                "|wdescription|n", maxwidth=_DEFAULT_WIDTH)
        for place in places:
            clower = place.key.lower()
            aliases = place.aliases.all()
            table.add_row(*["%s%s" % clower,
                            "%s" % ",".join(aliases),
                            place.db.desc])
        table.reformat_column(0, width=9)
        table.reformat_column(3, width=14)

        # Send table to player
        caller.msg("\nAvailable Places:\n%s" % table)
