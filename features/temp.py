"""

"""
import time
import hashlib
from django.conf import settings
from evennia import CmdSet
from evennia.accounts.bots import Bot
from evennia.accounts.models import AccountDB
from evennia.utils.utils import class_from_module
from evennia.utils import create, search
from twisted.application import internet
from twisted.words.protocols import irc
from twisted.internet import protocol, reactor
from evennia.server.portal.irc import parse_ansi_to_irc, parse_irc_to_ansi
from evennia.server.session import Session
from evennia.utils import logger, utils, ansi

COMMAND_DEFAULT_CLASS = class_from_module(settings.COMMAND_DEFAULT_CLASS)
_DEFAULT_WIDTH = settings.CLIENT_DEFAULT_WIDTH
_IRC_ENABLED = settings.IRC_ENABLED

_SESSIONS = None


class BotCmdSet(CmdSet):
    """
    Implements the account command set.
    """

    key = "DefaultAccount"
    priority = -10

    def at_cmdset_creation(self):
        """Populates the cmdset"""
        self.add(CmdPuppetBot())


class CmdPuppetBot(COMMAND_DEFAULT_CLASS):
    """
    link an evennia channel to an external IRC channel
    Usage:
      @irc2chan[/switches] <evennia_channel> = <ircnetwork> <port> <#irchannel> <botname>[:typeclass]
      @irc2chan/delete botname|#dbid
    Switches:
      /delete     - this will delete the bot and remove the irc connection
                    to the channel. Requires the botname or #dbid as input.
      /remove     - alias to /delete
      /disconnect - alias to /delete
      /list       - show all irc<->evennia mappings
      /ssl        - use an SSL-encrypted connection
    Example:
      @irc2chan myircchan = irc.dalnet.net 6667 #mychannel evennia-bot
      @irc2chan public = irc.freenode.net 6667 #evgaming #evbot:accounts.mybot.MyBot
    This creates an IRC bot that connects to a given IRC network and
    channel. If a custom typeclass path is given, this will be used
    instead of the default bot class.
    The bot will relay everything said in the evennia channel to the
    IRC channel and vice versa. The bot will automatically connect at
    server start, so this command need only be given once. The
    /disconnect switch will permanently delete the bot. To only
    temporarily deactivate it, use the  |w@services|n command instead.
    Provide an optional bot class path to use a custom bot.
    """

    key = "@puppetbot"
    switch_options = ("delete", "remove", "disconnect", "list", "ssl")
    locks = "cmd:serversetting(IRC_ENABLED) and pperm(Developer)"
    help_category = "Comms"

    def func(self):
        """Setup the irc-channel mapping"""

        if not settings.IRC_ENABLED:
            string = """IRC is not enabled. You need to activate it in game/settings.py."""
            self.msg(string)
            return

        if 'list' in self.switches:
            # show all connections
            ircbots = [bot for bot in AccountDB.objects.filter(db_is_bot=True, username__startswith="ircbot-")]
            if ircbots:
                from evennia.utils.evtable import EvTable
                table = EvTable("|w#dbref|n", "|wbotname|n", "|wev-channel|n",
                                "|wirc-channel|n", "|wSSL|n", maxwidth=_DEFAULT_WIDTH)
                for ircbot in ircbots:
                    ircinfo = "%s (%s:%s)" % (ircbot.db.irc_channel, ircbot.db.irc_network, ircbot.db.irc_port)
                    table.add_row("#%i" % ircbot.id, ircbot.db.irc_botname, ircbot.db.ev_channel, ircinfo,
                                  ircbot.db.irc_ssl)
                return table
            else:
                return "No irc bots found."

        if 'disconnect' in self.switches or 'remove' in self.switches or 'delete' in self.switches:
            botname = "ircbot-%s" % self.lhs
            matches = AccountDB.objects.filter(db_is_bot=True, username=botname)
            dbref = utils.dbref(self.lhs)
            if not matches and dbref:
                # try dbref match
                matches = AccountDB.objects.filter(db_is_bot=True, id=dbref)
            if matches:
                matches[0].delete()
                self.msg("IRC connection destroyed.")
            else:
                self.msg("IRC connection/bot could not be removed, does it exist?")
            return

        if not self.args or not self.rhs:
            string = "Usage: @irc2chan[/switches] <evennia_channel> =" \
                     " <ircnetwork> <port> <#irchannel> <botname>[:typeclass]"
            self.msg(string)
            return

        channel = self.lhs
        self.rhs = self.rhs.replace('#', ' ')  # to avoid Python comment issues
        try:
            irc_network, irc_port, irc_channel, irc_botname = \
                [part.strip() for part in self.rhs.split(None, 4)]
            irc_channel = "#%s" % irc_channel
        except Exception:
            string = "IRC bot definition '%s' is not valid." % self.rhs
            self.msg(string)
            return

        botclass = None
        if ":" in irc_botname:
            irc_botname, botclass = [part.strip() for part in irc_botname.split(":", 2)]
        botname = "ircbot-%s" % irc_botname
        # If path given, use custom bot otherwise use default.
        botclass = botclass if botclass else ServerBot
        irc_ssl = "ssl" in self.switches

        # create a new bot
        bot = AccountDB.objects.filter(username__iexact=botname)
        if bot:
            # re-use an existing bot
            bot = bot[0]
            if not bot.is_bot:
                self.msg("Account '%s' already exists and is not a bot." % botname)
                return
        else:
            password = hashlib.md5(bytes(str(time.time()), 'utf-8')).hexdigest()[:11]
            try:
                bot = create.create_account(botname, None, password, typeclass=botclass)
            except Exception as err:
                self.msg("|rError, could not create the bot:|n '%s'." % err)
                return
        bot.start(ev_channel=channel, irc_botname=irc_botname, irc_channel=irc_channel,
                  irc_network=irc_network, irc_port=irc_port, irc_ssl=irc_ssl)
        self.msg("Connection created. Starting IRC bot.")


