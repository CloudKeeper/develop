"""
IRC2Puppet - INOPERABLE

Cloud_Keeper 2018

The main character will have the session and account attached to it
Your puppets are a custom typeclass
You store a reference to your main account on the puppet.db.puppeteer
And you change their .msg() to send messages to their puppeteer rather
than their session. In your main character, you change the typeclass to keep
a history of the last 2 or 3 messages. That way, if your main character and
your puppets are in the same room, your main character will recieve the
first message and send it to your client. THen it'll get the second message
and see it's already gotten it and throw it away etc
You've already got your commands working so that's fine

Account method.

Account:
Secondary puppet
msg = if from secondary puppet (self.db.puppetter = self) check against history
and boot.
add puppet.db.puppetkey <>
add to history



Command:
Puppet <Object>
If not puppeted and passes lock builder, creates connection.
sets self.db.puppeteer
Gives command set.

Unpuppet <Object>

Puppet:
self.db.puppeteer = puppeteer
on_create() - make command based on key that sends text to execute command.


command
Createremote
creates character


# -----------------------------------------------------------------------------
NOTES:
-Switch to turn off going to None
-Stops spam
# -----------------------------------------------------------------------------
"""

from typeclasses.objects import Object
from evennia.accounts.bots import Bot

##############################################################################
#
# Remote Character
#
##############################################################################


class RemoteCharacter(DefaultCharacter):
    """

    """

    def at_object_creation(self):
        """
        At creation we hide the 'listener' from view.
        """
        self.db.allow_remote = False
        self.db.remote_account = None

    def at_post_unpuppet(self, account, session=None, **kwargs):
        """
        The RemoteCharacter provides a switch to toggle stowing the character
        away when the account goes ooc/logs off, to allow others to remote
        puppet the character whilst the account holder is gone.

        Args:
            account (Account): The account object that just disconnected
                from this object.
            session (Session): Session controlling the connection that
                just disconnected.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).
        """
        if not self.sessions.count():
            # only remove this char from grid if no sessions control it anymore.
            if self.location:
                def message(obj, from_obj):
                    obj.msg("%s has left the game." % self.get_display_name(obj), from_obj=from_obj)
                self.location.for_contents(message, exclude=[self], from_obj=self)
                self.db.prelogout_location = self.location
                if not self.db.allow_remote:  # The remote switch
                    self.location = None

    def at_post_unremotepuppet(self, account, session=None, **kwargs):
        """
        The RemoteCharacter provides a switch to toggle stowing the character
        away when the account goes ooc/logs off, to allow others to remote
        puppet the character whilst the account holder is gone.

        Args:
            account (Account): The account object that just disconnected
                from this object.
            session (Session): Session controlling the connection that
                just disconnected.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).
        """
        if not self.db.remote_account():
            super(RemoteCharacter, self).at_post_unpuppet(account, session,
                                                          **kwargs)

    def msg(self, text=None, from_obj=None, session=None, options=None, **kwargs):
        """
        If currently a remote puppet, send message to account
        """
        if self.db.remote_account:
            self.db.remote_account.msg(text, from_obj, session, options,
                                       **kwargs)
            return

        super(RemoteCharacter, self).msg(text, from_obj, session, options,
                                         **kwargs)

##############################################################################
#
# Remote Account
#
##############################################################################


class RemoteAccount(DefaultAccount):
    """

    """

    def at_account_creation(self):
        """
        This is called once, the very first time the account is created
        (i.e. first time they register with the game). It's a good
        place to store attributes all accounts should have, like
        configuration values etc.
        """
        super(RemoteAccount, self).at_account_creation()

        # Create message history to compare against and remove spamming.
        self.attribute.add("msg_history", [None, None])

    def msg(self, text=None, from_obj=None, session=None, options=None, **kwargs):
        """
        Evennia -> User
        This is the main route for sending data back to the user from the
        server.
        Args:
            text (str, optional): text data to send
            from_obj (Object or Account or list, optional): Object sending. If given, its
                at_msg_send() hook will be called. If iterable, call on all entities.
            session (Session or list, optional): Session object or a list of
                Sessions to receive this send. If given, overrules the
                default send behavior for the current
                MULTISESSION_MODE.
            options (list): Protocol-specific options. Passed on to the protocol.
        Kwargs:
            any (dict): All other keywords are passed on to the protocol.
        """
        if text in self.db.msg_history:
            return
        self.db.msg_history.append(text)
        self.db.msg_history.pop(0)

        super(RemoteAccount, self).msg(text, from_obj, session, options,
                                       **kwargs)

