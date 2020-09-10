"""
Set up chains of emote messsages.

"""
from django.conf import settings
from typeclasses.objects import Object
from evennia.utils.utils import class_from_module
from evennia import TICKER_HANDLER as tickerhandler   
COMMAND_DEFAULT_CLASS = class_from_module(settings.COMMAND_DEFAULT_CLASS)

class EmoteChainMixin(Object):
    """
    Attributes:
        dances (dict): A characters saved emotechains
    """

    def at_object_creation(self):
        super(EmoteChainMixin, self).at_object_creation()
        self.db.emotechains = {}
        self.db.current_emotechain = []
        self.db.emote_step = 0

    def start_emotechain(self, emote_chain):
        # Init emote chain
        self.db.emote_step = 0
        self.db.current_emotechain = emote_chain
        tickerhandler.add(5, self.at_emote)
        
        # Send first message immediately
        self.at_emote()

    def at_emote(self):
        chain = self.db.current_emotechain
        step = self.db.emote_step
        
        if step > len(chain):
            self.stop_emotechain
            return
        
        msg = "%s%s" % (self.name, chain[step])
        self.location.msg_contents(text=(msg, {"type": "pose"}), from_obj=self)
        self.db.emote_step = step + 1
        
    def stop_emotechain(self):
        tickerhandler.remove(5, self.at_emote)

class CmdEmote(COMMAND_DEFAULT_CLASS):
    """
    Describe an action or series of actions being taken.

    Usage:
        emote <emote text>
        emote's <emote text>
        emote <emote 1>; <emote 2>

    Example:
        emote is standing by the wall, smiling.
        -> others will see:
        Tom is standing by the wall, smiling
      
        emote dances to the left; dances to the right
        -> others will see:
        Tom dances to the left
        -> 5 seconds later:
        Tom dances to the right

    The emote text will automatically begin with your name.
    """

    key = "emote"
    aliases = [":"]
    switch_options = ("stop")
    locks = "cmd:all()"

    def parse(self):
        """
        Custom parse the cases where the emote
        starts with some special letter, such
        as 's, at which we don't want to separate
        the caller's name and the emote with a
        space.
        """
        args = self.args.split(";")
        for arg in args:
            if arg and not arg[0] in ["'", ",", ":"]:
                args = " %s" % args.strip()
        self.args = args

    def func(self):
        """Hook function"""
        caller = self.caller
        args = self.args
        
        # Saved Emote Functionality
        if any(value in ("edit", "builder") for value in self.switches):
            # Chain builder
            return
        
        # Stop running emote chain
        if "stop" in self.switches:
            caller.stop_emote()
        
        # If empty message
        if len(args) == 1 and not args[0]:
            self.caller.msg("What do you want to do?")
            return
        
        # If only a single message, send immediately
        if len(args) == 1:
            msg = "%s%s" % (caller.name, args)
            caller.location.msg_contents(text=(msg, {"type": "pose"}), from_obj=caller)
        
        # If a chain, refer to emote_chain functionality
        else:
            caller.start_emote(self, args)