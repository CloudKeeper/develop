"""
Talking NPC
This is a Mixin that provides an NPC with the functionality to respond to the
'talk' command with an EvMenu based on a string, list, or dictionary.

By default, messages are collected from obj.db.conversation but may be expanded
in future.

Dictionary doesn't work because EvMenu has changed.

"""
from evennia import CmdSet, EvMenu
from evennia.utils import evtable
from evennia.utils import dbserialize
from evennia.utils.utils import class_from_module
from django.conf import settings
COMMAND_DEFAULT_CLASS = class_from_module(settings.COMMAND_DEFAULT_CLASS)

class CmdTalk(COMMAND_DEFAULT_CLASS):
    """
    Talk to a NPC. Triggers the corresponding objects at_talk hook.

    Usage:
        talk <obj>
    """
    key = "talk"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        """Actions undertaken by the Command"""

        # Set up function variables.
        caller = self.caller

        # If no target given, prompt caller
        if not self.args:
            caller.msg("Talk to whom?")
            return

        # Find target, or prompt caller
        target = caller.search(self.args,
                               nofound_string="You cannot talk to {}.".format(self.args))
        if not target:
            # No target msg handled by .search()
            return

        # Trigger conversation on target, or prompt caller
        if callable(target.at_talk):
            target.at_talk(caller)
        else:
            caller.msg("You cannot talk to {}.".format(self.args))

class ConversationMixin():
    """
    This is a mixin that provides functionality to respond to the Talk Command.
    """
    
    def at_talk(self, caller):
        """
        This class interprets the char.db.conversation attribute and displays
        the information in an EvMenu.
        """
        
        # Obtain Converstaion
        conversation = self.attributes.get("conversation", False)
        
        # Set Conversation Appearance
        def clean_node(nodetext, optionstext, caller=None):
            return nodetext
        def clean_options(optionlist, caller=None):
            return ""
        
        # Trigger Conversation
        if not conversation:
            caller.msg(clean_node("...", ""))
            return
            
        if isinstance(conversation, str):
            # Convert to a list and pass to isinstance(list)
            conversation = [conversation]
        
        if isinstance(conversation, dbserialize._SaverList) or isinstance(conversation, list):
            # Convert to a EvMenu dictionary and pass to EvMenu
            def node1(caller):
                menu = caller.ndb._menutree
                text = menu.conversation[menu.position]
                menu.position = menu.position + 1
                if menu.position >= len(menu.conversation):
                    return text, None
                else:
                    return text, {"key": "_default", "goto": "node1"}
            node_dict = {"node1": node1}
            
            EvMenu(caller, node_dict, 
                    startnode="node1",
                    cmdset_mergetype="Replace", 
                    cmd_on_exit="",
                    node_formatter= clean_node, 
                    options_formatter= clean_options,
                    position=0, 
                    conversation=conversation)
            return
        
        if isinstance(conversation, dbserialize._SaverDict) or isinstance(conversation, dict):
            # Pass to EvMenu
            EvMenu(caller, conversation, 
                    startnode="node1",
                    cmdset_mergetype="Replace", 
                    cmd_on_exit="",
                    node_formatter= clean_node, 
                    options_formatter= clean_options)
            return
        
        caller.msg(clean_node("...", ""))
        return
