"""
IRC Radio - INOPERABLE

Cloud_Keeper 2018

This connects an Evennia object to an IRC channel. This is achieved by having
a bot (the Portal Bot) connect to IRC. The Portal Bot communicates what it
hears to a bot (the Server Bot) inside Evennia. The Server Bot then causes the
object to speak the IRC dialogue. This is a one way connection.

IRC -> Portal Bot -> inputfuncs.bot_data_in -> Server Bot -> Radio Object

This is meant as a simple one way version of an IRC bot.

Instructions:
    1. Ensure IRC is enabled in your games settings file.
    2. Import the BotCmdSet to your character CmdSet.
    3. @puppetbot <irc_network> <port> <#irchannel> <object_name>

# -----------------------------------------------------------------------------
NOTES:
-Complete Command

# -----------------------------------------------------------------------------
"""

from django.conf import settings
from evennia import CmdSet
from evennia.accounts.bots import Bot
from evennia.accounts.models import AccountDB
from evennia.server.portal.irc import IRCBot, IRCBotFactory
from evennia.utils import create, search, utils, ansi

_DEFAULT_WIDTH = settings.CLIENT_DEFAULT_WIDTH

COMMAND_DEFAULT_CLASS = utils.class_from_module(settings.COMMAND_DEFAULT_CLASS)

_IRC_ENABLED = settings.IRC_ENABLED

_SESSIONS = None

##############################################################################
#
# Portal Bot
#
##############################################################################


class PortalBot(IRCBot):
    """
    IRC -> *Portal Bot* -> inputfuncs.bot_data_in -> Server Bot -> Radio Object

    This is a simple bot that idles in an IRC channel as a fake user. Messages
    inside of IRC triggers the privmsg() function. It sends everything it hears
    in the channel to Evennia. People who try to PM the bot will receive a
    polite message.

    The default implementation (evennia\server\portal\irc) is largely enough
    for our current purposes so we simply inherit from it. If you need to
    extend or alter the Bot's behaviour you can overload it here.

    For the full list of methods available refer to:
    https://github.com/twisted/twisted/blob/twisted-18.9.0/src/twisted/words/protocols/irc.py#L1099
    """
    def privmsg(self, user, channel, msg):
        """
        Called when the connected channel receives a message.

        Args:
            user (str): User name sending the message.
            channel (str): Channel name seeing the message.
            msg (str): The message arriving from channel.

        """
        # Respond to private messages with a little bit of information.
        if channel == self.nickname:
            user = user.split('!', 1)[0]
            pm_response = ("This is an Evennia IRC bot connecting from "
                           "'%s'." % settings.SERVERNAME)
            self.send_privmsg(pm_response, user=user)

        # We pass regular channel messages to out Server Bot.
        elif not msg.startswith('***'):
            user = user.split('!', 1)[0]
            user = ansi.raw(user)
            self.data_in(text=msg, type="msg", user=user, channel=channel)


class PortalBotFactory(IRCBotFactory):
    """
    Creates instances of the PortalBot.

    The original IRCBotFactory hardcodes the Bot, so this is our copy.
    """
    def buildProtocol(self, addr):
        """
        Build the protocol and assign it some properties.

        Args:
            addr (str): Not used; using factory data.

        """
        protocol = PortalBot()
        protocol.factory = self
        protocol.nickname = self.nickname
        protocol.channel = self.channel
        protocol.network = self.network
        protocol.port = self.port
        protocol.ssl = self.ssl
        protocol.nicklist = []
        return protocol

##############################################################################
#
# InputFunc.bot_data_in (located at evennia\server\inputfunc.py)
# Input Functions catch incoming messages from external to Evennia and handle
# getting them to where they need to go inside of Evennia.
# For information only, should not need to be edited.
#
##############################################################################


