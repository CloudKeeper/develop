"""
Housing - INOPERABLE

-Character Mixin
-Exit Obj
-Room Mixin
-Design Menu

class RadioObj(FixtureObj):
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
 
class RadioStation(DefaultScript):
    """
    A script for sending a channel messages to simulate talk back radio.
    Channels do not have a script handler so the script must be global.
    The script draws messages from a flat file and sends it to an in-game
    channel. The key of the script should be the same as the flat file
    dictionary from which it draws and the channel to which it sends to.

    Changing interval in at_repeat doesn't change interval time. I imagine it's
    because at start it subscribes to a ticker.
    """
    key = "Radio"
    interval = 5  # Repeats after 10 seconds.
 
    def at_script_creation(self):
        self.db.channel = ChannelDB.objects.channel_search(self.key)[0]
        self.db.data = None
        self.db.playlist = []
        self.db.position = 0
        pass
 
    def at_start(self):
        """TO DO"""
        self.db.data = utils.variable_from_module("world.radio",
                                                  variable="pokemusic")
 
        TICKER_HANDLER.add(10, self.broadcast)
 
    def broadcast(self):
 
        if not self.db.playlist or self.db.playlist[0] not in self.db.data:
            x = self.db.data.keys()
            random.shuffle(x)
            self.db.playlist = x
            self.db.position = 0
 
        if self.db.position == len(self.db.data[self.db.playlist[0]]):
            self.db.playlist.pop(0)
            self.db.position = 0
 
        pos = self.db.position
 
        self.db.channel.msg(self.db.data[self.db.playlist[0]][pos],
                            header=None, senders=None)
        self.db.position += 1
 
# encoding=utf-8
"""
Songs for radio channels.
"""
 
static = {
 
    "Static" : [
        "The crackle of background static bellows from the speakers",
    ],
}
 
pokemusic = {
 
    "Pokemon Theme": [
        "♫ I want to be the very best, like no one ever was. ♫",
        "♫ To catch them is my real test, to train them is my cause. ♫",
       
    ],
 
    "PokeRap" : [
        "♫ I want to be the best there ever was ♫",
        "♫ To beat all the rest, yeah, that's my cause! ♫",
    ],
}
 
 
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
