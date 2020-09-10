"""
Ambient Rooms - TO BE TESTED

Cloud_Keeper

This is a system for sending intermittent messages to players within a room to
provide ambiance.

A series of Mixins, allows all objects to optionally hold messages which
have a chance to be intermittently displayed to the objects around them.
These messages are collected with the return_ambient_msgs() function.
By default:
    Objects only return their own messages.
    Characters return their own messages + the messages of worn clothing.
    Rooms return their own messages + the messages returned by their contents.
    
When a player enters a room, the room subscribes to a timer. When the interval
has elapsed the room sends an ambient message to it's contents randomly chosen
from the list returned by return_ambient_msgs(). When no players are in the room
it unsubscribes from the timer.

Expansions:
- Command to control Ambient messages
- Messasges have Ambience tag
"""

from evennia import DefaultObject, DefaultCharacter, DefaultRoom, DefaultScript
from evennia import TICKER_HANDLER as tickerhandler
import random
from evennia.server.sessionhandler import SESSIONS


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
        ambient_interval (int): Seconds between ambient messages
        connected_to_ticker (Bool): Whether connected to ticker or not
    """

    def at_object_creation(self):
        """
        Adds Database Attributes:
            ambient_switch (Bool): Whether ambient msgs will be collected
        ambient_msgs (dict): Dict of ambient message strings and weighting. 
                             Eg. {"The sun shines brightly": 1}
        """
        super(AmbientRoom, self).at_object_creation()
        self.db.ambient_interval = 30
        self.db.connected_to_ticker = False
    
    def at_object_receive(self, moved_obj, source_location, **kwargs):
        """
        Called after an object has been moved into this object.
        Args:
            moved_obj (Object): The object moved into this one
            source_location (Object): Where `moved_object` came from.
                Note that this could be `None`.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).
        """
        super(AmbientRoom, self).at_object_receive()
        if self.db.ambient_switch:
            # If player enters and not already, connect to ticker
            if moved_obj.has_account and not self.db.connected_to_ticker:
                tickerhandler.add(self.db.ambient_interval,
                                  self.display_ambient_msg(),
                                  persistent=True)
                self.db.connected_to_ticker = True

    def at_object_leave(self, moved_obj, target_location, **kwargs):
        """
        Called just before an object leaves from inside this object
        Args:
            moved_obj (Object): The object leaving
            target_location (Object): Where `moved_obj` is going.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).
        """
        if self.db.connected_to_ticker:
            # If we no longer have players in the room. Turn off ticker.
            if not [obj.has_account for obj in self.contents_get()]:
                tickerhandler.remove(self.db.ambient_interval,
                                     self.display_ambient_msg())
                self.db.connected_to_ticker = False
            pass

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
