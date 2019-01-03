"""
Ambient Messages

Cloud_Keeper

This is a system for sending intermittant messages to a room to provide 
ambiance. 

A series of Mixins, allows all objects to optionally hold messages which
have a chance to be intermittently displayed to the objects around them.
These messages can be collected with the return_ambientmsgs() functions.
By default:
    Objects only return their own messages.
    Characters return their  own messages + the messages of worn clothing.
    Rooms return their own  messages + the messages returned by their contents.
    
A global script set at 30 second intervals, determines which rooms have 
players in  them and triggers an ambient message picked at random by the 
rooms returned messages.

"""

"""
NOTES:

    2.1 A room Mixin that subscribes to the ticker at an individual interval.
        1.2 A Handler you can connect to your typeclass.

self.db.ambientmsg is dictionary {"message": weight}
If items(), keys(), values(),  iteritems(), iterkeys(), and  itervalues() are 
called with no intervening modifications to the dictionary, the lists will 
directly correspond: 3.x documentation.

random.choices(population, weights=None, *, cum_weights=None, k=1)

TO DO:
-*EQUIPPABLE ITEMS HAVE THEIR OWN RETURN_AMBIENTMSGS THAT APPENDS NAME ETC
-    def at_object_receive(self, moved_obj, source_location, **kwargs):
        ""
        If room recieves a player, and an ambience message is 15 seconds away,
        send an ambience message in 5 seconds if still in the room.
        ""
-Rooms could have an on/off switch that the script checks for.
   
# STORING THE MESSAGES - METHOD 2 - Handler
So that anything you attach the handler to will get full functionality.

# SENDING THE MESSAGES - METHOD 2 - ON ROOMS
class AmbientRoom(DefaultRoom):

    def at_creation():
        self.db.interval = #ANYTHING YOU WANT

    def at_object_receive():
        if moved_obj is Character & Character.account:
            tickerhandler.add(self.db.interval, call_ambient_message, 
                      idstring="ticker1", persistent=True, *args, **kwargs)
                      
    def at_object_leave():
        if no_other_players:
            tickerhandler.remove(self.db.interval, call_ambient_message,
                                idstring="ticker1")
                                
    def call_ambient_message():
        get_ambient_messages
        self.msg_contents(random(messages))
"""

from evennia import DefaultObject, DefaultCharacter, DefaultRoom, DefaultScript

#------------------------------------------------------------------------------
# Storing the messages
#------------------------------------------------------------------------------

class AmbientObj(DefaultObject):
    """
    Basic typeclass for the Ambient Objects.
    
    Attributes:
        ambientmsgs (dict): Dictionary of ambient messages and weighting.
    """
    
    def at_object_creation(self):
        """
        Adds the ambientmsgs dictionary to the object.
        Eg. self.db.ambientmsgs = {"The sun shines brightly": 1}
        """
        super(AmbientObj, self).at_object_creation()
        self.db.ambientmsgs = {}
        
    def return_ambientmsgs(self):
        """
        In the basic typeclass, merely returns the raw ambientmsgs dictionary.
        """
        return self.db.ambientmsgs
        
class AmbientChar(DefaultCharacter, AmbientObj):
    """
    Typeclass for the Ambient Character.
    
    Attributes:
        ambientmsgs (dict): Dictionary of ambient messages and weighting.
    """
        
    def return_ambientmsgs(self):
        """
        Collects the ambient messages from the characters worn equipment and 
        adds them to the characters own messages
        """
        ambientmsgs = self.db.ambientmsgs
        # for obj in self.EQUIPMENT:
        #     try:
        #         ambientmsgs.update(obj.return_ambientmsgs()}
        #     except:
        #         continue
        return ambientmsgs
        
class AmbientRoom(DefaultRoom, AmbientObj):
    """
    Typeclass for the Ambient Room.
    
    Attributes:
        ambientmsgs (dict): Dictionary of ambient messages and weighting.
    """

    def return_ambientmsgs(self):
        """
        Collects the ambient messages from room contents and 
        adds them to the Rooms own messages.
        """
        ambientmsgs = self.db.ambientmsgs
        for obj in self.contents_get():
            try:
                ambientmsgs.update(obj.return_ambientmsgs()
            except:
                continue
        return ambientmsgs

#------------------------------------------------------------------------------
# Sending the messages
#------------------------------------------------------------------------------

class Ambience(DefaultScript): 
    """
    Triggers Ambience Messages. Meant to be attached to a room.
    """
    def at_script_creation(self):
        self.key = "ambience_script"
        self.desc = "Triggers ambience messages in rooms from contents."
        self.interval = 30
        self.persistent = True

    def at_repeat(self):
        """
        Called every self.interval seconds.
        """   
        # get_list_of_players
        # get_player_locations
        # for room in player_locations:
        #     messages = get_ambient_messages(room)
        #     room.msg_contents(random(messages))
