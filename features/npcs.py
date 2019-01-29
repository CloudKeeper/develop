"""
NPCS - INOPERABLE

-Recurring NPCs
-NPCs by area.

"""

from typeclasses.characters import Character
from evennia.utils.evmenu import EvMenu


class Trainer(Character):
    """
    Typeclass for trainer characters.

    """

    def at_object_creation(self):
        """
        Called only once, when object is first created
        """
        super().at_object_creation()
        self.db.conversation =

    def at_talk(self, caller):
        """
        Called when obj targeted by a talk command.
        """

        # Response if parent has player or NPC has no conversation set.
        if self.has_player:
            caller.execute_cmd("Say Hi %s" % self.key)
            return

        if not self.db.conversation:
            caller.msg("%s appears too busy to talk right now." % self.key)
            return

        # Telegraph action to room.
        caller.location.msg_contents(caller.key + "speaks to " + self.key,
                                     exclude=caller)

        # Retrieve conversation stored on the object
        conversation = {}
        exec self.db.conversation

        EvMenu(caller, conversation, cmdset_mergetype="Replace",
               startnode="node1", cmdset_priority=1,
               cmd_on_exit="", npc=self)
