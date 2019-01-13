"""
IRC2Puppet - TO BE TESTED

Cloud_Keeper 2018

This is a simple version of an IRC2Puppet bot. This connects an Evennia
location to an IRC channel. This is achieved by having a hidden 'listener'
object in the room which sends say and pose messages to a bot (the Portal Bot)
connected to IRC. The Portal Bot communicates what it receives to the IRC
channel E.g.
        MUDUser says, "Hi There" -> <IRC2Puppet> MUDUser: Hi There
The Portal Bot then communicates what is said in IRC back to Evennia via the
AccountBot. The Server Bot creates a puppet for each user inside the IRC
channel in the same room as the listener object and causes the puppets to mimic
what is said and posed in IRC.

Table of Contents - In order of the Message Path Evennia -> IRC -> Evennia:
Evennia to IRC Path:
    Listener Object -> AccountBot -> PortalBot -> IRC
IRC to Evennia Path:
    IRC -> PortalBot -> AccountBot -> Puppet Objects
Helper Functions:
    AccountBot Start & Delete Functions
    PortalFactory
IRC2Puppet Command.

Instructions:
    1. Ensure IRC is enabled in your games settings file.
    2. Import the BotCmdSet to your character CmdSet.
    3. @puppetbot <ircnetwork> <port> <#irchannel> <botname>

### NOTES ###
Line 783. I think password cannot be None.
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

_SESSIONS = None

_DEFAULT_WIDTH = settings.CLIENT_DEFAULT_WIDTH

COMMAND_DEFAULT_CLASS = utils.class_from_module(settings.COMMAND_DEFAULT_CLASS)

##############################################################################
#
# Listener Object - Evennia -> IRC
#
##############################################################################


class Listener(Object):
    """
    Evennia to IRC Path:
    **Listener Object** -> ServerBot -> AccountBot -> IRC

    This is the beginning of the Evennia to IRC Pipeline. The simple 'listener'
    object sits in a target room catching all messages and forwarding them to a
    bot (the AccountBot) for formatting.
    """
    def at_object_creation(self):
        """
        At creation we hide the 'listener' from view.
        """
        self.locks.add("view:perm(Immortals)")

    def msg(self, text=None, **kwargs):
        """
        Relay messages to the Portal Bot via the AccountBot.
        """
        if self.db.bot:
            self.db.bot.msg(text=text, **kwargs)


class Puppet(Character):
    """
    Evennia to IRC Path:
    **Listener Object** -> ServerBot -> AccountBot -> IRC

    This implements a character object intended to be controlled remotely by
    the PuppetBot. Each user on the target IRC channel will be represented by
    a Puppet object and all communication will be through the puppet object
    using the execute_cmd method.

    The Puppets are an alternative source of messages. Whispers.
    """
    pass


##############################################################################
#
# Server Bot - Evennia -> IRC
#
##############################################################################


class AccountBotOutputFunctions(Bot):
    """
    Evennia to IRC Path:
    Listener Object -> **AccountBot** -> PortalBot -> IRC

    For readability, the Server Bot has been split into two parts. This is the
    first half, dedicated to 'Evennia to IRC Pipeline' functionality.

    Where as the PortalBot is a fake player (external to Evennia) the Account
    bot is the fake players account. In the same way that a real player
    account handles receiving game messages and sending them to the players
    client (whether it be telnet, the webclient or otherwise) the AccountBot
    handles receiving messages (from the listener object) and sending them to
    the fake player.
    """

    def msg(self, text=None, **kwargs):
        """
        Receive text via the Listener Object and send to IRC via the PortalBot
        after changing the messages to an IRC format.
        By ultimately running super.msg(channel=msg) it will call the
        send_channel method on the corresponding Portal connection.

        Common message types that will be received by the listener are:
            Messages from the 'Say' Command:
                text = ("MUDUser says, 'text'", {"type":say"})
                kwargs = {from_obj=obj, session=session, options:[]}
            Messages from the 'Whisper' Command:
                text = ("MUSUser whispers, 'text;", {"type":"whisper"})
                kwargs = {from_obj=obj, session=session, options:[]}
            Messages from the 'Pose' Command:
                text = ("MUDUser text", {"type":"pose"})
                kwargs = {from_obj=obj, session=session, options:[]}
            Messages from the 'Look' Command and other game text:
                text = "text"
                kwargs = {from_obj=obj, session=session, options:[]}
        """
        # Only allow msgs with type tag...
        if isinstance(text, tuple):
            msg = text[0]
            if text[1].get("type") == "pose":
                # The msg is already in the format for IRC actions 'MUDUser poses'
                super(AccountBotOutputFunctions, self).msg(channel=msg)
                return

            if text[1].get("type") == "say":
                # Turn 'MUDUser says, "string"' to 'MUDUser: Hi There'
                msg = kwargs["from_obj"].key + ": " + msg.split('"', 1)[1][:-1]
                super(AccountBotOutputFunctions, self).msg(channel=msg)
                return

    def get_nicklist(self, caller=None):
        """
        Send a request for the nick listed from the connected channel.

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
        if caller:
            self._nicklist_callers.append(caller)
        super(AccountBotOutputFunctions, self).msg(request_nicklist="")
        return

##############################################################################
#
# Portal Bot - Evennia -> IRC
#
##############################################################################


class PortalBot(IRCBot):
    """
    Evennia to IRC Path:
    Listener Object -> AccountBot -> **PortalBot** -> IRC

    The PortalBot is a fake player which connects to an IRC channel. This
    portion of the PortalBot receives Evennia messages forwarded by the
    Listener and sends it to the IRC channel.
    """

    # def send_channel(self, *args, **kwargs):
    #     """
    #     Send a message to the connected IRC channel. The base functionality
    #     is suitable for our purposes. For Information Only.
    #     """

##############################################################################
#
# IRC to Evennia Path:
#     IRC -> PortalBot -> AccountBot -> Puppet Objects
#
##############################################################################
#
# Portal Bot - IRC -> Evennia
#
##############################################################################
    """
    IRC to Evennia Path:
    IRC -> *PortalBot* -> AccountBot -> Puppet Objects

    The PortalBot is a fake player which connects to an IRC channel. This
    is a continuation of the PortalBot. This portion handles receiving messages
    from IRC and sending them back to Evennia.
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

        # We pass regular channel messages to our Server Bot.
        elif not msg.startswith('***'):
            user = user.split('!', 1)[0]
            user = ansi.raw(user)
            self.data_in(text=msg, type="msg", user=user, channel=channel)

    def joined(self, channel):
        """
        Called when I finish joining a channel.
        channel has the starting character (C{'#'}, C{'&'}, C{'!'}, or C{'+'})
        intact.
        """
        # Return user list to Server bot.
        self.get_nicklist()

    def userJoined(self, user, channel):
        """
        Called when I see another user joining a channel.
        """
        # Send messasge to Server bot.
        self.data_in(text="", type="joined", user="server", channel=channel,
                     nicklist=[user])

    def userRenamed(self, oldname, newname):
        """
        A user changed their name from oldname to newname.
        """
        # Send messasge to Server bot.
        self.data_in(text="", type="renamed", oldname=oldname, newname=newname)

    def userLeft(self, user, channel):
        """
        Called when I see another user leaving a channel.
        """
        # Send messasge to Server bot.
        self.data_in(text="", type="left", user="server", channel=channel,
                     nicklist=[user])

##############################################################################
#
# Server Bot - IRC -> Evennia
#
##############################################################################


class AccountBot(AccountBotOutputFunctions):
    """

    """

    def execute_cmd(self, session=None, txt=None, **kwargs):
        """
        Take incoming data and make the appropriate action. This acts as a
        CommandHandler of sorts for the various "type" of actions the Portal
        bot returns to the Server. This is triggered by the bot_data_in
        Inputfunc.

        Args:
            session (Session, optional): Session responsible for this
                command. Note that this is the bot.
            txt (str, optional):  Command string.
        Kwargs:
            user (str): The name of the user who sent the message.
            channel (str): The name of channel the message was sent to.
            nicklist (list, optional): Set if `type='nicklist'`. This is a
                                       list of nicks returned by calling
                                       the `self.get_nicklist`. It must look
                                       for a list `self._nicklist_callers`
                                       which will contain all callers waiting
                                       for the nicklist.
            timings (float, optional): Set if `type='ping'`. This is the return
                                       (in seconds) of a ping request triggered
                                       with `self.ping`. The return must look
                                       for a list `self._ping_callers` which
                                       will contain all callers waiting for
                                       the ping return.
            type (str): The type of response returned by the IRC bot.
                        Including:
                        "nicklist": Returned when first joining a channel.
                        "joined": Returned when a new user joins a channel.
                        "left": Returned when a user leaves a channel.
                        "privmsg": Returned when the bot is directly messaged.
                        "action": Returned when a user uses /me in IRC
                        Everything else is assumed to be text to speak.
        """
        if kwargs["type"] == "nicklist":
            """
            Returned when first joining a channel.
            """
            # Send Nicklist to requesting players
            if hasattr(self, "_nicklist_callers") and self._nicklist_callers:
                chstr = "%s (%s:%s)" % (self.db.irc_channel,
                                        self.db.irc_network, self.db.irc_port)
                nicklist = ", ".join(sorted(kwargs["nicklist"],
                                            key=lambda n: n.lower()))
                for obj in self._nicklist_callers:
                    obj.msg("Nicks at %s:\n %s" % (chstr, nicklist))
                self._nicklist_callers = []
                return

            # Called by Session to initiate puppets.
            else:
                self.prep_listener()

                # Prepare puppets
                self.db.puppetdict = {}
                for nick in kwargs["nicklist"]:
                    self.prep_puppet(ansi.strip_ansi(nick))

                # Hide stale puppets.
                for puppet in search.search_tag(self.key + "-puppet"):
                    if puppet.location is not None \
                            and puppet not in self.db.puppetdict.values():
                        puppet.move_to(None, to_none=True)
                return

        elif kwargs["type"] == "ping":
            """
            Returned by the ping command.
            """
            if hasattr(self, "_ping_callers") and self._ping_callers:
                chstr = "%s (%s:%s)" % (self.db.irc_channel,
                                        self.db.irc_network, self.db.irc_port)
                for obj in self._ping_callers:
                    obj.msg("IRC ping return from %s took %ss." % (chstr, kwargs["timing"]))
                self._ping_callers = []
            return

        elif kwargs["type"] == "joined":
            """
            Returned when a new user joins a channel - Prepare Puppet
            """
            for nick in kwargs["nicklist"]:
                self.prep_puppet(ansi.strip_ansi(nick))
            return

        elif kwargs["type"] == "renamed":
            """
            Returned when IRC user changes nick.
            """
            puppetdict = self.db.puppetdict
            newname = kwargs["newname"]
            oldname = kwargs["oldname"]

            # List of puppet objects matching newname.
            puppetlist = [puppet for puppet in
                          search.search_tag(self.key + "-puppet")
                          if puppet.key == newname]

            # Use an existing puppet.
            if puppetlist:
                # Set up new puppet
                puppetdict[newname] = puppetlist[0]
                if not puppetdict[newname].location == self.db.ev_location:
                    puppetdict[newname].move_to(self.db.ev_location, quiet=True)
                    self.db.ev_location.msg_contents(
                        oldname + " has become " + newname)
                # Pack up old puppet
                self.db.puppetdict[oldname].move_to(None, to_none=True)
                del self.db.puppetdict[oldname]

            # Else recycle old puppet.
            elif oldname in puppetdict:
                print('Reusing puppetbot from puppetdict: ', oldname, puppetdict[oldname])
                puppetdict[oldname].key = newname
                puppetdict[newname] = puppetdict.pop(oldname)
                self.db.ev_location.msg_contents(oldname + " has become " + newname)
                return

        elif kwargs["type"] == "left":
            """
            Returned when a user leaves a channel - Pack up puppet.
            """
            for nick in kwargs["nicklist"]:
                nick = ansi.strip_ansi(nick)
                if nick in self.db.puppetdict:
                    self.db.puppetdict[nick].move_to(None, to_none=True)
                    self.db.ev_location.msg_contents(self.db.puppetdict[nick].key + self.db.puppetexitmsg)
                    del self.db.puppetdict[nick]
            return

        elif kwargs["type"] == "action":
            """
            Returned when a user uses /me in IRC
            Causes in-game puppet to act out pose.
            """
            if ansi.strip_ansi(kwargs["user"]) in self.db.puppetdict:
                self.db.puppetdict[ansi.strip_ansi(kwargs["user"])].execute_cmd("pose " + txt)
            return

        else:
            """
            Everything else is assumed to be text to speak.
            Cause the puppet to say the message.
            """
            if ansi.strip_ansi(kwargs["user"]) in self.db.puppetdict:
                self.db.puppetdict[ansi.strip_ansi(kwargs["user"])].execute_cmd("say " + txt)
            return

##############################################################################
#
# SETUP FUNCTIONS
#
##############################################################################
    """
    
    """

    def start(self, ev_location=None, irc_botname=None, irc_channel=None,
              irc_network=None, irc_port=None, irc_ssl=None):
        """
        Start by telling the portal to start a new session.

        Args:
            ev_location (obj): The Evennia location to connect to.
            irc_botname (str): Name of bot to connect to irc channel. If
                not set, use `self.key`.
            irc_channel (str): Name of channel on the form `#channelname`.
            irc_network (str): URL of the IRC network, like `irc.freenode.net`.
            irc_port (str): Port number of the irc network, like `6667`.
            irc_ssl (bool): Indicates whether to use SSL connection.

        """
        global _SESSIONS
        if not _SESSIONS:
            from evennia.server.sessionhandler import SESSIONS as _SESSIONS

        # if keywords are given, store (the BotStarter script
        # will not give any keywords, so this should normally only
        # happen at initialization)
        if ev_location:
            self.db.ev_location = ev_location
        if irc_botname:
            self.db.irc_botname = irc_botname
        elif not self.db.irc_botname:
            self.db.irc_botname = self.key
        if irc_channel:
            self.db.irc_channel = irc_channel
        if irc_network:
            self.db.irc_network = irc_network
        if irc_port:
            self.db.irc_port = irc_port
        if irc_ssl:
            self.db.irc_ssl = irc_ssl

        # Default bot values.
        self.db.botdesc = "This is an Evennia IRC bot connecting from '%s'." % settings.SERVERNAME

        self.db.puppetdict = {}
        self.db.puppetprefix = ""
        self.db.puppetsuffix = ""
        self.db.puppetentrymsg = " appears in the room."
        self.db.puppetexitmsg = " has left the room."
        self.db.puppetdefaultdesc = "This is a Puppet."
        self.db.puppetlastdesc = "This is a Puppet."
        self.db.userignorelist = [self.db.irc_botname, "@"+self.db.irc_botname,
                                  "@ChanServ", "ChanServ"]

        # instruct the server and portal to create a new session with
        # the stored configuration
        configdict = {"uid": self.dbid,
                      "botname": self.db.irc_botname,
                      "channel": self.db.irc_channel,
                      "network": self.db.irc_network,
                      "port": self.db.irc_port,
                      "ssl": self.db.irc_ssl}
        _SESSIONS.start_bot_session("typeclasses.ircpuppetbot.PortalBotFactory", configdict)

    def ping(self, caller):
        """
        Fire a ping to the IRC server.

        Args:
            caller (Object or Account): The requester of the ping.

        """
        if not hasattr(self, "_ping_callers"):
            self._ping_callers = []
        self._ping_callers.append(caller)
        super(AccountBot, self).msg(ping="")

    def reconnect(self):
        """
        Force a protocol-side reconnect of the client without
        having to destroy/recreate the bot "account".

        """
        super(AccountBot, self).msg(reconnect="")

    def prep_listener(self):
        """
        Obtain, or create, a listener object to be placed in the target room.

        Triggered when first connecting to a IRC channel.
        """
        # Search for listener.
        listener = search.object_search(self.key + "-listener",
                                        typeclass=Listener)

        if listener:
            # Use an existing listener.
            listener = listener[0]
            listener.move_to(self.db.ev_location, quiet=True)
            self.db.listener = listener
            listener.db.bot = self
        else:
            # Create a new listener.
            listener = create.create_object(Listener, key=self.key + "-listener",
                                            location=self.db.ev_location)
            self.db.listener = listener
            listener.db.bot = self

    def prep_puppet(self, nick):
        """
        This method will find an existing puppet or create a puppet of
        a given name. It will then teleport the puppet to the location
        and keep a reference to more easily facilitate passing commands to.

        Used when first connecting to a IRC channel or a new user joins.

        Args:
            nick (str): The name of the user the puppet will represent.
        """
        # Ignore bot and automatic users.
        if nick in self.db.userignorelist:
            return

        puppetdict = self.db.puppetdict

        # List of puppet objects with matching name.
        puppetlist = [puppet for puppet in
                      search.search_tag(self.key + "-puppet")
                      if puppet.key == self.db.puppetprefix + nick + self.db.puppetsuffix]

        # Use an existing puppet.
        if puppetlist:
            puppetdict[nick] = puppetlist[0]
            if not puppetdict[nick].location == self.db.ev_location:
                puppetdict[nick].move_to(self.db.ev_location, quiet=True)
                self.db.ev_location.msg_contents(puppetdict[nick].key + self.db.puppetentrymsg)

        # Create a new puppet.
        else:
            puppetdict[nick] = create.create_object(Puppet, key=self.db.puppetprefix + nick + self.db.puppetsuffix,
                                                    location=self.db.ev_location)
            puppetdict[nick].db.nick = nick
            puppetdict[nick].db.desc = self.db.puppetdefaultdesc
            puppetdict[nick].tags.add(self.key + "-puppet")
            puppetdict[nick].db.bot = self
            self.db.ev_location.msg_contents(puppetdict[nick].key + self.db.puppetentrymsg)
        return

    def delete(self, *args, **kwargs):
        """
        Deletes the bot permanently.

        Notes:
            `*args` and `**kwargs` are passed on to the base delete
             mechanism (these are usually not used).

        """
        # Delete listener
        if self.db.listener:
            self.db.listener.delete()

        # Delete puppets
        puppetlist = [puppet for puppet in
                      search.search_tag(self.key + "-puppet")]
        for puppet in puppetlist:
            puppet.delete()

        # Delete bot
        self.db.ev_location.msg_contents("Bot commencing shut-down process.")
        super(AccountBot, self).delete(*args, **kwargs)


class PortalBotFactory(IRCBotFactory):
    """
    Creates instances of IRCBot, connecting with a staggered
    increase in delay

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
# IRC2Puppet Commands
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
    Link an Evennia location to an external IRC channel.
    The location will be populated with puppet characters for each user in IRC.

    Usage:
        @puppetbot # lists all bots currently active.
        @puppetbot irc.freenode.net 6667 #irctest mud-bot
        @puppetbot <ircnetwork> <port> <#irchannel> <botname>
        @puppetbot/delete botname|#dbid

    Switches:
        /ping       - Fire a ping to the IRC server.
        /who
        /delete     - this will delete the bot and remove the irc connection
                      to the channel. Requires the botname or #dbid as input.
        /reconnect  - Force a protocol-side reconnect of the client without
                      having to destroy/recreate the bot "account".
        /reload     - Delete all puppets, recreates puppets from new user list.

        /ignore     - Toggle ignore IRC user. Neither puppet or msgs will be visible.
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
                                            typeclass=AccountBot)
            except Exception as err:
                self.msg("|rError, could not create the bot:|n '%s'." % err)
                return
        bot.start(ev_location=location, irc_botname=irc_botname,
                  irc_channel=irc_channel, irc_network=irc_network,
                  irc_port=irc_port)
        self.msg("Connection created. Starting IRC bot.")
