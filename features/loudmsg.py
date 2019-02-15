"""
Loud Sounds - TO BE TESTED

This is Room object functions which sends a message to the contents of all 
rooms connecting to this room via an exit (Entrances) or all rooms this room connects to 
via exits (Exits) or both.

There is also a basic sample command that utilises this functionality.


Say Command that sends messages to adjoining rooms
Add function to object that messages contents and the contents of destinations
set on it's contents.

entrances = Exit.objects.filter(db_destination=here)
exits = here.exits

"""
from evennia.utils.utils import make_iter, is_iter
from evennia typeclasses.rooms import DefaultRoom


class LoudRoom(DefaultRoom):
    """
    This is the base room object. It's just like any Object except its
    location is always `None`.
    """
    
    def msg_entrances(self, text=None, exclude=None, from_obj=None, **kwargs):
            """
            Emit message to all objects inside rooms connecting to this room
            via exits.
            
            Args:
                text (str or tuple): Message to send. If a tuple, this should be
                    on the valid OOB outmessage form `(message, {kwargs})`,
                    where kwargs are optional data passed to the `text`
                    outputfunc.
                exclude (list, optional): A list of objects not to send to.
                from_obj (Object, optional): An object designated as the
                    "sender" of the message. See `DefaultObject.msg()` for
                    more info.
            Kwargs:
                Keyword arguments will be passed on to `obj.msg()` for all
                messaged objects.
            """
            # we also accept an outcommand on the form (message, {kwargs})
            is_outcmd = text and is_iter(text)
            message = text[0] if is_outcmd else text
            outkwargs = text[1] if is_outcmd and len(text) > 1 else {}
    
            # Collect exit and entrance locations with no repeats.
            rooms = self.objects.filter(db_destination=self)
            rooms = list(set(rooms))
            if self in rooms: rooms.remove(self)
    
            if exclude:
                exclude = make_iter(exclude)
                rooms = [room for room in rooms if room not in exclude]
            for room in rooms:
                room.msg_contents(text=(message, outkwargs), from_obj=from_obj, **kwargs)
    
    def msg_exits(self, text=None, exclude=None, from_obj=None, **kwargs):
            """
            Emit message to all objects in rooms this room connects to via 
            exits.
            
            Args:
                text (str or tuple): Message to send. If a tuple, this should be
                    on the valid OOB outmessage form `(message, {kwargs})`,
                    where kwargs are optional data passed to the `text`
                    outputfunc.
                exclude (list, optional): A list of objects not to send to.
                from_obj (Object, optional): An object designated as the
                    "sender" of the message. See `DefaultObject.msg()` for
                    more info.
            Kwargs:
                Keyword arguments will be passed on to `obj.msg()` for all
                messaged objects.
            """
            # we also accept an outcommand on the form (message, {kwargs})
            is_outcmd = text and is_iter(text)
            message = text[0] if is_outcmd else text
            outkwargs = text[1] if is_outcmd and len(text) > 1 else {}
    
            # Collect exit and entrance locations with no repeats.
            rooms = [exit.destination for exit in self.exits]
            rooms = list(set(rooms))
            if self in rooms: rooms.remove(self)
    
            if exclude:
                exclude = make_iter(exclude)
                rooms = [room for room in rooms if room not in exclude]
            for room in rooms:
                room.msg_contents(text=(message, outkwargs), from_obj=from_obj, **kwargs)

    def msg_connections(self, text=None, exclude=None, from_obj=None, **kwargs):
            """
            Emit message to all objects inside rooms connecting to this room
            via exits, and rooms this room connects to via exits.
            
            Args:
                text (str or tuple): Message to send. If a tuple, this should be
                    on the valid OOB outmessage form `(message, {kwargs})`,
                    where kwargs are optional data passed to the `text`
                    outputfunc.
                exclude (list, optional): A list of objects not to send to.
                from_obj (Object, optional): An object designated as the
                    "sender" of the message. See `DefaultObject.msg()` for
                    more info.
            Kwargs:
                Keyword arguments will be passed on to `obj.msg()` for all
                messaged objects.
            """
            # we also accept an outcommand on the form (message, {kwargs})
            is_outcmd = text and is_iter(text)
            message = text[0] if is_outcmd else text
            outkwargs = text[1] if is_outcmd and len(text) > 1 else {}
    
            # Collect exit and entrance locations with no repeats.
            room = []
            rooms.append(self.objects.filter(db_destination=self))
            rooms.append([exit.destination for exit in self.exits])
            rooms = list(set(rooms))
            if self in rooms: rooms.remove(self)
    
            if exclude:
                exclude = make_iter(exclude)
                rooms = [room for room in rooms if room not in exclude]
            for room in rooms:
                room.msg_contents(text=(message, outkwargs), from_obj=from_obj, **kwargs)
