"""
IRC2Puppet - INOPERABLE

Cloud_Keeper 2018

This connects an Evennia location to an IRC channel. This is achieved by having
a hidden 'listener' object in the room which sends conversation to a bot (the
Portal Bot) connected to IRC. The Portal Bot communicates what it receives to
the IRC channel eg. '<IRC2Puppet> MUDUser: Hi There'. The Portal Bot then
communicates what is said in IRC back to Evennia via the Server Bot. The
Server Bot creates a puppet for each user inside the IRC channel in the same
room as the listener object and causes the puppets to mimic what is said in IRC.

Evennia to IRC Pipeline:
Listener Object -> Server Bot -> Portal Bot -> IRC

IRC to Evennia Pipeline:
IRC -> Portal Bot -> inputfunc.bot_data_in -> Server Bot -> Puppet Objects

This is meant as a simple version of the IRC2Puppet bot.

Instructions:
    1. Ensure IRC is enabled in your games settings file.
    2. Import the BotCmdSet to your character CmdSet.
    3. @puppetbot <irc_network> <port> <#irchannel> <object_name>

# -----------------------------------------------------------------------------
NOTES:

# -----------------------------------------------------------------------------
"""

from typeclasses.objects import Object
from evennia.accounts.bots import Bot

##############################################################################
#
# Listener Object
#
##############################################################################


class Listener(Object):
    """
    Evennia to IRC Pipeline:
    **Listener Object** -> Server Bot -> Portal Bot -> IRC

    This is the beginning of the Evennia to IRC Pipeline. The 'listener' object
    sits in a target room and sends conversations it overhears to a bot (the
    Portal Bot) connected to IRC.
    """
    def at_object_creation(self):
        """
        At creation we hide the 'listener' from view.
        """
        self.locks.add("view:perm(Immortals)")

    def msg(self, text=None, **kwargs):
        """
        Relay messages to the Portal Bot via the Server Bot.
        """
        if self.db.bot:
            self.db.bot.msg(text=text, **kwargs)


class ServerBot(Bot):
    """
    Evennia to IRC Pipeline:
    Listener Object -> **Server Bot** -> Portal Bot -> IRC

    For readability, the Server Bot has been split into two parts. This is the
    first half, dedicated to 'Evennia to IRC Pipeline' functionality.

    Where as the Portal Bot is a fake player (external to Evennia) the Server
    bot is the fake players account. In the same way that a real players
    account handles sending messages to the players client (whether it be
    telnet, the webclient or otherwise) the Server Bot handles receiving
    messages (from the listener object) and sending them to the fake player.
    """

    def msg(self, text=None, **kwargs):
        """
        Receive text via the listener object and send to IRC via the Portal Bot.

        Common message types that will be received by the listener are:
            Say msg: text = ("text", {"type":say"})
                     kwargs = {from_obj=obj, session=session, options:[]}
            Whisper msg: text = ("text", {"type":whisper"})
                         kwargs = {from_obj=obj, session=session, options:[]}
            Pose msg: text = ("text", {"type":whisper"})
                      kwargs = {from_obj=obj, session=session, options:[]}
            Misc msg: text = "text"
                      kwargs = {from_obj=obj, session=session, options:[]}

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
        if not kwargs.get("from_obj"):
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
