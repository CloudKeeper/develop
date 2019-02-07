"""
Ambient Messages - TO BE TESTED

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
from the list returned by return_ambient_msgs()

# -----------------------------------------------------------------------------
NOTES:
- Alternative to Mixinx: Have a central handler that deals with it all
- Ambient messages be weighted

*If items(), keys(), values(),  iteritems(), iterkeys(), and  itervalues() are
*called with no intervening modifications to the dictionary, the lists will
*directly correspond: 3.x documentation.
*random.choices(population, weights=None, *, cum_weights=None, k=1)

TO DO:
-Rooms could have an on/off switch that the script checks for. If off,
and player enters, it does not subscribe to ticker. If later turned on, it
checks to see if player in room then subscribes to ticker and will work normally
form then on.
-Command to control Ambient messages
-Messasges have Ambience tag
# -----------------------------------------------------------------------------
"""

from evennia import DefaultObject, DefaultCharacter, DefaultRoom
from evennia import TICKER_HANDLER as tickerhandler
from random import random

# -----------------------------------------------------------------------------
# Ambient Message Storage
# -----------------------------------------------------------------------------


class AmbientObj(DefaultObject):
    """
    Basic typeclass for the Ambient Objects.
    
    Database Attributes:
        ambient_msgs (dict): Dictionary of ambient messages and weighting.
    """
    
    def at_object_creation(self):
        """
        Adds the ambient_msgs dictionary to the object.
        Eg. self.db.ambient_msgs = {"The sun shines brightly": 1}
        """
        super(AmbientObj, self).at_object_creation()
        self.db.ambient_msgs = []
        
    def return_ambient_msgs(self):
        """
        In the basic typeclass, merely returns the raw ambient_msgs dictionary.
        """
        return self.db.ambient_msgs


class AmbientChar(DefaultCharacter, AmbientObj):
    """
    Typeclass for the Ambient Character.
    
    Database Attributes:
        ambient_msgs (dict): Dictionary of ambient messages and weighting.
    """
        
    def return_ambient_msgs(self):
        """
        Collects the ambient messages from the characters worn equipment and 
        adds them to the characters own messages
        """
        ambient_msgs = self.db.ambient_msgs
        # for obj in self.EQUIPMENT:
        #     try:
        #         ambient_msgs.update(obj.return_ambient_msgs()}
        #     except:
        #         continue
        return ambient_msgs


class AmbientRoom(DefaultRoom, AmbientObj):
    """
    Typeclass for the Ambient Room.
    
    Database Attributes:
        ambient_msgs (dict): Dictionary of ambient messages and weighting.
    """
    def at_object_creation(self):
        """
        Adds the ambient_msgs dictionary to the object.
        Eg. self.db.ambient_msgs = {"The sun shines brightly": 1}
        """
        super(AmbientRoom, self).at_object_creation()
        self.db.ambient_msgs = []
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
        # If player enters and not already connected to the ticker. Do so.
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
        self.msg_contents(random(self.return_ambient_msgs))

    def return_ambient_msgs(self):
        """
        Collects the ambient messages from room contents and
        adds them to the Rooms own messages.
        """
        ambient_msgs = self.db.ambient_msgs
        for obj in self.contents_get():
            ambient_msgs.update(obj.get("ambient_msgs", []))
        return ambient_msgs
