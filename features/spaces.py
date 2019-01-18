"""
Spaces - NEEDS TESTING

FEAATURES:
-SET A PLAYER LIMIT

-Character Mixin
-Exit Obj
-Room Mixin
-Design Menu

I suppose one could add  to the extended_room contrib with that kind of
functionality. My main reason for not doing so was always that in MUDs,
locations/places can depend quite a bit on your game system - should you be
able to evesdrop etc? Is what you hear based on your skills somehow etc? But
maybe it could still be implemented in a somewhat more general form.

My implementation for Places was a typeclass that has a cmdset for tabletalk,
joining the place, and leaving it. It doesn't replace or suppress any existing
commands, since it seems common that tabletalk basically becomes an impromptu
private channel for a few people during a large event, pretty much like people
using whisper with multiple targets. I do think it could be easily done as
channels, or any number of other implementations

so the tabletalk command literally sits on a table in the room that people
then use to communicate - that is, they need to write 'tabletalk <text>' to
communicate to others around the table?
It's really no different than just a multi-whisper, I just formatted it a
little differently. It probably would have made more sense to implement it as
a channel typeclass, though

you get alternative say/emote etc commands that only reroute outputs to the
others around the 'table'.

it just sends a msg to each person at the table, more or less the same way
whisper does. I think a channel typeclass would probably be a more elegant
implementation though

21:24 <Griatch> Tehom, I think I like your take on tabletalk better. If one
wanted to make it more complex, the 'tabletalk' command could add a new cmdset
to you with new implementations of say/emote etc that redirects outputs only to
your location.
"""
###############################################################################
# CmdPlace - Place Listing/Describing/Creating/Deleting Command.
###############################################################################
from evennia.commands.default.muxcommand import MuxCommand
from evennia.commands.cmdset import CmdSet
from evennia.utils import evtable, create
from typeclasses.objects import Object
from django.conf import settings

_DEFAULT_WIDTH = settings.CLIENT_DEFAULT_WIDTH


class CmdPlace(MuxCommand):
    """
    create new objects
    Usage:
        @place/create <objname>[, alias, alias...][= desc]"

    Command Description
        @place
    """
    key = "@place"
    switch_options = ("create", "desc", "del")
    help_category = "Building"
    locks = "cmd:perm(create) or perm(Builder)"

    def func(self):
        """Implement function"""
        # Prepare common values.
        caller = self.caller
        places = [place for place in caller.location.content
                  if place.is_typeclass(PlaceObj)]

        if not self.switches:
            """
            
            """
            # Handle no Places located.
            if not places:
                self.msg("No channels available.")
                return

            # Organise EvTable for display
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
            self.msg("\nAvailable channels:\n%s" % table)

        elif 'create' in self.switches:
            """
            create new objects
            Usage:
                @place/create <objname>[, alias, alias...][= desc]

            Command Description
                @place/create fireplace, fire
            """
            # Handle improper use.
            if not self.args:
                string = "Usage: @place/create <objname>[, alias, alias...][= desc]"
                caller.msg(string)
                return

            # Parse arguments
            key = self.lhslist.pop(0)
            aliases = self.lhslist
            desc = self.rhs

            # Create Object
            place = create.create_object(PlaceObj, key, caller.location,
                                         aliases=aliases)
            place.db.desc = desc if desc else "A place to talk with others."

            # Message Player
            if aliases:
                string = "You create a new Place: %s (aliases: %s)."
                string = string % (key, ", ".join(aliases))
            else:
                string = "You create a new Place: %s."
                string = string % place.name
            caller.msg(string)

        elif 'desc' in self.switches:
            """

            """
            # Handle improper use.
            if not self.args:
                string = "Usage: @place/desc <objname> = desc"
                caller.msg(string)
                return

            # Parse arguments
            place = caller.search(self.lhs, candidates=places)
            if not place:
                string = "Target '" + self.lhs + "' could not be located."
                caller.msg(string)
                return
            desc = self.rhs or ''

            # Update object description.
            if place.access(self.caller, 'control') or \
                    place.access(self.caller, 'edit'):
                place.db.desc = desc
                caller.msg("The description was set on %s." %
                           place.get_display_name(caller))
            else:
                caller.msg("You don't have permission to edit the description "
                           "of %s." % place.key)

        elif 'del' in self.switches:
            """

            """
            # Handle improper use.
            if not self.args:
                string = "Usage: @place/desc <objname> = desc"
                caller.msg(string)
                return

            # Parse arguments
            place = caller.search(self.lhs, candidates=places)
            if not place:
                string = "Target '" + self.lhs + "' could not be located."
                caller.msg(string)
                return

            # Delete object.
            if place.access(self.caller, 'control') or \
                    place.access(self.caller, 'edit'):
                place.delete()
                caller.msg("The description was set on %s." %
                           place.get_display_name(caller))
            else:
                caller.msg("You don't have permission to delete the "
                           "place: %s." % place.key)


class PlaceCommand(MuxCommand):
    """

    """
    obj = None

    def message_occupants(self, msg):
        """

        """
        for occupant in self.obj.db.occupants:
            if occupant.location == self.obj.location:
                occupant.msg(msg)
            else:
                self.obj.db.occupants.remove(occupant)

    def func(self):
        """

        """
        caller = self.caller
        place = self.obj
        occupants = place.db.occupants

        if not self.switches:
            """

            """
            # Handle non-occupant messages
            if caller not in occupants:
                self.msg("To contribute to the conversation you must join "
                         "the " + place.key)
                self.message_occupants(caller.key + " attempts to speak "
                                       "from elsewhere but his words are not "
                                       "heard.")
                return

            # Send message to occupants.
            msg = caller.key + " says to the group, '" + self.args + "'."
            self.message_occupants(msg)

        elif 'join' in self.switches:
            """
            
            """
            # Add caller to occupants and alert occupants.
            occupants.append(caller)
            caller.msg("You have joined the " + place.key)
            self.message_occupants(caller.key + "has joined the " + place.key)

            # Send message to occupants.
            if self.args:
                msg = caller.key + " says to the group, '" + self.args + "'."
                self.message_occupants(msg)

        elif 'leave' in self.switches:
            """

            """
            # Send message to occupants.
            if self.args:
                msg = caller.key + " says to the group, '" + self.args + "'."
                self.message_occupants(msg)

            # Remove caller from occupants and alert occupants.
            occupants.remove(caller)
            caller.msg("You have left the " + place.key)
            self.message_occupants(caller.key + "has left the " + place.key)


class PlaceObj(Object):
    """

    """

    place_command = PlaceCommand
    priority = 101

    lockstring = "get:false()"
    occupants = []

    # Helper classes and methods to implement the Exit. These need not
    # be overloaded unless one want to change the foundation for how
    # Exits work. See the end of the class for hook methods to overload.

    def create_place_cmdset(self, exidbobj):
        """
        Helper function for creating an exit command set + command.
        The command of this cmdset has the same name as the Exit
        object and allows the exit to react when the account enter the
        exit's name, triggering the movement between rooms.
        Args:
            exidbobj (Object): The DefaultExit object to base the command on.
        """

        # create an exit command. We give the properties here,
        # to always trigger metaclass preparations
        cmd = self.exit_command(key=exidbobj.db_key.strip().lower(),
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

    # Command hooks

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
            self.cmdset.add_default(self.create_exit_cmdset(self), permanent=False)

    def at_init(self):
        """
        This is called when this objects is re-loaded from cache. When
        that happens, we make sure to remove any old ExitCmdSet cmdset
        (this most commonly occurs when renaming an existing exit)
        """
        self.cmdset.remove_default()
