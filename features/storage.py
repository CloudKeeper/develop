"""


"""

class CmdGet(COMMAND_DEFAULT_CLASS):
    """
    pick up something
    Usage:
      get <obj>
    Picks up an object from your location and puts it in
    your inventory.
    """
    key = "get"
    aliases = "grab"
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def func(self):
        """implements the command."""

        caller = self.caller

        if not self.args:
            caller.msg("Get what?")
            return
        obj = caller.search(self.args, location=caller.location)
        if not obj:
            return
        if caller == obj:
            caller.msg("You can't get yourself.")
            return
        if not obj.access(caller, 'get'):
            if obj.db.get_err_msg:
                caller.msg(obj.db.get_err_msg)
            else:
                caller.msg("You can't get that.")
            return

        # calling at_before_get hook method
        if not obj.at_before_get(caller):
            return

        obj.move_to(caller, quiet=True)
        caller.msg("You pick up %s." % obj.name)
        caller.location.msg_contents("%s picks up %s." %
                                     (caller.name,
                                      obj.name),
                                     exclude=caller)
        # calling at_get hook method
        obj.at_get(caller)





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
        pass
        
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
        return True

    def at_get(self, getter, **kwargs):
        """
        Called by the default `get` command when this object has been
        picked up.
        Args:
            getter (Object): The object getting this object.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).
        Notes:
            This hook cannot stop the pickup from happening. Use
            permissions or the at_before_get() hook for that.
        """
        pass
        
      