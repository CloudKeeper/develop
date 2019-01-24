"""
IRC2Puppet - TO BE TESTED

-Code appears to fall asleep if left too long.

Cloud_Keeper 2018

This is a bare-bones version of the IRC2Puppet bot. This connects an Evennia
location to an IRC channel. This is achieved by having a hidden 'listener'
object in the room which sends say and pose messages to a bot (the Portal Bot)
connected to IRC. The Portal Bot communicates what it receives to the IRC
channel E.g.
        MUDUser says, "Hi There" -> <IRC2Puppet> MUDUser: Hi There
        
The PortalBot then communicates what is said in IRC back to Evennia via the
AccountBot. The AccountBot creates a puppet for each user inside the IRC
channel in the same room as the listener object and causes the puppets to mimic
what is said and posed in IRC.

Evennia to IRC Path:
    Listener Object -> AccountBot -> PortalBot -> IRC
IRC to Evennia Path:
    IRC -> PortalBot -> AccountBot -> Puppet Objects
Helper Functions:
    AccountBot Start & Delete Functions
    PortalFactory
IRC2Puppet Command.

Install Instructions:
    1. Ensure IRC is enabled in your games settings file.
    2. Import the BotCmdSet to your character CmdSet.
    3. @irc2puppet <ircnetwork> <port> <#irchannel> <botname>
"""