# def bot_data_in(session, *args, **kwargs):
#     """
#     Text input from the IRC and RSS bots.
#     This will trigger the execute_cmd method on the bots in-game counterpart.
#
#     Args:
#         session (Session): The active Session to receive the input.
#         text (str): First arg is text input. Other arguments are ignored.
#
#     """
#
#     txt = args[0] if args else None
#
#     # Explicitly check for None since text can be an empty string, which is
#     # also valid
#     if txt is None:
#         return
#     # this is treated as a command input
#     # handle the 'idle' command
#     if txt.strip() in _IDLE_COMMAND:
#         session.update_session_counters(idle=True)
#         return
#     kwargs.pop("options", None)
#     # Trigger the execute_cmd method of the corresponding bot.
#     session.account.execute_cmd(session=session, txt=txt, **kwargs)
#     session.update_session_counters()

##############################################################################
#
# Server Bot
#
##############################################################################


class ServerBot(Bot):
    """
    IRC -> Portal Bot -> inputfuncs.bot_data_in -> *Server Bot* -> Radio Object

    This is the Server bot that receives the IRC messages from the Portal Bot
    via the bot_data_in input function and sends it in turn to the IRC object.

    The default implementation (evennia.accounts.bots.IRCBot) is largely enough
    for our current purposes so we simply inherit from it. If you need to
    extend or alter the Bot's behaviour you can overload it here.

    The Server Bot is created first and creates the Portal Bot in start()
    """

    def start(self, ev_object=None, irc_botname=None, irc_channel=None,
              irc_network=None, irc_port=None, irc_ssl=None):
        """
        Start by telling the portal to start a new session.

        Args:
            ev_object (obj): The Evennia object to connect to.
            irc_botname (str): Name of bot to connect to irc channel. If
                not set, use `self.key`.
            irc_channel (str): Name of channel on the form `#channelname`.
            irc_network (str): URL of the IRC network, like `irc.freenode.net`.
            irc_port (str): Port number of the irc network, like `6667`.
            irc_ssl (bool): Indicates whether to use SSL connection.

        """
        if not _IRC_ENABLED:
            # the bot was created, then IRC was turned off. We delete
            # ourselves (this will also kill the start script)
            self.delete()
            return

        global _SESSIONS
        if not _SESSIONS:
            from evennia.server.sessionhandler import SESSIONS as _SESSIONS

        # if keywords are given, store (the BotStarter script
        # will not give any keywords, so this should normally only
        # happen at initialization)
        if irc_botname:
            self.db.irc_botname = irc_botname
        elif not self.db.irc_botname:
            self.db.irc_botname = self.key
        if ev_object:
            ev_object.db.bot = self
            self.db.ev_object = ev_object
        if irc_channel:
            self.db.irc_channel = irc_channel
        if irc_network:
            self.db.irc_network = irc_network
        if irc_port:
            self.db.irc_port = irc_port
        if irc_ssl:
            self.db.irc_ssl = irc_ssl

        # Instruct the server and portal to create a new session with
        # the stored configuration
        configdict = {"uid": self.dbid,
                      "botname": self.db.irc_botname,
                      "channel": self.db.irc_channel,
                      "network": self.db.irc_network,
                      "port": self.db.irc_port,
                      "ssl": self.db.irc_ssl}
        _SESSIONS.start_bot_session("features.ircradio.PortalBotFactory",
                                    configdict)

    def execute_cmd(self, session=None, txt=None, **kwargs):
        """
        Route messages to our radio object. This is triggered by the
        bot_data_in Inputfunc. For our purposes we are only worried about
        channel messages and actoins. Other forms of input (join msgs etc)
        are ignored.

        Args:
            session (Session, optional): Session responsible for this command.
                Note that this is the bot.
            txt (str, optional):  Command string.
        Kwargs:
            user (str): The name of the user who sent the message.
            channel (str): The name of channel the message was sent to.
            type (str): Nature of message. Either:-
                        'msg' - Message sent to connected channel by a user.
                        'action' - An IRC /me message
                        'nicklist' - List of users in IRC channel
                        'ping'. - Testing the channel connectivity
            nicklist (list, optional): Set if `type='nicklist'`. This is a list
                of nicks returned by calling the `self.get_nicklist`. It must
                look for a list `self._nicklist_callers` which will contain all
                callers waiting for the nicklist.
            timings (float, optional): Set if `type='ping'`. This is the return
                in seconds) of a ping request triggered with `self.ping`. The
                return must look for a list `self._ping_callers` which will
                contain all callers waiting for the ping return.
        """
        # Our radio object has been deleted (Returns None). Destroy self.
        if not self.db.ev_object:
            self.delete()

        # Cache object reference - Saves checking DB every message.
        if not self.ndb.ev_object and self.db.ev_object:
            self.ndb.ev_object = self.db.ev_object

        if self.ndb.ev_object:
            if kwargs["type"] == "action":
                # An action (irc pose)
                text = "%s-%s@%s %s" % (self.ndb.ev_object.key, kwargs["user"],
                                        kwargs["channel"], txt)
                self.ndb.ev_object.location.msg_contents(
                    text=(text, {"type": "irc"}), from_obj=self.ndb.ev_object)

            if kwargs["msg"] == "action":
                # msg - A normal channel message
                text = "%s-%s@%s: %s" % (self.ndb.ev_object.key, kwargs["user"],
                                         kwargs["channel"], txt)
                self.ndb.ev_object.location.msg_contents(
                    text=(text, {"type": "irc"}), from_obj=self.ndb.ev_object)

