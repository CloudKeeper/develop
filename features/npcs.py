"""
NPCS - INOPERABLE

-Recurring NPCs
-NPCs by area.

"""

from typeclasses.characters import Character
from evennia.utils.evmenu import EvMenu


class EvMenuNPC(Character):
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


"""
Example BatchCode

npc = create_object(npcs.EvMenuNPC, key="NPC", location=caller.location)
npc.db.desc = "This is a test NPC."
npc.db.conversation = ""
def node1(caller):
    text = "Hi. I'm a test NPC!"
    options = None
    return utils_text.nobordertext(text, "Lab Aide"), options

conversation = {"node1": node1}
""


More Advanced Example

agent = create_object(npcs.EvMenuNPC, key="NPC", location=caller.location)
agent.db.desc = "A well dressed business man."
agent.db.conversation = ""
def node1(caller):
    if caller.location in caller.db.property_owned:
        text = ("I hope you're enjoying your apartment!..")
        return utils_text.nobordertext(text, "Agent"), None

    text = ("Would you like your very own apartment?.. [Y/N]")
    options = {"key": "_default",
               "goto": "node2"}
    return utils_text.nobordertext(text, "Agent"), options

def node2(caller, raw_string):
    if raw_string not in ["yes", "y"]:
        text = ("Perhaps next time!")
        return utils_text.nobordertext(text, "Agent"), None

    from evennia import create_object
    from typeclasses import rooms_apartments, exits
    
    room = create_object(Apartment, key=caller.key+"'s Room", location=None)
    room.db.owner = caller
    caller.db.property_owned[caller.location] = room

    text = ("Here you go..")
    options = {"key": "_default",
               "goto": "node3"}
    return utils_text.nobordertext(text, "Agent"), None

conversation = {"node1": node1,
                "node2": node2}
""

"""