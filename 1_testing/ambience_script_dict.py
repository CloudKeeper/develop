"""
Ambient Script - TO BE TESTED

Cloud_Keeper

This is a system for sending intermittent messages to a room to provide
ambiance. 

A series of Mixins, allows all objects to optionally hold messages which
have a chance to be intermittently displayed to the objects around them.
These messages are collected with the return_ambient_msgs() function.
By default:
    Objects only return their own messages.
    Characters return their own messages + the messages of worn clothing.
    Rooms return their own messages + the messages returned by their contents.
    
A global script set at 30 second intervals determines which rooms have
players in them and triggers an ambient message picked at random by the
returned options.

Messages are stored in a dictioary on the object: {message:weight}

Expansions:
- Build Commands
- Ambience messages are tagged
"""

from evennia import DefaultObject, DefaultCharacter, DefaultRoom, DefaultScript
from evennia import TICKER_HANDLER as tickerhandler
import random
from evennia.server.sessionhandler import SESSIONS

# -----------------------------------------------------------------------------
# Ambient Message Storage
# -----------------------------------------------------------------------------


class AmbientObj(DefaultObject):
    """
    Basic Mixin for the Ambient Objects.
    
    Adds Database Attributes:
        ambient_switch (Bool): Whether ambient msgs will be collected
        ambient_msgs (dict): Dict of ambient message strings and weighting. 
                             Eg. {"The sun shines brightly": 1}
    """
    
    def at_object_creation(self):
        """
        Adds Database Attributes:
            ambient_switch (Bool): Whether ambient msgs will be collected
            ambient_msgs (dict): Dict of ambient message strings and weighting. 
                                 Eg. {"The sun shines brightly": 1}
        """
        super(AmbientObj, self).at_object_creation()
        self.db.ambient_switch = True
        self.db.ambient_msgs = {}
        
    def return_ambient_msgs(self):
        """
        In the basic typeclass, merely returns the raw ambient_msgs dictionary.
        """
        if self.db.ambient_switch:
            return self.db.ambient_msgs


class AmbientChararacter(DefaultCharacter, AmbientObj):
    """
    Typeclass for the Ambient Character.
    
    Adds Database Attributes:
        ambient_switch (Bool): Whether ambient msgs will be collected
        ambient_msgs (dict): Dict of ambient message strings and weighting. 
                             Eg. {"The sun shines brightly": 1}
    """
        
    def return_ambient_msgs(self):
        """
        Collects the ambient messages from the characters worn equipment and 
        adds them to the characters own messages
        """
        if self.db.ambient_switch:
            ambient_msgs = self.db.ambient_msgs
            # Append equipment messages here.
            return ambient_msgs


class AmbientRoom(DefaultRoom, AmbientObj):
    """
    Typeclass for the Ambient Room.
    
    Database Attributes:
        ambient_switch (Bool): Whether ambient msgs will be sent
        ambient_msgs (dict): Dict of ambient message strings and weighting. 
                             Eg. {"The sun shines brightly": 1}
    """

    def display_ambient_msg(self):
        """
        Displays an ambient message selected at random from list returned by
        return_ambient_msgs().
        """
        msgs = self.return_ambient_msgs()
        self.msg_contents(random.choices(list(msgs.keys()), 
                                         weights=list(msgs.values()),
                                         k=1)[0])
    
    def return_ambient_msgs(self):
        """
        Collects the ambient messages from room contents and 
        adds them to the Rooms own messages.
        """
        if self.db.ambient_switch:
            ambient_msgs = self.db.ambient_msgs
            for obj in self.contents_get():
                try:
                    ambient_msgs.update(obj.return_ambient_msgs())
                except:
                    continue
            return ambient_msgs

# -----------------------------------------------------------------------------
# Ambient Message Triggers
# -----------------------------------------------------------------------------


class AmbientScript(DefaultScript):
    """
    This is a Global Script. At each interval it collects a list of rooms
    which contains players. It then displays an ambiance message to it's
    contents selected from the messages returned by it's return_ambient_msgs
    function.
    """
    def at_script_creation(self):
        self.key = "ambiance_script"
        self.desc = "Triggers ambient messages in rooms from contents."
        self.interval = 30
        self.persistent = True

    def at_repeat(self):
        """
        Called every self.interval seconds.
        """
        # Get puppets with online players connected (and thus have a location)
        online_chars = [session.puppet for session in SESSIONS
                        if session.puppet]

        # Get puppet locations with no repeats
        inhabited_rooms = list(set([puppet.location for puppet in online_chars]))

        # Message room with random ambient message
        for room in inhabited_rooms:
            try:
                room.display_ambient_msg()
            except:
                continue
