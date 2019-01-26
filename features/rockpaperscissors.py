"""
Scissor Paper Rock Battle System. - TO BE TESTED
"""
import random
from evennia import DefaultScript
import itertools
from django.conf import settings
from evennia import create_script
from evennia import CmdSet
from typeclasses import characters
from evennia.utils.utils import class_from_module


COMMAND_DEFAULT_CLASS = class_from_module(settings.COMMAND_DEFAULT_CLASS)

##############################################################################
#
# Rock Paper Scissors Battle Command
#
##############################################################################


class CombatCmdSet(CmdSet):
    """The battle related commands available to all characters."""
    key = "combat_cmdset"
    priority = 1

    def at_cmdset_creation(self):
        self.add(CmdBattle())


class CmdBattle(COMMAND_DEFAULT_CLASS):
    """
    Initiates Rock Paper Scissors

    Usage:
        battle <participant>
        battle <participant>, <participant>, ...]
    """
    key = "battle"
    aliases = ["challenge", "fight"]
    help_category = "General"

    def func(self):
        """We want to send a list of player objects to the Handler"""
        caller = self.caller
        participants = []

        if not self.args:
            caller.msg("Battle whom?")
            return

        for char in self.lhslist:
            char = caller.search(char)

            if not char:
                caller.msg("A target could not be located.")
                return
            if not isinstance(char, characters.Character):
                caller.msg("A target is not the right typeclass to battle.")
                return
            if char.ndb.combat_handler:
                caller.msg("A target is already in battle.")
                return
            if char in participants:
                caller.msg("A target was named twice.")
                return

            participants.append(char)

        handler = create_script(CombatHandler)
        handler.init_battle(participants, "Challenge")

##############################################################################
#
# Combat Handler
#
##############################################################################


