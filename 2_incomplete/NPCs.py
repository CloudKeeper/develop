"""
Talking NPCs and Vendors.

To use:
Add from features import NPCs to default_cmdsets
Add self.add(NPCs.TalkCmdSet()) to default_cmdsets under characters
Create a NPC using the NPC typeclass.

"""
from evennia import CmdSet, EvMenu
from evennia.utils import evtable
from evennia.utils import dbserialize
from typeclasses.characters import Character
from evennia.utils.utils import class_from_module
from django.conf import settings
COMMAND_DEFAULT_CLASS = class_from_module(settings.COMMAND_DEFAULT_CLASS)

class TalkCmdSet(CmdSet):
    """CmdSet for communicating with NPCs."""
    key = "talkcmdset"
    priority = 1

    def at_cmdset_creation(self):
        self.add(CmdTalk())


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

        target = caller.search(self.args,
                               typeclass=NPC,
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
        

class NPC(Character):
    """
    Talking NPCs
    """
    
    def at_talk(self, caller):
        """
        This class interprets the char.db.conversation attribute and displays
        the information in the following ways:
        
        If a list, the contents of the list is displayed as a EvMenu.
        If a dictionary, expects a node_dict and runs in EvMenu.
        If a string, then executed as python code and ran in Evmenu
        If anything else, then a "..." message is displayed.
        """

        def clean_node(nodetext, optionstext, caller=None):
            return nodetext
        def clean_options(optionlist, caller=None):
            return ""

        if not self.db.conversation:
            caller.msg(clean_node("...", ""))
            return

        conversation = self.db.conversation

        if isinstance(conversation, str):
            try:
                exec_variables = {}
                exec(conversation, exec_variables)
                EvMenu(caller, exec_variables["node_dict"], startnode="node1",
                        cmdset_mergetype="Replace", cmd_on_exit="",
                        node_formatter=clean_node, options_formatter=clean_options)
            except:
                caller.msg(clean_node("...", ""))
            return
            
        elif isinstance(conversation, dbserialize._SaverList):
            caller.msg("list")
            def node1(caller):
                menu = caller.ndb._menutree
                text = menu.conversation[menu.num]
                menu.num = menu.num + 1
                if menu.num >= len(menu.conversation):
                    return text, None
                else:
                    return text, {"key": "_default", "goto": "node1"}
            node_dict = {"node1": node1}
            EvMenu(caller, node_dict, startnode="node1",
                    cmdset_mergetype="Replace", cmd_on_exit="",
                    node_formatter=clean_node, options_formatter=clean_options,
                    num=0, conversation=conversation)
            return
        
        elif isinstance(conversation, dbserialize._SaverDict):
            EvMenu(caller, conversation, startnode="node1",
                    cmdset_mergetype="Replace", cmd_on_exit="",
                    node_formatter=clean_node, options_formatter=clean_options)
        
        else:
            caller.msg("else")
            caller.msg(clean_node("...", ""))
            return