##############################################################################
#
# Radio Object
# We are simply using the object for it's location. This can be any object
# Specified by the IRCRadio command. The Bot will delete itself if it finds
# our radio object has been deleted.
#
##############################################################################

##############################################################################
#
# IRCRadio Command
#
##############################################################################


class BotCmdSet(CmdSet):
    """
    Holds commands used by the IRCPuppetBot.
    Import this to accounts command set to gain access to Puppet bot commands.
    """
    def at_cmdset_creation(self):
        self.add(CmdPuppetBot())


class CmdPuppetBot(COMMAND_DEFAULT_CLASS):
    """
    Link an Evennia object to an external IRC channel.
    The location of the object will be used to send IRC messages to
    object.location.msg_contents()

    """

    key = "@ircradio"
    locks = "cmd:serversetting(IRC_ENABLED) and pperm(Immortals)"
    help_category = "Comms"

    def func(self):
        """Setup the irc-channel mapping"""

        if not settings.IRC_ENABLED:
            string = "IRC is not enabled. Activate it in game/settings.py."
            self.msg(string)
            return

        # If no args direct to help.
        if not self.args:
            self.msg("Use 'Help @ircradio' for instructions.")
            return

        # Switch options available only if valid bot is given.
        if self.switches:
            botname = "ircbot-%s" % self.lhs
            matches = AccountDB.objects.filter(db_is_bot=True, username=botname)
            dbref = utils.dbref(self.lhs)
            if not matches and dbref:
                # try dbref match
                matches = AccountDB.objects.filter(db_is_bot=True, id=dbref)
            if not matches:
                self.msg("No valid bot given. Consult 'help @puppetbot'")
                return

            # Puppetbot/reconnect <bot> - reconnect bot.
            if "reconnect" in self.switches:
                matches[0].reconnect()
                self.msg("Reconnecting " + self.lhs)
                return

        # Create Bot.
        location = self.caller.location
        self.args = self.args.replace('#', ' ')  # Avoid Python comment issues
        try:
            irc_network, irc_port, irc_channel, irc_botname = \
                       [part.strip() for part in self.args.split(None, 4)]
            irc_channel = "#%s" % irc_channel
        except Exception:
            string = "IRC bot definition '%s' is not valid." % self.args
            self.msg(string)
            return

        botname = "ircbot-%s" % irc_botname
        # create a new bot
        bot = AccountDB.objects.filter(username__iexact=botname)
        if bot:
            # re-use an existing bot
            bot = bot[0]
            if not bot.is_bot:
                self.msg("'%s' already exists and is not a bot." % botname)
                return
        else:
            try:
                bot = create.create_account(botname, None, None,
                                           typeclass=ServerBot)
            except Exception as err:
                self.msg("|rError, could not create the bot:|n '%s'." % err)
                return
        bot.start(ev_location=location, irc_botname=irc_botname,
                  irc_channel=irc_channel, irc_network=irc_network,
                  irc_port=irc_port)
        self.msg("Connection created. Starting IRC bot.")