class CombatHandler(DefaultScript):
    """This implements the combat handler."""

    def at_script_creation(self):
        """
        Called when script is first created. Sets up values then idles.

        Args:
            phase [string]: Used by at_start() to determine what phase to
                            initialise trainers for - Challenge / Action.
            participants [dict]: Stores trainers and their action choices.
                            self.db.participants={Player1:True, Player2:None}
        """
        # Script attributes.
        self.key = "combat_handler_%i" % random.randint(1, 1000)
        self.desc = "handles combat"
        self.interval = 60 * 2  # two minute timeout
        self.start_delay = True
        self.persistent = True

        # Battle attributes.
        self.db.phase = "Challenge"
        self.db.participants = {}

    #########################
    # At Battle Initialisation
    #########################

    def init_battle(self, participants, phase):
        """
        Initialises battles values and starting state.

        Args:
            phase [string]: Used by at_start() to determine what phase to
                            initialise trainers for - Challenge / Action.
            participants [list]: All participants.
        """
        self.db.phase = phase
        # Create dictionary from list argument.
        self.db.participants = dict.fromkeys(list(itertools.chain.from_iterable(participants)))
        self.at_start()

    def at_start(self):
        """
        This is called on first start but also when the script is restarted
        after a server reboot. We need to re-assign this combat handler to
        all characters as well as re-assign the cmdset.
        """
        if self.db.phase == "Challenge" and self.db.participants:
            for participant in self.db.participants:
                self._init_trainer_challenge(participant)

        elif self.db.phase == "Action" and self.db.participants:
            for participant in self.db.participants.keys():
                self._init_trainer_action(participant)

    #########################
    # Challenge stage
    #########################

    def _init_participant_challenge(self, participant):
        """
        Present players with an invitation to accept the battle.
        Players are given a command set with acceptance commands.
        """
        # Set up Participant.
        participant.ndb.combat_handler = self

        # Present Participant with challenge.
        participant.msg("You have been challenged to Scissor Paper Rock.")
        participant.cmdset.add(self.ChallengeCmdSet)

    class ChallengeCmdSet(CmdSet):
        """Contains response commands"""
        key = "challengecmdset"
        mergetype = "Merge"
        priority = 10
        no_exits = True

        def at_cmdset_creation(self):
            self.add(self.CmdChallengeResponse())

    class CmdChallengeResponse(COMMAND_DEFAULT_CLASS):
        """Challenge Response"""
        key = "challengeresponse"
        aliases = ["yes", "y", "accept", "no", "n", "decline"]
        help_category = "General"

        def func(self):
            """Challenge Response"""

            # >challengeresponse
            if "challengeresponse" in self.cmdstring:
                self.msg("Do you accept a challenge. Answer [Y]es or [N]o.")
                return

            # Accept Challenge
            if any(i in ['yes', 'y', 'accept'] for i in self.cmdstring):
                self.caller.msg("You have accepted the invitation.")
                self.caller.ndb.combat_handler.challenge_callback(self.caller,
                                                                  True)
                return

            # Decline Challenge
            if any(i in ['no', 'n', 'decline'] for i in self.switches):
                self.caller.msg("You have declined the invitation.")
                self.caller.ndb.combat_handler.challenge_callback(self.caller,
                                                                  False)
                return

    def challenge_callback(self, caller, response):
        """
        Receives response from players. Called by acceptance commands.
        Interacts with the trainers dictionary. On Player 1 accepting:
                self.db.participants={Player1:True, Player2:None}
        """
        if response:
            self.db.participants[caller] = True

            # If all have accepted: Trigger Action Phase
            if all(self.db.participants.values()):
                self.ndb.challenge_turn = True
                self.db.phase = "Action"
                self.force_repeat()

        # If anyone declines, rescind invitations and cancel battle.
        else:
            self.msg_all(caller.key + " has declined to battle.",
                         exceptions=[caller])
            self.stop()

    #########################
    # Action stage
    #########################

    def _init_participant_action(self, participant):
        """
        Creates pokemon commands during combat.
        """
        participant.ndb.combat_handler = self
        participant.cmdset.add(self.ActionCmdSet)

    class ActionCmdSet(CmdSet):
        """Contains action commands"""
        key = "actioncmdset"
        mergetype = "Merge"
        priority = 10
        no_exits = True

        def at_cmdset_creation(self):
            self.add(self.CmdActionResponse())

    class CmdActionResponse(COMMAND_DEFAULT_CLASS):
        """Challenge Response"""
        key = "actionresponse"
        aliases = ["rock", "r", "paper", "p", "scissors", "s"]
        help_category = "General"

        def func(self):
            """Action Response"""

            # >actionresponse
            if "actionresponse" in self.cmdstring:
                self.msg("Select an action: [R]ock, [P]aper, [S]cissors?")
                return

            # Rock Response
            if any(i in ['rock', 'r'] for i in self.cmdstring):
                self.caller.msg("You have selected Rock.")
                self.caller.ndb.combat_handler.action_callback(self.caller,
                                                               "Rock")
                return

            # Paper Response
            if any(i in ['paper', 'p'] for i in self.cmdstring):
                self.caller.msg("You have selected Paper.")
                self.caller.ndb.combat_handler.action_callback(self.caller,
                                                               "Paper")
                return

            # Scissors Response
            if any(i in ['scissors', 's'] for i in self.cmdstring):
                self.caller.msg("You have selected Scissors.")
                self.caller.ndb.combat_handler.action_callback(self.caller,
                                                               "Scissors")
                return

    def action_callback(self, caller, response):
        """
        Receives response from players. Called by action commands.
        Interacts with the trainers dictionary. On Player 1 responding:
                self.db.participants={Player1:"rock", Player2:None}
        """
        self.db.participants[caller] = response

        # If all have Responded: Trigger Action Phase
        if all(self.db.participants.values()):
            self.ndb.challenge_turn = True
            self.db.phase = "Action"
            self.force_repeat()

    #########################
    # Repeat Script
    #########################

    def at_repeat(self):
        """
        This is called every self.interval seconds (turn timeout) or
        when force_repeat is called (because everyone has entered their
        commands). We know this by checking the existence of the
        `challenge_turn` or `action_turn` NAttribute, set just before calling
        force_repeat.

        This prepares the teams for the next round.
        """
        if self.ndb.challenge_turn:
            del self.ndb.challenge_turn
            for participant in self.db.participants:
                participant.cmdset.remove(self.ChallengeCmdSet)
                self.db.participants[participant] = None
                self._init_participant_action(participant)
            self.msg_all("Select an action: [R]ock, [P]aper, [S]cissors?")

        elif self.ndb.action_turn:
            del self.ndb.action_turn
            self.action_resolution()
            self.stop()

        else:
            # turn timeout
            self.msg_all("Combat has ended due to inaction.")
            self.stop()

    #########################
    # Resolve Battle
    #########################

    def action_resolution(self):
        """
        self.db.participants={Player1:"rock", Player2:"paper"}
        """
        actions = self.db.participants
        beaten_by = {"Rock": "Paper",
                     "Paper": "Scissors",
                     "Scissors": "Rock"}
        result = dict(actions)

        for player in actions:
            if beaten_by[actions[player]] in actions.values():
                result[player] = "lost."
            else:
                result[player] = "won."

        msg = ""
        for player in result:
            msg += player.key + " has " + result[player] + ". "
        self.msg_all(msg)

    #########################
    # Script Utilities
    #########################

    def msg_all(self, message, exceptions=()):
        """
        Send message to all combatants
        """
        for trainer in self.db.trainers:
            if trainer not in exceptions:
                trainer.msg(message)

    #########################
    # Finish Script
    #########################

    def at_stop(self):
        """
        Called just before the script is stopped/destroyed.
        Conducts cleanup on each trainer connected to handler.
        """
        for participant in self.db.participants:
            self._cleanup_participant(participant)

    def _cleanup_participant(self, participant):
        """
        Remove the handler reference and cmdsets from character.
        """
        del participant.ndb.combat_handler
        participant.cmdset.remove(self.ChallengeCmdSet)
        participant.cmdset.remove(self.ActionCmdSet)

##############################################################################
#
# AI Combatant
#
##############################################################################


class AICombatant(characters.Character):
    """

    """
    def at_msg_receive(self, text=None, from_obj=None, **kwargs):
        """
        This hook is called whenever someone sends a message to this
        object using the `msg` method.
        Args:
            text (str, optional): The message received.
            from_obj (any, optional): The object sending the message.
        Kwargs:
            This includes any keywords sent to the `msg` method.
        Notes:
            If this method returns False, the `msg` operation
            will abort without sending the message.
        """

        if text is "You have been challenged to Scissor Paper Rock.":
            # Accept Challenge
            try:
                self.location.msg_contents("You dare challenge me?!")
                self.ndb.combat_handler.challenge_callback(self.caller, True)
                return True
            except:
                return True

        if text is "Select an action: [R]ock, [P]aper, [S]cissors?":
            # Choose Rock, Paper Scissors
            try:
                self.ndb.combat_handler.action_callback(self.caller, "Rock")
                return True
            except:
                return True

        return True
