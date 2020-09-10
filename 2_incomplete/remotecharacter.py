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

@remote > RemoteCharacter > RemoteAccount

# -----------------------------------------------------------------------------
NOTES:
-Add tag to msg being sent to account when acting as a puppet.
-Switch to turn off going to None
-Stops spam
-Have custom header, border or something to show it's from  a remote.
-Toggle stashing character after puppetting
# -----------------------------------------------------------------------------

In settings add max characters greater than 1:
    MAX_NR_CHARACTERS = 1

"""

from typeclasses.objects import Object
from evennia.accounts.bots import Bot


##############################################################################
#
# @Remote Command
#
##############################################################################

class RemoteCmdSet(CmdSet):
    """
    Holds commands used by the IRCPuppetBot.
    Import this to accounts command set to gain access to Puppet bot commands.
    """
    def at_cmdset_creation(self):
        self.add(CmdRemote())


class CmdRemote(COMMAND_DEFAULT_CLASS):
    """
    Creation and Deleting completed by @charcreate, @chardelete.
    Puppeting primary Character completed with @ic
    
    -Lock checks?
    @remote - All available characters and controlled characters
    @remote/control <character> - Start controlling character
    @remote <character> = <CmdString> - Act as controlled character
    *Prefer a command per remoteCharacter set up when you can work out how
    """
    key = "@remote"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        """ """
        # @remote  //  @remote/control
        # If no args: list controlled chars and available chars.
        if not self.args:
            self.msg("Your Current Main Character is %s" % self.account.obj.key)
            
            self.msg("Your Currently Controlled Characters:")
            current = [char for char in self.account.db._playable_characters
                       if char.db.remote_account is self.account]
            self.msg(str(current))
      
            self.msg("Your Currently available Characters:")
            current = [char for char in self.account.db._playable_characters
                       if not char.db.remote_account and not char.account]
            self.msg("Usage: @remote[/contro] <character> [= <cmdstring>]")
            return
      
        # @remote/control <character>
        # Set up controlling character remotely
        if "control" in self.switches:    
            # Get available character
            character = search.object_search(self.args,
                                candidates=self.account.db._playable_characters)
            if not character:
                self.msg("No Playable Characters by that name.")
                return

            if character[0].has_account or character[0].db.remote_account:
                self.msg("Character is currently being used.")
                return

            # Remote Character
            character.remote_control(caller)
            
        # @remote <character> = <cmdstring>
        # TO DO

##############################################################################
#
# RemoteCharacter Typeclass
#
##############################################################################


class RemoteCharacter(FILL IN WITH ALL CLASSES):
    """
    Collects Mixins to a single reference typeclass
    """

    def at_object_creation(self):
        """
        At creation we hide the 'listener' from view.
        """
        self.db.remote_account = None
        self.db.no_session_stashing = True

    def remote_control(self, controller):
        """
        """
        if not controller:
            return
        
        self.db.remote_account = controller
        
        # Set remote attribute
        # create command
        # give caller commandset

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
        if not self.sessions.count() and self.db.no_session_stashing:
            # only remove this char from grid if no sessions control it anymore.
            if self.location:
                def message(obj, from_obj):
                    obj.msg("%s has left the game." % self.get_display_name(obj),
                            from_obj=from_obj)

                self.location.for_contents(message, exclude=[self],
                                           from_obj=self)
                self.db.prelogout_location = self.location
                self.location = None

##############################################################################
#
# RemoteAccount Typeclasses
#
##############################################################################

class RemoteAccount(FILL IN WITH ALL CLASSES)):
    """

    """
    def at_account_creation(self):
        """
        This is called once, the very first time the account is created.
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
