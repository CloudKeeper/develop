"""
Radio Station - To Be Tested

This is a system for having in-game radio stations which players can tune into
via radio objects to 'hear' (read) their favourite songs or 'listen to' (read) 
their favourite radio host.

A 'radio channel' is a regular channel, like that created by the channelcreate
command, that players cannot connect to directly. Instead special radio 
objects are 'tuned' to the different channels and will then echo the 
messages from that channel into the their current location. 

- Get list of variables in module and pop next song from list. That will 
prevent repeats until set finished.
Enhancements:
- Pause Station so you can run your own show etc
-Radio objcts allow changing channels
    Get list from tag
    alphebetise
    Skip to next one in list

Channel Locks
send - who may send to the channel.
listen - who may subscribe and listen to the channel.

LockFunc
true()/all() - give access to everyone
none() - give access to none. Superusers bypass the check entirely and are thus the only ones who will pass this check.
attr(attrname) - checks if a certain Attribute exists on accessing_object.
attr(attrname, value) - checks so an attribute exists on accessing_object and has the given value.

NOTES:
-Custom lock for not accounts or characters with accounts.

"""
from evennia.comms.models import ChannelDB
from evennia.utils import utils
from evennia import DefaultObject, DefaultScript, TICKER_HANDLER
import random, sys


# -----------------------------------------------------------------------------
#
# Radio Channel
#
# The functionality of the channel is just the default channel
# A lock is attached so only radio objects may join the channel. 
# A tag is attached to readily find radio channels.
# This is handled in channel creation. See sample Batch below.
# 
# ----------------------------------------------------------------------------

"""
# Setup Channel
from evennia import create_channel
radio_channel = create_channel("radio channel",
                               desc="Good times and Greatest Hits",
                               locks="send:all();listen:all();control:all()",
                               tags=["radio"])
"""

# -----------------------------------------------------------------------------
#
# Radio Object
# 
# -----------------------------------------------------------------------------

class RadioObj(DefaultObject):
    """
    Objects that subscribe to channels and relay the messages they receive
    to the room they are in.
    """

    def at_object_creation(self):
        """
        Adds Database Attributes:
            radio_switch (Bool): Will only echo messages if True
        """
        super(RadioObj, self).at_object_creation()
        self.db.radio_switch = False

    def msg(self, text=None, from_obj=None, session=None, options=None, **kwargs):
        """
        Channels send their messages with a marker. We check for the marker
        and echo it to the room if the marker is found and radio is on.
        """
        if options and self.db.radio_switch:
            if "from_channel" in options:
                self.location.msg_contents(text, exclude=self)
        super(RadioObj, self).msg()

class RadioRoom (DefaultObject):
    """
    Rooms that subscribe to channels and relay the messages they receive
    to their contents.
    """

    def at_object_creation(self):
        """
        Adds Database Attributes:
            radio_switch (Bool): Will only echo messages if True
        """
        super(RadioRoom, self).at_object_creation()
        self.db.radio_switch = False

    def msg(self, text=None, from_obj=None, session=None, options=None, **kwargs):
        """
        Channels send their messages with a marker. We check for the marker
        and echo it to the room if the marker is found and radio is on.
        """
        if options and self.db.radio_switch:
            if "from_channel" in options:
                self.msg_contents(text, exclude=self)
        super(RadioObj, self).msg()

# -----------------------------------------------------------------------------
#
# Radio Station - Source > RadioStation > Channel > RadioObject > Room
#
# -----------------------------------------------------------------------------

class RadioStation(DefaultScript):
    """
    self.db.source [Python path, absolute path or a module]
    self.db.channel = ChannelDB.objects.channel_search(self.key)[0]
    """

    def at_script_creation(self):
        self.key = "Radio Station"
        self.desc = "Script that sends messages to a channel"
        self.interval = 10  # Repeats after 10 seconds.

        self.db.channel = None
        self.db.source = sys.modules[__name__] # Default source file (this one)
        self.db.channel = None  # Channel to broadcast to.
        self.db.current = None  # Current song.

    def at_repeat(self):
        """

        """

        # If no current, pick random song from source and break into lines.
        if not self.db.current:
            self.db.current = utils.random_string_from_module(self.db.source).splitlines()

        # Broadcast next line.
        if self.db.channel:
            self.db.channel.msg(self.db.current.pop(0))

# -----------------------------------------------------------------------------
#
# Radio Messages - Source > RadioStation > Channel > RadioObject > Room
# Default radio messages to be played if no source identified.
#
# -----------------------------------------------------------------------------

# Default radio messages.
static = """\
The crackle of background static bellows from the speakers\
"""

ball_game = """\
♫ Take me out to the ball game ♫
♫ Take me out with the crowd ♫
♫ Buy me some peanuts and Cracker Jack ♫
♫ I don't care if I never get back ♫
♫ Let me root, root, root for the home team ♫
♫ If they don't win, it's a shame ♫
♫ For it's one, two, three strikes, you're out ♫
♫ At the old ball game ♫\
"""

evennia_ad = """\
We interrupt this program for a word from our sponsors:
Good morning boys and girls!
Did you know that Evennia is an open-source library and toolkit...
made for building multi-player online text games!
You can easily design your entire game using normal Python modules.
Get your parents to get you Evennia today!
Now back to your regular program.\
"""

# -----------------------------------------------------------------------------
#
# Example Batch Code Creation
#
# -----------------------------------------------------------------------------

"""
from evennia.comms.models import ChannelDB
from evennia.comms.channelhandler import CHANNELHANDLER
from evennia import create_channel, create_object, create_script
from typeclasses import objects
 
# Setup Channel
radio_channel = create_channel("radio",
                               ["Radio"],
                               "Description",
                               "send:all();listen:all();control:all()")

# Setup Station
station = create_script("features.radiostation.RadioStation", obj=None)
station.db.channel = radio_channel

# Setup Radio
radio = create_object("features.radiostation.RadioObject", 
                      key="radio", location=caller.location)
radio_channel.connect(radio)
"""
