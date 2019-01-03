"""
Photography

Take an in-game photograph.

Create a camera object which allows you to use the "photograph" command. When
the "photograph" command is used, the descriptions of your listed targets 
(by default the current room and room contents) will be saved onto a newly
created photograph object and can be viewed at any time after by looking
at the photograph.

Technical:
The 'photograph' command triggers the custom use_object() function on the 
camera object. The use_object() function creates a photo object and saves 
a dictionary of object names and descriptions. The photo object has a custom
return_appearance() function that draws upon the saved description data to
create an EvMenu that emulates being at the location.

Usage - In-game:
    @create camera:features.photography.Camera
    selfie

"""

"""
NOTES:
Photo Valuer:
-Pokemon emotes messages have a value attached to them stored on photo.
-Locatins have a value stored on the location -No point of reference on emote.
-Value of photo determined by factors including those values.

"""
import time
from django.conf import settings
from evennia.utils import utils, evmenu
from evennia import CmdSet
from evennia.utils.create import create_object
from typeclasses.objects import Object

COMMAND_DEFAULT_CLASS = utils.class_from_module(settings.COMMAND_DEFAULT_CLASS)

_TGT_ERRMSG = "'{}' could not be located."

#------------------------------------------------------------------------------
# Camera Object - Creates photographs when used.
#------------------------------------------------------------------------------

class Camera(Object):

    def at_object_creation(self):
        self.cmdset.add_default(CameraCmdSet, permanent=True)
        super(Camera, self).at_object_creation()

    def use_object(self, character, subjects):

        # Create photograph object.
        photo = create_object(typeclass=Photograph, location=character,
                              key="Photo " + character.location.key + str(int(time.time())))
        
        # Stores names and descriptions of Characters/Objects at location.
        photo.db.desc = "A small polaroid picture."
        photo.db.image = ("Captured in the glossy polaroid is: \n" +
                          character.location.key + "\n" +
                          character.location.db.desc + "\n")
        photo.db.subjects = {subject.key: subject.db.desc for subject in list(set(subjects))}
        character.location.msg_contents(character.key + " snapped a photograph!")

#------------------------------------------------------------------------------
# Camera Commands - Calls the camera.use_object() function
#------------------------------------------------------------------------------

class CameraCmdSet(CmdSet):
    """
    Camera Command Set
    """
    key = "cameracmdset"
    priority = 1

    def at_cmdset_creation(self):
        self.add(CmdPhotograph())


class CmdPhotograph(COMMAND_DEFAULT_CLASS):
    """
    Take a photograph.

    Usage:
        Photograph <subject>, <subject>, <subject>....]


    """
    key = "photograph"
    aliases = ["snap", "selfie"]
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        """Pass specified subjects to obj or default to location.contents"""

        subjectlist = []
        for subject in self.lhslist:
            if subject:
                subject = self.caller.search(subject, nofound_string=_TGT_ERRMSG.format(subject))
            if subject:
                subjectlist.append(subject)
        if not subjectlist:
            subjectlist = self.caller.location.contents

        self.obj.use_object(self.caller, subjectlist)

#------------------------------------------------------------------------------
# Photograph Object - Uses menus to mimic location when photograph taken.
#------------------------------------------------------------------------------

class Photograph(Object):

    def return_appearance(self, looker):

        # Initialise photograph menu.
        evmenu.EvMenu(looker, "features.photography",
                      startnode="photograph_node", persistent=True,
                      cmdset_mergetype="Replace",
                      node_formatter=photograph_node_formatter,
                      options_formatter=photograph_options_formattter,
                      photodesc=self.db.image, 
                      subjects=self.db.subjects,
                      current_state="")
        return ""

#------------------------------------------------------------------------------
# Photograph Menu - Look through objects and descriptions.
#------------------------------------------------------------------------------

def photograph_node_formatter(nodetext, optionstext, caller=None):
    """
    A minimalistic node formatter, no lines or frames.
    """
    return nodetext + "\n" + optionstext


def photograph_options_formattter(optionlist, caller=None):
    """
    A minimalistic options formatter that mirrors a rooms content list.
    """
    if not optionlist:
        return ""

    return "You see: " + ", ".join([key for key, msg in optionlist])

def photograph_node(caller, input_string):
    menu = caller.ndb._menutree
    text = ""
    options = [{"key": "_default",
                "goto": "photograph_node"}]

    # An item was selected to display, display item description.
    if input_string in menu.subjects:
        text = ("Looking closely at '" + input_string + "' you see: \n" +
                input_string.title() + "\n" + menu.subjects[input_string])
        menu.current_state = input_string
   
    # No match was found. Display main text but do not repeat it.
    else:
        if menu.current_state != "Main Menu":
            menu.current_state = "Main Menu"
            # Display main photo description
            text = menu.photodesc
            for subject in menu.subjects:
                _dict = {}
                _dict["key"] = subject
                _dict["goto"] = "photograph_node"
                options.append(_dict)
        else:
            # Display error message
            text += "Choose an option or 'Quit' to stop viewing."

    return text, options