"""
IRC Radio - INOPERABLE

Cloud_Keeper 2018

This connects an Evennia object to an IRC channel. This is achieved by having
a bot (the Portal Bot) connect to IRC. The Portal Bot communicates what it
hears to a bot (the Server Bot) inside Evennia. The Portal Bot then causes the
object to speak the IRC dialogue. This is a one way connection.

IRC -> Portal Bot -> inputfuncs.bot_data_in -> Server Bot -> Radio Object

This is meant as a simple one way version of an IRC bot.

"""
import time
from django.conf import settings
from evennia import CmdSet
from evennia.accounts.bots import Bot
from evennia.accounts.models import AccountDB
from evennia.server.portal.irc import IRCBot, IRCBotFactory
from evennia.utils import create, search, utils, ansi
from typeclasses.characters import Character
from typeclasses.objects import Object

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

#TODO Add run down of message types

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
        if channel == self.nickname:
            # private message
            user = user.split('!', 1)[0]
            pm_response = ("This is an Evennia IRC bot connecting from "
                           "'%s'." % settings.SERVERNAME)
            self.send_privmsg(pm_response, user=user)
        elif not msg.startswith('***'):
            # channel message
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
        bot_data_in Inputfunc. Other forms of input (join msgs etc) are ignored.
#TODO
        Args:
            session (Session, optional): Session responsible for this command.
                Note that this is the bot.
            txt (str, optional):  Command string.
        Kwargs:
            user (str): The name of the user who sent the message.
            channel (str): The name of channel the message was sent to.
            type (str): Nature of message. Either 'msg', 'action', 'nicklist'
                or 'ping'.
            nicklist (list, optional): Set if `type='nicklist'`. This is a list
                of nicks returned by calling the `self.get_nicklist`. It must
                look for a list `self._nicklist_callers` which will contain all
                callers waiting for the nicklist.
            timings (float, optional): Set if `type='ping'`. This is the return
                in seconds) of a ping request triggered with `self.ping`. The
                return must look for a list `self._ping_callers` which will
                contain all callers waiting for the ping return.
        """
        if kwargs["type"] == "ping":
            # the return of a ping
            if hasattr(self, "_ping_callers") and self._ping_callers:
                chstr = "%s (%s:%s)" % (self.db.irc_channel, self.db.irc_network, self.db.irc_port)
                for obj in self._ping_callers:
                    obj.msg("IRC ping return from %s took %ss." % (chstr, kwargs["timing"]))
                self._ping_callers = []
            return

        else:
            # something to send to the main channel
            if kwargs["type"] == "action":
                # An action (irc pose)
                text = "%s@%s %s" % (kwargs["user"], kwargs["channel"], txt)
            else:
                # msg - A normal channel message
                text = "%s@%s: %s" % (kwargs["user"], kwargs["channel"], txt)

            if not self.ndb.ev_object and self.db.ev_object:
                # cache channel lookup
                self.ndb.ev_object = self.db.ev_object
            if self.ndb.ev_object:
                self.ndb.ev_object.location.msg_contents(
                    text=(text,
                    {"type": "irc"}),
                    from_obj=self.ndb.ev_object)

##############################################################################
#
# Radio Object
# We are simply using the object for it's location. This can be any object
# Specified by the IRCRadio command
#
##############################################################################

##############################################################################
#
# Server Bot
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

    """

    key = "@puppetbot"
    locks = "cmd:serversetting(IRC_ENABLED) and pperm(Immortals)"
    help_category = "Comms"

    def func(self):
        """Setup the irc-channel mapping"""

        if not settings.IRC_ENABLED:
            string = "IRC is not enabled. Activate it in game/settings.py."
            self.msg(string)
            return

        # If no args: list bots.
        if not self.args:
            # show all connections
            ircbots = [bot for bot in
                       AccountDB.objects.filter(db_is_bot=True,
                                               username__startswith="ircbot-")]
            if ircbots:
                from evennia.utils.evtable import EvTable
                table = EvTable("|w#dbref|n", "|wbotname|n",
                                "|wev-channel/location|n",
                                "|wirc-channel|n", "|wSSL|n",
                                maxwidth=_DEFAULT_WIDTH)
                for ircbot in ircbots:
                    ircinfo = "%s (%s:%s)" % (
                        ircbot.db.irc_channel, ircbot.db.irc_network,
                        ircbot.db.irc_port)
                    table.add_row("#%i" % ircbot.id, ircbot.db.irc_botname,
                                  ircbot.attributes.get("ev_channel", ircbot.db.ev_location.key),
                                  ircinfo, ircbot.db.irc_ssl)
                self.msg(table)
                self.msg("Use 'help @puppetbot' for more infomation.")
            else:
                self.msg("No irc bots found.")
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

            # Puppetbot/delete <bot> - Delete bot.
            if any(i in ['disconnect', 'remove', 'delete'] for i in self.switches):
                matches[0].delete()
                self.msg("IRC link/bot destroyed.")
                return

            # Puppetbot/ping <bot> - ping bot.
            if "ping" in self.switches:
                matches[0].ping(self.caller)
                self.msg("Pinging " + self.lhs)
                return

            # Puppetbot/about <bot> = msg - Set bot about message.
            if "about" in self.switches:
                if self.rhs:
                    matches[0].db.botdesc = self.rhs
                    self.msg("Bot about message changed to: " + self.rhs)
                else:
                    self.msg("No message given. 'About' desc change aborted.")
                return

            # Puppetbot/who <bot> - Get IRC user list..
            if "who" in self.switches:
                # retrieve user list. The bot must handles the echo since it's
                # an asynchronous call.
                self.caller.msg("Requesting nicklist from %s (%s:%s)." % (
                                matches[0].db.irc_channel,
                                matches[0].db.irc_network,
                                matches[0].db.irc_port))
                matches[0].get_nicklist(self.caller)
                return

            # Puppetbot/reconnect <bot> - reconnect bot.
            if "reconnect" in self.switches:
                matches[0].reconnect()
                self.msg("Reconnecting " + self.lhs)
                return

            # Puppetbot/reload <bot> - Delete all bots, recreates bots from new user list.
            if "reload" in self.switches:
                matches[0].db.ev_location.msg_contents("Puppet reload in progress.")
                puppetlist = [puppet for puppet in search.search_tag(matches[0].key + "-puppet")]
                for puppet in puppetlist:
                    puppet.delete()
                matches[0].get_nicklist()
                return

            # Puppetbot/ignore <bot> = puppet - Toggle ignore IRC user.
            if "ignore" in self.switches:
                if self.rhs:
                    user = self.rhs.strip()
                    # If already ignored, toggle off.
                    if user in matches[0].db.userignorelist:
                        matches[0].db.userignorelist.remove(user)
                        matches[0].get_nicklist()
                        return

                    # Else ignore user.
                    else:
                        matches[0].db.userignorelist.append(user)
                        if user in matches[0].db.puppetdict:
                            matches[0].db.puppetdict[user].delete()
                            del matches[0].db.puppetdict[user]
                        return
                else:
                    self.msg("Usage: Puppetbot/ignore <bot> = <puppet>")
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
