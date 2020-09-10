"""
NPCS - INOPERABLE

-Recurring NPCs
-NPCs by area.

"""

from typeclasses.characters import Character
from evennia.utils.evmenu import EvMenu

# -----------------------------------------------------------------------------
#
# Talk Command
#
# -----------------------------------------------------------------------------


class CmdTalk(COMMAND_DEFAULT_CLASS):
    """
    Talk to a NPC. Triggers the corresponding objects at_talk hook.

    Usage:
        talk <obj> =['say message][:pose message][:'say message]
    """
    key = "talk"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        """Talk to an Character."""

        # Set up function variables.
        caller = self.caller
        rplist = self.rhs.split(":") if self.rhs else None

        # Find and confirm suitability of target.
        if not self.args:
            caller.msg("Talk to whom?")
            return

        target = caller.search(self.args, typeclass=EvMenuNPC,
                               nofound_string="You cannot talk to {}.".format(self.args))
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
        target.at_talk(caller)

# -----------------------------------------------------------------------------
#
# Conversation NPC
#
# -----------------------------------------------------------------------------


class EvMenuNPC(Character):
    """
    Typeclass for trainer characters.

    """

    def at_object_creation(self):
        """
        Called only once, when object is first created
        """
        super().at_object_creation()
        self.db.conversation = None

    def at_talk(self, caller):
        """
        Called when obj targeted by a talk command.
        """

        # Response if I have a player or I have no conversation set.
        if self.has_player:
            caller.execute_cmd("Say Hi %s" % self.key)
            return

        if not self.db.conversation:
            caller.msg("%s appears too busy to talk right now." % self.key)
            return

        # Telegraph action to room.
        caller.location.msg_contents("%s speaks to %s." % (caller.key, self.key),
                                     exclude=caller)

        # Conversation is either a dictionary or EvMenu object.
        EvMenu(caller, self.db.conversation, cmdset_mergetype="Replace",
               startnode="node1", cmdset_priority=1,
               cmd_on_exit="", npc=self)

# -----------------------------------------------------------------------------
#
# Conversation Nodes
#
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#
# Example Functionality
#
# -----------------------------------------------------------------------------


"""
# Example BatchCode

npc = create_object(npcs.EvMenuNPC, key="NPC", location=caller.location)
npc.db.desc = "This is a test NPC."
npc.db.conversation = {"node1": lambda caller: ("Hi. I'm a test NPC!", ({}))}

"""
