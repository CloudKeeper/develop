"""
Radio Station - INOPERABLE

This is a system for having in-game radio stations which players can tune into
via radio objects to 'hear' (read) their favourite songs or 'listen to' (read) 
their favourite radio host.

A 'radio station' is a channel, like that created by by the channelcreate
command, that players cannot connect to directly. Instead special radio 
objects are 'tuned' to the different channels and will then announce the 
messages from that channel into the their current location. 

The messages of the Radio Stations is broadcast by a script that, in this 
implementation, simply selects a global level string variable at random from a 
module which contains song lyrics to be split by line and 'broadcast' one at 
a time in sequence.

Lyric Module -> Radio Station -> Channel -> Radio Object -> Location

# -----------------------------------------------------------------------------
NOTES:
- Get list of variables in module and pop next song from list. That will 
prevent repeats until set finished.
# -----------------------------------------------------------------------------
"""
from evennia.comms.models import ChannelDB
from evennia.utils import utils
from evennia import DefaultScript, TICKER_HANDLER
import random, sys


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
♫ At the old ball game ♫
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


class RadioObj(Object):
    """
    Objects that subscribe to channels and relay the messages they receive
    to the room they are in.
    """

    def msg(self, text=None, from_obj=None, session=None, options=None, **kwargs):
        """
        Channels send their messages with a marker. We check for the marker
        and echo it to the room if the marker is found.
        """
        if options:
            if "from_channel" in options:
                self.location.msg_contents(text, exclude=self)

        super(RadioObj, self).msg()



"""
# -*- coding: utf-8 -*-
 
#
# Batchcself.db.channel.msg("Test", header=None, senders=None)ode Script
#
 
# HEADER
 
# CODE
from evennia.comms.models import ChannelDB
from evennia.comms.channelhandler import CHANNELHANDLER
from evennia import create_channel, create_object, create_script
from typeclasses import objects
 
# radio_channel = create_channel("radio",
#                                ["Radio"],
#                                "Description",
#                                "send:all();listen:all();control:id(%s)" % caller.id)
# radio_channel.connect(caller)
# CHANNELHANDLER.update()
 
channel = ChannelDB.objects.channel_search("Radio")
station = channel[0]
 
radio = create_object(objects.ReceiverObj, key="radio", location=caller.location)
station.connect(radio)
CHANNELHANDLER.update()
 
station.msg("Connected", header=None, senders=None)
create_script("world.script_radio.RadioStation", obj=None)
"""
