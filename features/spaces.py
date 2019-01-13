"""
Spaces - INOPERABLE

-Character Mixin
-Exit Obj
-Room Mixin
-Design Menu

picture a fireplace in a room. Those sitting at the fireplace are having a
conversation but that conversation isn't passed to everyone in the room. Just
those sitting at the fireplace

Apparently it's a very standard mush feature - it was something Apostate
asked me to implement very early on. Places/tabletalk, that is.

It's known as many different names across the hobby, I've known it as
"locations" or "sublocations" before.

So I was thinking an object with a "sit" command, that when you sit it
replaces your say and pose commands with a custom one.

Some consider using dicts in Attributes but I've also seen people using
coordinate systems inside the room or even to use rooms-within-rooms.

Thinking outloud. If the say command is on the fireplace, you could save
putting any attributes on the player because the cmd.object would be the
fireplace

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
from evennia.commands import cmdset, command
from evennia.utils import utils
COMMAND_DEFAULT_CLASS = utils.class_from_module(settings.COMMAND_DEFAULT_CLASS)


class CmdSpace(COMMAND_DEFAULT_CLASS):
    """
    Create and delete spaces
    """

    key = "@space"
    locks = "cmd:perm(home) or perm(Builder)"
    arg_regex = r"$"

    def func(self):
        """
        Default exit traverse if no syscommand is defined.
        """
        # If no args return list of places & Usage
        if not self.args:
            pass

        # Switch options available
        if self.switches:
            # @space/create <place> [, alias, alias]
            if "create" in self.switches:
                pass

            # @space/delete <place>
            elif "delete" in self.switches:
                pass

            # Invalid switches: Return usage
            else:
                pass

        # Handle everything else as a message.
        pass

def create_place(object, name="Campfire", aliases=[], locks=None):
    """

    """
    cmd = PlaceCommand(key=name.strip().lower(),
                       aliases=[alias.strip().lower() for alias in aliases],
                       locks=locks,
                       auto_help=False,
                       obj=object)
    # create a cmdset
    exit_cmdset = cmdset.CmdSet(None)
    exit_cmdset.key = 'ExitCmdSet'
    exit_cmdset.priority = 100
    exit_cmdset.duplicates = True
    # add command to cmdset
    exit_cmdset.add(cmd)

    object.cmdset.add_default(PlaceCommand(self), permanent=True)


class PlaceCommand(COMMAND_DEFAULT_CLASS):
    """
    allows usage of a space
    """
    obj = None

    def func(self):
        """
        Default exit traverse if no syscommand is defined.
        """
        # If no args return usage.
        if not self.args:
            pass

        # Switch options available
        if self.switches:
            # <placekey>/join <place>
            if "join" in self.switches:
                pass

            # <placekey>/quit <place>
            elif "quit" in self.switches:
                pass

            # Invalid switches: Return Usage
            else:
                pass

        # Handle everything else as a message.
        pass

def delete_place(place):
    """

    """
    pass