import time
import hashlib
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
    **Listener Object** -> AccountBot -> PortalBot -> IRC

    This is the beginning of the Evennia to IRC Pipeline. The invisible 
    'listener' object sits in a target room catching all messages and 
    forwarding them to a bot (the AccountBot) for formatting.
    """
    def at_object_creation(self):
        """
        At creation we hide the 'listener' from view.
        """
        self.locks.add("view:perm(Immortals)")

    def msg(self, text=None, **kwargs):
        """
        Relay messages to the connected AccountBot.
        """
        if self.db.bot:
            self.db.bot.msg(text=text, **kwargs)


##############################################################################
#
# Account Bot - Evennia -> IRC
#
##############################################################################


class AccountBotOutputFunctions(Bot):
    """
    Evennia to IRC Path:
    Listener Object -> **AccountBot** -> PortalBot -> IRC

    For readability, the AccountBot has been split into parts. This portion is 
    dedicated to 'Evennia to IRC Pipeline' functionality.

    The AccountBot is a fake in-game account used by the PortalBot (a fake 
    player). The AccountBot handles recieving in-game messages and formatting
    them to be sent to the player (PortalBot). The AccountBot also handles 
    recieving external messages from the PortalBot and instigating the required 
    reaction.
    """

    def msg(self, text=None, **kwargs):
        """
        Recieve in-game messages via the Listerner Object. Format the messages
        for IRC and use the default msg() function to forward messages to the
        PortalBot.

        Common message types that will be received by the listener are:
            Messages from the 'Say' Command:
                text = ("MUDUser says, 'text'", {"type":"say"})
                kwargs = {from_obj=obj, options:[]}
            Messages from the 'Whisper' Command:
                text = ("MUSUser whispers, 'text;", {"type":"whisper"})
                kwargs = {from_obj=obj, options:[]}
            Messages from the 'Pose' Command:
                text = ("MUDUser text", {"type":"pose"})
                kwargs = {from_obj=obj, options:[]}
            Messages from the 'Look' Command and other in-game text:
                text = ("text", {"type":"look"})
                kwargs = {options:[]}
        """
        # Only allow msgs from obj that aren't my own puppets.
        if not kwargs.get("from_obj") or \
                kwargs["from_obj"].tags.get(self.key+"-puppet", default=None):
            return

        # Only allow msgs with type tag...
        if isinstance(text, tuple):
            msg = text[0]
            if text[1].get("type") == "pose":
                # msg is already in the format for IRC actions 'MUDUser poses'
                super().msg(channel=msg)
                return

            if text[1].get("type") == "say":
                # Turn 'MUDUser says, "string"' to 'MUDUser: Hi There'
                msg = kwargs["from_obj"].key + ": " + msg.split('"', 1)[1][:-1]
                super().msg(channel=msg)
                return

    def get_nicklist(self, caller=None):
        """
        Send a request for the nicklist from the connected channel.

        Args:
            caller (Object or Account): The requester of the list. This will
                be stored and echoed to when the irc network replies with the
                requested info. If None, then the Bot is the caller using the 
                list to populate puppets.

        Notes: Since the return is asynchronous, the caller is stored internally
            in a list; all callers in this list will get the nick info once it
            returns (it is a custom OOB inputfunc option). The callback will not
            survive a reload (which should be fine, it's very quick).
        """
        if not hasattr(self, "_nicklist_callers"):
            self._nicklist_callers = []
        if caller:
            self._nicklist_callers.append(caller)
        super().msg(request_nicklist="")
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
    portion of the PortalBot receives output messages from Evennia and sends 
    them to the IRC channel. No formatting is done at this stage.
    """

    # def send_channel(self, *args, **kwargs):
    #     """
    #     # We use default behaviour. For Information only.#
    # 
    #     Send channel text to IRC channel (visible to all). Note that
    #     we don't handle the "text" send (it's rerouted to send_default
    #     which does nothing) - this is because the IRC bot is a normal
    #     session and would otherwise report anything that happens to it
    #     to the IRC channel (such as it seeing server reload messages).
    #     Args:
    #         text (str): Outgoing text
    #     """
    #     text = args[0] if args else ""
    #     if text:
    #         text = parse_ansi_to_irc(text)
    #         self.say(self.channel, text)

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
    IRC -> **PortalBot** -> AccountBot -> Puppet Objects

    The PortalBot is a fake player which connects to an IRC channel. This
    is a continuation of the PortalBot. This portion handles receiving messages
    from IRC and sending them back to Evennia.
    """

    def privmsg(self, user, channel, msg):
        """
        Called when the connected channel receives a message.
        Also called when this Bot recieves a personal message.

        Args:
            user (str): User name sending the message.
            channel (str): Channel name seeing the message. Or this Bots name
                           if recieving a personal message.
            msg (str): The message arriving from channel.

        """
        # Respond to private messages with a little bit of information.
        if channel == self.nickname:
            user = user.split('!', 1)[0]
            pm_response = ("This is an Evennia IRC bot connecting from "
                           "'%s'." % settings.SERVERNAME)
            self.send_privmsg(pm_response, user=user)

        # Regula Channel Message - We pass messages to our Server Bot.
        elif not msg.startswith('***'):
            user = user.split('!', 1)[0]
            user = ansi.raw(user)
            self.data_in(text=msg, type="msg", user=user, channel=channel)

    def joined(self, channel):
        """
        Called when I finish joining a channel.
        """
        # Return user list to Server bot to set up puppets.
        self.get_nicklist()

    def userJoined(self, user, channel):
        """
        Called when I see another user joining a channel.
        """
        # Send action to AccountBot.
        self.data_in(text="joined", type="joined", user="server",
                     channel=channel, nicklist=[user])

    def userRenamed(self, oldname, newname):
        """
        A user changed their name from oldname to newname.
        """
        # Send action to AccountBot.
        self.data_in(text="renamed", type="renamed", oldname=oldname,
                     newname=newname)

    def userLeft(self, user, channel):
        """
        Called when I see another user leaving a channel.
        """
        # Send action to AccountBot.
        self.data_in(text="left", type="left", user="server",
                     channel=channel, nicklist=[user])

##############################################################################
#
# Account Bot - IRC -> Evennia
#
##############################################################################


class AccountBotInputFunctions(Bot):
    """
    IRC to Evennia Path:
    IRC -> PortalBot -> **AccountBot** -> Puppet Objects

    This portion of the AccountBot is dedicated to 'IRC to Evennia Pipeline' 
    functionality.

    The AccountBot is a fake in-game account used by the PortalBot (a fake 
    player). The AccountBot handles recieving in-game messages and formatting
    them to be sent to the player (PortalBot). The AccountBot also handles 
    recieving external messages from the PortalBot and instigating the required 
    reaction.
    """

    def execute_cmd(self, session=None, txt=None, **kwargs):
        """
        Take incoming data and make the appropriate action. This acts as a
        CommandHandler of sorts for the various "type" of actions the PortalBot 
        returns to the Evennia. This is triggered by the bot_data_in Inputfunc.

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

            # Called by AccountBot to initiate puppets.
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
                puppetdict[oldname].key = newname
                puppetdict[newname] = puppetdict.pop(oldname)
                self.db.ev_location.msg_contents(
                    oldname + " has become " + newname)
                return

        elif kwargs["type"] == "left":
            """
            Returned when a user leaves a channel - Pack up puppet.
            """
            for nick in kwargs["nicklist"]:
                nick = ansi.strip_ansi(nick)
                if nick in self.db.puppetdict:
                    self.db.puppetdict[nick].move_to(None, to_none=True)
                    self.db.ev_location.msg_contents(nick + self.db.puppetexitmsg)
                    del self.db.puppetdict[nick]
            return

        elif kwargs["type"] == "action":
            """
            Returned when a user uses /me in IRC
            Causes in-game puppet to act out pose.
            """
            nick = ansi.strip_ansi(kwargs["user"])
            if nick in self.db.puppetdict:
                self.db.puppetdict[nick].execute_cmd("pose " + txt)
            return

        else:
            """
            Everything else is assumed to be text to speak.
            Cause the puppet to say the message.
            """
            nick = ansi.strip_ansi(kwargs["user"])
            if nick in self.db.puppetdict:
                self.db.puppetdict[nick].execute_cmd("say " + txt)
            return

##############################################################################
#
# Puppet Object - IRC -> Evennia
#
##############################################################################


class Puppet(Character):
    """
    IRC to Evennia Path:
    IRC -> PortalBot -> AccountBot -> **Puppet Objects**

    This implements a character object intended to be controlled remotely by
    the PuppetBot. Each user on the target IRC channel will be represented by
    a Puppet object and all communication will be through the puppet object
    using the execute_cmd method.
    """
    pass

##############################################################################
#
# SETUP FUNCTIONS
#
##############################################################################


class AccountBot(AccountBotOutputFunctions, AccountBotInputFunctions):
    """
    This portion of the AccountBot is dedicated to setup and support functions.

    The AccountBot is a fake in-game account used by the PortalBot (a fake 
    player). The AccountBot handles recieving in-game messages and formatting
    them to be sent to the player (PortalBot). The AccountBot also handles 
    recieving external messages from the PortalBot and instigating the required 
    reaction.
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

        # if keywords are given, store (the BotStarter script will not give any 
        # keywords, so this should normally only happen at initialization)
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
        self.db.puppetentrymsg = " appears in the room."
        self.db.puppetexitmsg = " has left the room."
        self.db.puppetdefaultdesc = "This is a Puppet."
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
        _SESSIONS.start_bot_session("typeclasses.irc2puppet.PortalBotFactory", configdict)

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

    def prep_listener(self):
        """
        Create a listener object to be placed in the target room.

        Triggered when first connecting to an IRC channel.
        """
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
                      if puppet.key == nick]

        # Use an existing puppet.
        if puppetlist:
            puppetdict[nick] = puppetlist[0]
            if not puppetdict[nick].location == self.db.ev_location:
                puppetdict[nick].move_to(self.db.ev_location, quiet=True)
                self.db.ev_location.msg_contents(puppetdict[nick].key + self.db.puppetentrymsg)

        # Create a new puppet.
        else:
            puppetdict[nick] = create.create_object(Puppet, key=nick,
                                                    location=self.db.ev_location)
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
        super().delete(*args, **kwargs)


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
        self.add(CmdIRC2Puppet())


class CmdIRC2Puppet(COMMAND_DEFAULT_CLASS):
    """
    Link an Evennia location to an external IRC channel.
    The location will be populated with puppet characters for each user in IRC.

    Usage:
        @irc2puppet # lists all bots currently active.
        @irc2puppet <ircnetwork> <port> <#irchannel> <botname>
        @irc2puppet irc.freenode.net 6667 #irctest mud-bot
        @irc2puppet/delete botname|#dbid

    Switches:
        /ping       - Fire a ping to the IRC server.
        /who        - Returns user list in IRC channel.
        /delete     - this will delete the bot and remove the irc connection
                      to the channel. Requires the botname or #dbid as input.
        /reconnect  - Force a protocol-side reconnect of the client without
                      having to destroy/recreate the bot "account".
        /reload     - Delete all puppets, recreates puppets from new user list.

        /ignore     - Toggle ignore IRC user. Neither puppet or msgs will be visible.
    """
    key = "@irc2puppet"
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
            self.msg("Account '%s' already exists." % botname)
            return
        else:
            password = "useruser"
            try:
                bot = create.create_account(botname, None, password,
                                            typeclass=AccountBot)
            except Exception as err:
                self.msg("|rError, could not create the bot:|n '%s'." % err)
                return
        bot.start(ev_location=location, irc_botname=irc_botname,
                  irc_channel=irc_channel, irc_network=irc_network,
                  irc_port=irc_port)
        self.msg("Connection created. Starting IRC bot.")