class ServerBot(Bot):
    """
    Bot for handling IRC connections.
    """

    def start(self, ev_channel=None, irc_botname=None, irc_channel=None, irc_network=None, irc_port=None, irc_ssl=None):
        """
        Start by telling the portal to start a new session.
        Args:
            ev_channel (str): Key of the Evennia channel to connect to.
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
        if ev_channel:
            # connect to Evennia channel
            channel = search.channel_search(ev_channel)
            if not channel:
                raise RuntimeError("Evennia Channel '%s' not found." % ev_channel)
            channel = channel[0]
            channel.connect(self)
            self.db.ev_channel = channel
        if irc_channel:
            self.db.irc_channel = irc_channel
        if irc_network:
            self.db.irc_network = irc_network
        if irc_port:
            self.db.irc_port = irc_port
        if irc_ssl:
            self.db.irc_ssl = irc_ssl

        # instruct the server and portal to create a new session with
        # the stored configuration
        configdict = {"uid": self.dbid,
                      "botname": self.db.irc_botname,
                      "channel": self.db.irc_channel,
                      "network": self.db.irc_network,
                      "port": self.db.irc_port,
                      "ssl": self.db.irc_ssl}
        _SESSIONS.start_bot_session("features.temp.PortalBotFactory", configdict)

    def at_msg_send(self, **kwargs):
        """Shortcut here or we can end up in infinite loop"""
        pass

    def get_nicklist(self, caller):
        """
        Retrieve the nick list from the connected channel.
        Args:
            caller (Object or Account): The requester of the list. This will
                be stored and echoed to when the irc network replies with the
                requested info.
        Notes: Since the return is asynchronous, the caller is stored internally
            in a list; all callers in this list will get the nick info once it
            returns (it is a custom OOB inputfunc option). The callback will not
            survive a reload (which should be fine, it's very quick).
        """
        if not hasattr(self, "_nicklist_callers"):
            self._nicklist_callers = []
        self._nicklist_callers.append(caller)
        super().msg(request_nicklist="")
        return

    def ping(self, caller):
        """
        Fire a ping to the IRC server.
        Args:
            caller (Object or Account): The requester of the ping.
        """
        if not hasattr(self, "_ping_callers"):
            self._ping_callers = []
        self._ping_callers.append(caller)
        super().msg(ping="")

    def reconnect(self):
        """
        Force a protocol-side reconnect of the client without
        having to destroy/recreate the bot "account".
        """
        super().msg(reconnect="")

    def msg(self, text=None, **kwargs):
        """
        Takes text from connected channel (only).
        Args:
            text (str, optional): Incoming text from channel.
        Kwargs:
            options (dict): Options dict with the following allowed keys:
                - from_channel (str): dbid of a channel this text originated from.
                - from_obj (list): list of objects sending this text.
        """
        from_obj = kwargs.get("from_obj", None)
        options = kwargs.get("options", None) or {}
        if not self.ndb.ev_channel and self.db.ev_channel:
            # cache channel lookup
            self.ndb.ev_channel = self.db.ev_channel
        if "from_channel" in options and text and self.ndb.ev_channel.dbid == options["from_channel"]:
            if not from_obj or from_obj != [self]:
                super().msg(channel=text)

    def execute_cmd(self, session=None, txt=None, **kwargs):
        """
        Take incoming data and send it to connected channel. This is
        triggered by the bot_data_in Inputfunc.
        Args:
            session (Session, optional): Session responsible for this
                command. Note that this is the bot.
            txt (str, optional):  Command string.
        Kwargs:
            user (str): The name of the user who sent the message.
            channel (str): The name of channel the message was sent to.
            type (str): Nature of message. Either 'msg', 'action', 'nicklist' or 'ping'.
            nicklist (list, optional): Set if `type='nicklist'`. This is a list of nicks returned by calling
                the `self.get_nicklist`. It must look for a list `self._nicklist_callers`
                which will contain all callers waiting for the nicklist.
            timings (float, optional): Set if `type='ping'`. This is the return (in seconds) of a
                ping request triggered with `self.ping`. The return must look for a list
                `self._ping_callers` which will contain all callers waiting for the ping return.
        """
        if kwargs["type"] == "nicklist":
            # the return of a nicklist request
            if hasattr(self, "_nicklist_callers") and self._nicklist_callers:
                chstr = "%s (%s:%s)" % (self.db.irc_channel, self.db.irc_network, self.db.irc_port)
                nicklist = ", ".join(sorted(kwargs["nicklist"], key=lambda n: n.lower()))
                for obj in self._nicklist_callers:
                    obj.msg("Nicks at %s:\n %s" % (chstr, nicklist))
                self._nicklist_callers = []
            return

        elif kwargs["type"] == "ping":
            # the return of a ping
            if hasattr(self, "_ping_callers") and self._ping_callers:
                chstr = "%s (%s:%s)" % (self.db.irc_channel, self.db.irc_network, self.db.irc_port)
                for obj in self._ping_callers:
                    obj.msg("IRC ping return from %s took %ss." % (chstr, kwargs["timing"]))
                self._ping_callers = []
            return

        elif kwargs["type"] == "privmsg":
            # A private message to the bot - a command.
            user = kwargs["user"]

            if txt.lower().startswith("who"):
                # return server WHO list (abbreviated for IRC)
                global _SESSIONS
                if not _SESSIONS:
                    from evennia.server.sessionhandler import SESSIONS as _SESSIONS
                whos = []
                t0 = time.time()
                for sess in _SESSIONS.get_sessions():
                    delta_cmd = t0 - sess.cmd_last_visible
                    delta_conn = t0 - session.conn_time
                    account = sess.get_account()
                    whos.append("%s (%s/%s)" % (utils.crop("|w%s|n" % account.name, width=25),
                                                utils.time_format(delta_conn, 0),
                                                utils.time_format(delta_cmd, 1)))
                text = "Who list (online/idle): %s" % ", ".join(sorted(whos, key=lambda w: w.lower()))
            elif txt.lower().startswith("about"):
                # some bot info
                text = "This is an Evennia IRC bot connecting from '%s'." % settings.SERVERNAME
            else:
                text = "I understand 'who' and 'about'."
            super().msg(privmsg=((text,), {"user": user}))
        else:
            # something to send to the main channel
            if kwargs["type"] == "action":
                # An action (irc pose)
                text = "%s@%s %s" % (kwargs["user"], kwargs["channel"], txt)
            else:
                # msg - A normal channel message
                text = "%s@%s: %s" % (kwargs["user"], kwargs["channel"], txt)

            if not self.ndb.ev_channel and self.db.ev_channel:
                # cache channel lookup
                self.ndb.ev_channel = self.db.ev_channel
            if self.ndb.ev_channel:
                self.ndb.ev_channel.msg(text, senders=self)


class PortalBot(irc.IRCClient, Session):
    """
    An IRC bot that tracks activity in a channel as well
    as sends text to it when prompted
    """
    lineRate = 1

    # assigned by factory at creation

    nickname = None
    logger = None
    factory = None
    channel = None
    sourceURL = "http://code.evennia.com"

    def signedOn(self):
        """
        This is called when we successfully connect to the network. We
        make sure to now register with the game as a full session.
        """
        self.join(self.channel)
        self.stopping = False
        self.factory.bot = self
        address = "%s@%s" % (self.channel, self.network)
        self.init_session("ircbot", address, self.factory.sessionhandler)
        # we link back to our bot and log in
        self.uid = int(self.factory.uid)
        self.logged_in = True
        self.factory.sessionhandler.connect(self)
        logger.log_info("IRC bot '%s' connected to %s at %s:%s." % (self.nickname, self.channel,
                                                                    self.network, self.port))

    def disconnect(self, reason=""):
        """
        Called by sessionhandler to disconnect this protocol.
        Args:
            reason (str): Motivation for the disconnect.
        """
        self.sessionhandler.disconnect(self)
        self.stopping = True
        self.transport.loseConnection()

    def at_login(self):
        pass

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
            self.data_in(text=msg, type="privmsg", user=user, channel=channel)
        elif not msg.startswith('***'):
            # channel message
            user = user.split('!', 1)[0]
            user = ansi.raw(user)
            self.data_in(text=msg, type="msg", user=user, channel=channel)

    def action(self, user, channel, msg):
        """
        Called when an action is detected in channel.
        Args:
            user (str): User name sending the message.
            channel (str): Channel name seeing the message.
            msg (str): The message arriving from channel.
        """
        if not msg.startswith('**'):
            user = user.split('!', 1)[0]
            self.data_in(text=msg, type="action", user=user, channel=channel)

    def get_nicklist(self):
        """
        Retrieve name list from the channel. The return
        is handled by the catch methods below.
        """
        if not self.nicklist:
            self.sendLine("NAMES %s" % self.channel)

    def irc_RPL_NAMREPLY(self, prefix, params):
        """"Handles IRC NAME request returns (nicklist)"""
        channel = params[2].lower()
        if channel != self.channel.lower():
            return
        self.nicklist += params[3].split(' ')

    def irc_RPL_ENDOFNAMES(self, prefix, params):
        """Called when the nicklist has finished being returned."""
        channel = params[1].lower()
        if channel != self.channel.lower():
            return
        self.data_in(text="", type="nicklist", user="server", channel=channel, nicklist=self.nicklist)
        self.nicklist = []

    def pong(self, user, time):
        """
        Called with the return timing from a PING.
        Args:
            user (str): Name of user
            time (float): Ping time in secs.
        """
        self.data_in(text="", type="ping", user="server", channel=self.channel, timing=time)

    def data_in(self, text=None, **kwargs):
        """
        Data IRC -> Server.
        Kwargs:
            text (str): Ingoing text.
            kwargs (any): Other data from protocol.
        """
        self.sessionhandler.data_in(self, bot_data_in=[parse_irc_to_ansi(text), kwargs])

    def send_channel(self, *args, **kwargs):
        """
        Send channel text to IRC channel (visible to all). Note that
        we don't handle the "text" send (it's rerouted to send_default
        which does nothing) - this is because the IRC bot is a normal
        session and would otherwise report anything that happens to it
        to the IRC channel (such as it seeing server reload messages).
        Args:
            text (str): Outgoing text
        """
        text = args[0] if args else ""
        if text:
            text = parse_ansi_to_irc(text)
            self.say(self.channel, text)

    def send_privmsg(self, *args, **kwargs):
        """
        Send message only to specific user.
        Args:
            text (str): Outgoing text.
        Kwargs:
            user (str): the nick to send
                privately to.
        """
        text = args[0] if args else ""
        user = kwargs.get("user", None)
        if text and user:
            text = parse_ansi_to_irc(text)
            self.msg(user, text)

    def send_request_nicklist(self, *args, **kwargs):
        """
        Send a request for the channel nicklist. The return (handled
        by `self.irc_RPL_ENDOFNAMES`) will be sent back as a message
        with type `nicklist'.
        """
        self.get_nicklist()

    def send_ping(self, *args, **kwargs):
        """
        Send a ping. The return (handled by `self.pong`) will be sent
        back as a message of type 'ping'.
        """
        self.ping(self.nickname)

    def send_reconnect(self, *args, **kwargs):
        """
        The server instructs us to rebuild the connection by force,
        probably because the client silently lost connection.
        """
        self.factory.reconnect()

    def send_default(self, *args, **kwargs):
        """
        Ignore other types of sends.
        """
        pass


class PortalBotFactory(protocol.ReconnectingClientFactory):
    """
    Creates instances of IRCBot, connecting with a staggered
    increase in delay
    """
    # scaling reconnect time
    initialDelay = 1
    factor = 1.5
    maxDelay = 60

    def __init__(self, sessionhandler, uid=None, botname=None, channel=None, network=None, port=None, ssl=None):
        """
        Storing some important protocol properties.
        Args:
            sessionhandler (SessionHandler): Reference to the main Sessionhandler.
        Kwargs:
            uid (int): Bot user id.
            botname (str): Bot name (seen in IRC channel).
            channel (str): IRC channel to connect to.
            network (str): Network address to connect to.
            port (str): Port of the network.
            ssl (bool): Indicates SSL connection.
        """
        self.sessionhandler = sessionhandler
        self.uid = uid
        self.nickname = str(botname)
        self.channel = str(channel)
        self.network = str(network)
        self.port = port
        self.ssl = ssl
        self.bot = None
        self.nicklists = {}

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

    def startedConnecting(self, connector):
        """
        Tracks reconnections for debugging.
        Args:
            connector (Connector): Represents the connection.
        """
        logger.log_info("(re)connecting to %s" % self.channel)

    def clientConnectionFailed(self, connector, reason):
        """
        Called when Client failed to connect.
        Args:
            connector (Connection): Represents the connection.
            reason (str): The reason for the failure.
        """
        self.retry(connector)

    def clientConnectionLost(self, connector, reason):
        """
        Called when Client loses connection.
        Args:
            connector (Connection): Represents the connection.
            reason (str): The reason for the failure.
        """
        if not (self.bot or (self.bot and self.bot.stopping)):
            self.retry(connector)

    def reconnect(self):
        """
        Force a reconnection of the bot protocol. This requires
        de-registering the session and then reattaching a new one,
        otherwise you end up with an ever growing number of bot
        sessions.
        """
        self.bot.stopping = True
        self.bot.transport.loseConnection()
        self.sessionhandler.server_disconnect(self.bot)
        self.start()

    def start(self):
        """
        Connect session to sessionhandler.
        """
        if self.port:
            if self.ssl:
                try:
                    from twisted.internet import ssl
                    service = reactor.connectSSL(self.network, int(self.port), self, ssl.ClientContextFactory())
                except ImportError:
                    logger.log_err("To use SSL, the PyOpenSSL module must be installed.")
            else:
                service = internet.TCPClient(self.network, int(self.port), self)
            self.sessionhandler.portal.services.addService(service)
