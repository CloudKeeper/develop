"""
Invisible Objects - Needs Testing

Vanilla Evennia does not allow true invisibility out of the box.

The 'view' lock will disallow viewing with "Could not view 'object(#9)'", 
instead of 'Could not find 'bla''.

The 'get' lock will disallow getting with "Could not get 'object(#9)'", 
instead of 'Could not find 'bla''.

Both of which give away the existance of our hidden object.

Here we set up the infrastructure for a new lock "invisible". When true, look 
and get will return like it could not find the object at all.

SHORTCOMINGS:
-Because the hooks don't know the command given, they will always use the key
of the object, which may be different if they used an alias. Will also not
relay capitalisations of argument command like normal.

"""

from evennia import DefaultObject
from evennia.utils import utils

# -----------------------------------------------------------------------------
# Ambient Message Storage
# -----------------------------------------------------------------------------

class RespectInvisibilityMixin():
    """
    A mixin to put on Character objects. This will allow

    """
    def at_look(self, target, **kwargs):
        """
        Called when this object performs a look. It allows to
        customize just what this means. It will not itself
        send any data.

        Args:
            target (Object): The target being looked at. This is
                commonly an object or the current location. It will
                be checked for the "view" type access.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call. This will be passed into
                return_appearance, get_display_name and at_desc but is not used
                by default.

        Returns:
            lookstring (str): A ready-processed look string
                potentially ready to return to the looker.

        """
        # Check view lock, default gives away the hidden object. 
        # Change to pretend no object was found from search.
        if target.access(self, "invisible"):
            self.msg(f"Could not find '{target.key}'")
            return
        
        if not target.access(self, "view"):
            try:
                return "Could not view '%s'." % target.get_display_name(self, **kwargs)
            except AttributeError:
                return "Could not view '%s'." % target.key

        description = target.return_appearance(self, **kwargs)

        # the target's at_desc() method.
        # this must be the last reference to target so it may delete itself when acted on.
        target.at_desc(looker=self, **kwargs)

        return description
        

    def at_before_get(self, getter, **kwargs):
        """
        Called by the default `get` command before this object has been
        picked up.

        Args:
            getter (Object): The object about to get this object.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).

        Returns:
            shouldget (bool): If the object should be gotten or not.

        Notes:
            If this method returns False/None, the getting is cancelled
            before it is even started.
        """
        # Check view lock, default gives away the hidden object. 
        # Change to pretend no object was found from search.
        if self.access(self, "invisible"):
            getter.msg(f"Could not find '{self.key}'")
            return False
        return True