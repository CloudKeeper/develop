"""
IRC Puppet Bot.

Cloud_Keeper 2017

This connects an Evennia room to an IRC channel, creating a puppet character
for each user in the IRC channel. The bot pipes what is said by users on IRC
to the corresponding puppet in the room.

Features:
    -Connect an IRC channel to Evennia where the IRC users become chatty NPCs.
    -Connect two IRC channels by having two IRCbots in the same location.
        Bots talking from one channel will be communicated to the other channel
        and appear as if they were MUD accounts talking.
        (If the same user is in both channels there will be two user puppets)
    -IRC users can interact with the bot with Who, About, Look, Whisper & Desc
    -Changable about message to return to IRC users.

    -Handles accounts joining/leaving channel and change of names.
    -Changable prefix/suffix on puppet objects
    -Changable descriptions on puppet objects by IRC users.
    -Changable default descriptions for puppets with soft and hard reloads.
    -

To Use:
    Ensure IRC is enabled in your games settings file.
    Put ircpuppetbot.py in your typeclasses folder
    Import the BotCmdSet to your character CmdSet.
    Use the PuppetBot command as described in the help menu.

IRC Private Message Commands:
    "Who": Return a list of online MUD users
    "About": Returns information about the MUD
    "Look" : Look at the Evennia location and those within it.
             E.g. "look" or "look chair"
    "Desc" : If empty, shows users in-game bots description. Else, sets
             bots in-game bot description to given value.
    All other messages return this help message.'

In Game Command Usage:
    @puppetbot # lists all bots currently active.
    @puppetbot <ircnetwork> <port> <#irchannel> <botname>
    @puppetbot/delete botname|#dbid
    @puppetbot/defaultdesc botname|#dbid = <new description>
    @puppetbot/forcedesc botname|#dbid

Switches:
    /about      - set about message to be returned in IRC if bot PM'd "about"
    /ping       - Fire a ping to the IRC server.
    /delete     - this will delete the bot and remove the irc connection
                  to the channel. Requires the botname or #dbid as input.
    /reconnect  - Force a protocol-side reconnect of the client without
                  having to destroy/recreate the bot "account".
    /reload     - Delete all puppets, recreates puppets from new user list.

    /ignore     - Toggle ignore IRC user. Neither puppet or msgs will be visible.

    /entrymsg   - set message sent to room when user joins.
    /exitmsg    - set message sent to room when user leaves.

    /prefix     - set string put before username in puppet.key
    /suffix     - set string put after username in puppet.key

    /defaultdesc- set default description given to new puppets.
    /softdesc   - Only change noncustom puppet descriptions to new default.
    /forcedesc  - changes all bots puppets to defaultdesc.


to do:
    -Perhaps a quiet switch which doesn't send messages to the room when using commands.
    *-Change IRC nick
    -accounts entering and leaving the room
    - support emoticons etc.
    -toggle invisibility
    *-hide idle puppets?
    *-different prefix/suffix for idle puppets
    -set locks
    -Bug:
    If you have the puppetbot running, then turn off the computer/restart the
    computer, when you start back evennia will still be running but you can't
    connect to the server. Evennia stop it then evennia start it and the bot
    won't reconnect to irc I'll need to test whether the normal bot does that
    If you stop Evennia and start it again a second time it then works
    So the shutdown of a stale Evennia process doesn't shutdown/start properly
    -bot duplicted and teleported to none then tries using say command.
        
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

_SESSIONS = None

##################################
# IRCPuppetBot Commands
##################################


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
        @puppetbot <ircnetwork> <port> <#irchannel> <botname>
        @puppetbot/delete botname|#dbid
        @puppetbot/defaultdesc botname|#dbid = <new description>
        @puppetbot/forcedesc botname|#dbid

    Switches:
        /about      - set about message to be returned in IRC if bot PM'd "about"
        /ping       - Fire a ping to the IRC server.
        /who
        /delete     - this will delete the bot and remove the irc connection
                      to the channel. Requires the botname or #dbid as input.
        /reconnect  - Force a protocol-side reconnect of the client without
                      having to destroy/recreate the bot "account".
        /reload     - Delete all puppets, recreates puppets from new user list.

        /ignore     - Toggle ignore IRC user. Neither puppet or msgs will be visible.

        /entrymsg   - set message sent to room when user joins.
        /exitmsg    - set message sent to room when user leaves.

        /prefix     - set string put before username in puppet.key
        /suffix     - set string put after username in puppet.key

        /defaultdesc- set default description given to new puppets.
        /softdesc   - Only change noncustom puppet descriptions to new default.
        /forcedesc  - changes all bots puppets to defaultdesc.

        @puppetbot irc.freenode.net 6667 #irctest mud-bot
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

            # Puppetbot/entrymsg <bot> = msg - Set default puppet creation message.
            if "entrymsg" in self.switches:
                if self.rhs:
                    matches[0].db.puppetentrymsg = " " + self.rhs
                    self.msg("Bot entry message changed to: " + " " + self.rhs)
                else:
                    self.msg("No message given. Message change aborted.")
                return

            # Puppetbot/exitmsg <bot> = msg - Set default puppet deletion message.
            if "exitmsg" in self.switches:
                if self.rhs:
                    matches[0].db.puppetexitmsg = " " + self.rhs
                    self.msg("Bot exit message changed to: " + " " + self.rhs)
                else:
                    self.msg("No message given. Message change aborted.")
                return

            # Puppetbot/prefix <bot> = msg - Set string put before username in puppet.key
            if "prefix" in self.switches:
                if self.rhs:
                    matches[0].db.puppetprefix = self.rhs
                    self.msg("Puppet prefix changed to: " + self.rhs)
                    self.msg("Use: '@puppetbot/reload <bot>' to implement changes.")
                else:
                    self.msg("No message given. Prefix change aborted.")
                return

            # Puppetbot/suffix <bot> = msg - Set string put after username in puppet.key
            if "suffix" in self.switches:
                if self.rhs:
                    matches[0].db.puppetsuffix = self.rhs
                    self.msg("Puppet suffix changed to: " + self.rhs)
                    self.msg("Use: '@puppetbot/reload <bot>' to implement changes.")
                else:
                    self.msg("No message given. Suffix change aborted.")
                return

            # Puppetbot/defaultdesc <bot> = msg - Set default puppet desc message.
            if "defaultdesc" in self.switches:
                if self.rhs:
                    matches[0].db.puppetlastdesc = matches[0].db.puppetdefaultdesc
                    matches[0].db.puppetdefaultdesc = self.rhs
                    self.msg("Default puppet description changed to: " + self.rhs)
                else:
                    self.msg("No message given. Message change aborted.")
                return

            # Puppetbot/softdesc <bot> = msg - Only changes non custom puppet descriptions to new default.
            if "softdesc" in self.switches:
                puppetlist = [puppet for puppet in
                              search.search_tag(matches[0].key + "-puppet")]
                for puppet in puppetlist:
                    if puppet.db.desc == matches[0].db.puppetlastdesc:
                        puppet.db.desc = matches[0].db.puppetdefaultdesc
                self.msg("Puppets description changed to: " + matches[0].db.puppetdefaultdesc)
                return

            # Puppetbot/forcedesc <bot> = msg - Changes all puppet descriptions to new default.
            if "forcedesc" in self.switches:
                puppetlist = [puppet for puppet in
                              search.search_tag(matches[0].key + "-puppet")]
                for puppet in puppetlist:
                    puppet.db.desc = matches[0].db.puppetdefaultdesc
                self.msg("Puppets description changed to: " + matches[0].db.puppetdefaultdesc)
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

##################################
# IRCPuppetBot TypeClasses
##################################


class Puppet(Character):
    """
    This implements a character object intended to be controlled remotely by
    the PuppetBot. Each user on the target IRC channel will be represented by
    a Puppet object and all communication will be through the puppet object
    using the execute_cmd method.
    """

    STYLE = '|G'

    def msg(self, text=None, **kwargs):
        """
        Whilst the listener sends everything to the Session Bot. We only want
        to send private messages. Otherwise the Server bot would get 50 msgs
        each time something is said.
        """
        if isinstance(text, tuple) and "type" in text[1] and text[1]["type"] == "whisper":
            self.db.bot.msg(text=text, user=self.db.nick, **kwargs)


class Listener(Object):
    """
    This implements an object which sits invisible in the target room and
    relays messages to the IRCPuppetBot.
    """
    def at_object_creation(self):
        """
        Set locks so object only visible to Immortals and above.
        """
        self.locks.add("view:perm(Immortals)")

    def msg(self, text=None, **kwargs):
        """
        Relay messages to IRCPuppetBot to send to IRC.
        """
        if self.db.bot:
            self.db.bot.msg(text=text, **kwargs)


class ServerBot(Bot):
    """
    This is the Server side Bot which acts as the middle man between the Portal
    side Bot connected to IRC and the Puppets which represent each user in the
    IRC channel.

    On creation the Server side Bot creates the Portal side Bot which joins an
    IRC channel and returns all messages, actions and users to the Server Bot
    in their raw forms for processing before passing it to the relevant puppet.

    The Server side Bot creates a listener in the chosen location which returns
    all messages and actions to the Server Bot in their raw forms for
    processing before passing it through to the Portal Bot.

    When the Server Bot detects a new user a Puppet is created. All messages
    from that user will than be processed and forwarded to that Puppet through
    the execute_cmd method.
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
        super(ServerBot, self).msg(ping="")

    def reconnect(self):
        """
        Force a protocol-side reconnect of the client without
        having to destroy/recreate the bot "account".

        """
        super(ServerBot, self).msg(reconnect="")

    def msg(self, text=None, **kwargs):
        """
        Takes text from the connected location via the listener.

        We process messages here to be sent to IRC.

        Args:
            text (str, optional): Incoming text from location.

        Kwargs:
            options (dict): Options dict with the following allowed keys.
                - from_obj (list): list of objects this text.

        """
        # Only allow msgs with type tag...
        if not isinstance(text, tuple) or "type" not in text[1]:
            return
        # and from objects other than my puppets.
        if not kwargs.get("from_obj") or \
                kwargs["from_obj"].tags.get(self.key+"-puppet", default=None):
            return

        msg = text[0]

        if text[1]["type"] == "say":
            # Turn 'User says, "string"' to 'User: string'
            msg = kwargs["from_obj"].key + ": " + msg.split('"', 1)[1][:-1]
            super(ServerBot, self).msg(channel=msg)
            return

        if text[1]["type"] == "pose":
            # A pose is already the way we want it for /me: 'User string'.
            super(ServerBot, self).msg(channel=msg)
            return

        if text[1]["type"] == "whisper":
            super(ServerBot, self).msg(privmsg=((msg,), {"user": kwargs["user"]}))
            return

    def prep_listener(self):
        """
        Obtain, or create, a listener object to be placed in the target room.

        Triggered when first connecting to a IRC channel.
        """
        # Search for listener.
        listener = search.object_search(self.key+"-listener",
                                        typeclass=Listener)

        if listener:
            # Use an existing listener.
            listener = listener[0]
            listener.move_to(self.db.ev_location, quiet=True)
            self.db.listener = listener
            listener.db.bot = self
        else:
            # Create a new listener.
            listener = create.create_object(Listener, key=self.key+"-listener",
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
                      search.search_tag(self.key+"-puppet")
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
            puppetdict[nick].tags.add(self.key+"-puppet")
            puppetdict[nick].db.bot = self
            self.db.ev_location.msg_contents(puppetdict[nick].key + self.db.puppetentrymsg)
        return

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
            if hasattr(self,"_nicklist_callers") and self._nicklist_callers:
                chstr = "%s (%s:%s)" % (
                self.db.irc_channel, self.db.irc_network, self.db.irc_port)
                nicklist = ", ".join(
                    sorted(kwargs["nicklist"], key=lambda n: n.lower()))
                for obj in self._nicklist_callers:
                    obj.msg("Nicks at %s:\n %s" % (chstr, nicklist))
                self._nicklist_callers = []
                return

            else:
                # Prepare blank reference dictionary.
                self.db.puppetdict = {}

                # Prepare listener.
                self.prep_listener()

                # Prepare puppets.
                for nick in kwargs["nicklist"]:
                    self.prep_puppet(ansi.strip_ansi(nick))

                # Hide stale puppets.
                for puppet in search.search_tag(self.key+"-puppet"):
                    if puppet.location is not None \
                            and puppet not in self.db.puppetdict.values():
                        puppet.move_to(None, to_none=True)
                return

        elif kwargs["type"] == "ping":
            """
            Returned by the ping command.
            """
            if hasattr(self, "_ping_callers") and self._ping_callers:
                chstr = "%s (%s:%s)" % (self.db.irc_channel, self.db.irc_network, self.db.irc_port)
                for obj in self._ping_callers:
                    obj.msg("IRC ping return from %s took %ss." % (chstr, kwargs["timing"]))
                self._ping_callers = []
            return

        elif kwargs["type"] == "joined":
            """
            Returned when a new user joins a channel.
            """
            # Prepare puppet.
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
            newkey = self.db.puppetprefix + newname + self.db.puppetsuffix
            oldkey = self.db.puppetprefix + oldname + self.db.puppetsuffix

            # List of puppet objects matching newname.
            puppetlist = [puppet for puppet in
                          search.search_tag(self.key + "-puppet")
                          if puppet.key == newkey]

            # Use an existing puppet.
            if puppetlist:
                # Set up new puppet
                puppetdict[newname] = puppetlist[0]
                if not puppetdict[newname].location == self.db.ev_location:
                    puppetdict[newname].move_to(self.db.ev_location, quiet=True)
                    self.db.ev_location.msg_contents(
                        oldkey + " has become " + newkey)
                # Pack up old puppet
                self.db.puppetdict[oldname].move_to(None, to_none=True)
                del self.db.puppetdict[oldname]

            # Else recycle old puppet.
            elif oldname in puppetdict:
                print('Reusing puppetbot from puppetdict: ', oldname, puppetdict[oldname])
                puppetdict[oldname].key = newkey
                puppetdict[newname] = puppetdict.pop(oldname)
                self.db.ev_location.msg_contents(oldkey+" has become "+newkey)
                return

        elif kwargs["type"] == "left":
            """
            Returned when a user leaves a channel.
            """
            # Pack up puppet.
            for nick in kwargs["nicklist"]:
                nick = ansi.strip_ansi(nick)
                if nick in self.db.puppetdict:
                    self.db.puppetdict[nick].move_to(None, to_none=True)
                    self.db.ev_location.msg_contents(self.db.puppetdict[nick].key + self.db.puppetexitmsg)
                    del self.db.puppetdict[nick]
            return

        elif kwargs["type"] == "privmsg":
            """
            Returned when the bot is directly messaged.
            Users can issue commands to the Server bot through IRC PM.
            "Who" - Return a list of current users in the MUD
            "About" - Describes the bot and the connected MUD
            "Look" - Look at the Evennia location and those within it.
            "whisper" - Whisper in-game account "whisper user = msg"
            "Desc" - If empty, shows in-game bots description. Else, sets bots
                     in-game bot description to given value.
            All other messages return a help message.
            """

            user = kwargs["user"]
            
            # Who command - Returns online users in game.
            if txt.lower().startswith("who"):
                # return server WHO list (abbreviated for IRC)
                global _SESSIONS
                if not _SESSIONS:
                    from evennia.server.sessionhandler import \
                        SESSIONS as _SESSIONS
                whos = []
                t0 = time.time()
                for sess in _SESSIONS.get_sessions():
                    delta_cmd = t0 - sess.cmd_last_visible
                    delta_conn = t0 - session.conn_time
                    account = sess.get_account()
                    whos.append("%s (%s/%s)" % (utils.crop("|w%s|n" % account.name, width=25),
                                                utils.time_format(delta_conn, 0),
                                                utils.time_format(delta_cmd, 1)))
                text = "Who list (online/idle): %s" % ", ".join(sorted(whos, key=lambda w:w.lower()))

                # Return Message.
                super(ServerBot, self).msg(privmsg=((text,), {"user": user}))

            # About command - Return a blurb explaining origin of bot.
            elif txt.lower().startswith("about"):
                # some bot info
                text = self.db.botdesc

                # Return Message.
                super(ServerBot, self).msg(privmsg=((text,), {"user": user}))

            # Look command - Look at the Evennia location and those within it.
            elif txt.lower().startswith("look"):
                # Mirror in-game look command.
                txt = txt.partition(" ")[2]
                if not txt:
                    target = self.db.ev_location
                else:
                    result = search.object_search(txt, candidates=self.db.ev_location.contents)
                    target = result[0] if len(result) > 0 else None

                if not target:
                    text = "'%s' could not be located." % txt
                else:
                    text = target.return_appearance(self.db.puppetdict[user]).replace('\n', ' ')

                # Return Message.
                super(ServerBot, self).msg(privmsg=((text,), {"user": user}))

            # Desc command - If empty, shows in-game bots description. Else,
            # sets bots in-game bot description to given value.
            elif txt.lower().startswith("desc"):
                # Split text - set desc as text or return current desc if none.
                txt = txt.partition(" ")[2]
                if not txt:
                    text = self.db.puppetdict[user].db.desc
                else:
                    self.db.puppetdict[user].db.desc = txt
                    text = "Desc changed to: " + txt

                # Return Message.
                super(ServerBot, self).msg(privmsg=((text,), {"user": user}))

            # Whisper command - Whisper a user in game through a puppet.
            elif txt.lower().startswith("whisper"):

                # Parse input. Must be in form 'whisper nick = msg'
                txt = txt.split(" ", 1)[1]
                try:
                    nick, msg = txt.split("=")
                except Exception:
                    text = "Whisper Usage: 'Whisper Character = Msg'"
                    super(ServerBot, self).msg(privmsg=((text,),
                                                        {"user": user}))
                    return

                if not nick or not msg:
                    text = "Whisper Usage: 'Whisper Character = Msg'"
                    super(ServerBot, self).msg(privmsg=((text,),
                                                        {"user": user}))
                    return

                puppet = self.db.puppetdict[ansi.strip_ansi(user)]
                target = puppet.search(nick)

                if not target:
                    text = "Whisper Aborted: Character could not be found."
                    # Return Message.
                    super(ServerBot, self).msg(privmsg=((text,),
                                                        {"user": user}))
                    return

                puppet.execute_cmd("whisper " + nick + "=" + msg)
                text = 'You whisper to ' + nick + ', "' + msg + '"'
                super(ServerBot, self).msg(privmsg=((text,),
                                                    {"user": user}))
                return

            # Default message - Acts as help information.
            else:
                text = ("Command list: \n"
                        '   "Who": Return a list of online users on %s.\n'
                        '   "About": Returns information about %s.\n'
                        '   "Look": Look at the Evennia location and those within it.\n'
                        '   "Desc": If empty, shows in-game bots description. Else, sets\n'
                        '   "whisper" - Whisper in-game account "whisper user = msg"\n'
                        '           bots in-game bot description to given value.\n'
                        '   All other messages return this help message.') % (settings.SERVERNAME, settings.SERVERNAME)
                        
                # Return Message.
                super(ServerBot, self).msg(privmsg=((text,), {"user": user}))

        elif kwargs["type"] == "action":
            """
            Returned when a user uses /me in IRC
            """
            # Cause puppet to act out pose.
            if ansi.strip_ansi(kwargs["user"]) in self.db.puppetdict:
                user = ansi.strip_ansi(kwargs["user"])
                self.db.puppetdict[user].execute_cmd("pose "+txt)
            return

        else:
            """
            Everything else is assumed to be text to speak.
            """
            # Cause the puppet to say the message.
            if ansi.strip_ansi(kwargs["user"]) in self.db.puppetdict:
                user = ansi.strip_ansi(kwargs["user"])
                self.db.puppetdict[user].execute_cmd("say "+txt)
            return

    def get_nicklist(self, caller=None):
        """
        Retrive the nick list from the connected channel.

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
        super(ServerBot, self).msg(request_nicklist="")
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
                      search.search_tag(self.key+"-puppet")]
        for puppet in puppetlist:
            puppet.delete()

        # Delete bot
        self.db.ev_location.msg_contents("Bot commencing shut-down process.")
        super(ServerBot, self).delete(*args, **kwargs)


class PortalBot(IRCBot):
    """

    """
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

"""
NOTES:

Changing Nick:
TRY IRC CHANGES ONLY THEN SEE WHAT WE REALLY NEED TO CHANGE IN THE SERVERBOT.

server :
need to freshly set:
self.db.irc_botname
self.db.userignorelist = [self.db.irc_botname, "@"+self.db.irc_botname,
                              "@ChanServ", "ChanServ"]

irc:
    def setNick(self, nickname):
        "
        Set this client's nickname.
        @type nickname: C{str}
        @param nickname: The nickname to change to.
        "
        self._attemptedNick = nickname
        self.sendLine("NICK %s" % nickname)

    def irc_ERR_NICKNAMEINUSE(self, prefix, params):
        "
        Called when we try to register or change to a nickname that is already
        taken.
        "
        self._attemptedNick = self.alterCollidedNick(self._attemptedNick)
        self.setNick(self._attemptedNick)


    def alterCollidedNick(self, nickname):
        "
        Generate an altered version of a nickname that caused a collision in an
        effort to create an unused related name for subsequent registration.
        @param nickname: The nickname a user is attempting to register.
        @type nickname: C{str}
        @returns: A string that is in some way different from the nickname.
        @rtype: C{str}
        "
        return nickname + '_'

    def irc_NICK(self, prefix, params):
        "
        Called when a user changes their nickname.
        "
        nick = prefix.split('!', 1)[0]
        if nick == self.nickname:
            self.nickChanged(params[0])
        else:
            self.userRenamed(nick, params[0])

    def nickChanged(self, nick):
        "
        Called when my nick has been changed.
        "
        self.nickname = nick

IDle:
Give puppets a cmd_last_visible attribute and do a check after an interval

    def idle_time(self):
        "
        Returns the idle time of the least idle session in seconds. If
        no sessions are connected it returns nothing.
        "
        idle = [session.cmd_last_visible for session in self.sessions.all()]
        if idle:
            return time.time() - float(max(idle))
        return None
"""
