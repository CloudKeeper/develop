"""
Scissor Paper Rock Game System.

This game system uses Evennia Scripts. Scripts are a class which call a 
series of function on repeat after a set time period, by default 2 minutes. 
The life cycle of class looks like:

At_Start - Called when the script is created and when repeated.
At_Repeat - Called after the set time period and recalls At_Start
At_Stop - Interrupts the loop.

At_Start <-
   |      |
 2 Mins   |   Interrupt with At_Stop
   |      |
   v      |
At_Repeat--

We can use this cycle to base our game system on. 
We'll set up the script to have a variable "phase". When At_Start is called
the script will check the "phase" it is in and take different actions:

None - The script will remain in it's loop, essentially idling.
Invitation - The script will send a messasge to any players it has been given
			 inviting them to play a game. Players will be given a command set
			 allowing them to "accept" or "decline" the invitation,
Action - The script will send a message to any players it has been given
	     inviting them to select "scissor", "paper" or "rock". 

      At_Start <------
		  |          |
   --------------    |
   |      |     |    |
 Idle  Invite Action | Interrupt with At_Stop
   |      |     |    |
   --------------    |
          |          |
          v          |
      At_Repeat-------
	  
At_Repeat will be called when all players have responded OR At_Repeat will be
called after the time limit has ran out.

If a player has refused to play, or the timer has finished without everyone
responding, the game will call At_Stop and close the game.

If all players have accepted the invitation, it will move to the action phase.
If all players have selected an action, it will calculate the winner.
"""
import random
from evennia import DefaultScript
import itertools
from django.conf import settings
from evennia import create_script
from evennia import CmdSet
from trainers.typeclasses import Trainer
from evennia.utils.utils import class_from_module


COMMAND_DEFAULT_CLASS = class_from_module(settings.COMMAND_DEFAULT_CLASS)

##############################################################################
#
# Rock Paper Scissors Battle Command
#
##############################################################################


class SPRCmdSet(CmdSet):
    """
    All characters have this command, so challenges to play Scissor Paper
    Rock can happen at any time!
    """
    key = "sprcmdset"
    priority = 1

    def at_cmdset_creation(self):
        self.add(CmdSPR())


class CmdSPR(COMMAND_DEFAULT_CLASS):
    """
    Initiates a game of Scissors Paper Rock
    
    Usage:
        spr <participant>
        spr <participant>, <participant>, ...]
        
    Collects suitable players to start a game with and starts the game scripts.
    """
    key = "spr"
    aliases = []
    help_category = "General"

    def func(self):
        """We want to send a list of player objects to the Game Handler"""
        caller = self.caller
        participants = [caller]

        # Handle no input
        if not self.args:
            caller.msg("Play with whom?")
            return

        # Obtain suitable players from listed.
        # .lhslist breaks a string into a list for us.
        for target in self.lhslist:
            participant = caller.search(target)

            if not participant:
                # Only players at your location can play.
                caller.msg(target + " could not be located.")
                return
            if not isinstance(participant, Trainer):
                # Only players can play.
                caller.msg(target + " is not able to play a game.")
                return
            if participant.ndb.game_handler:
                # Can only play one game at a time.
                caller.msg(target + " is already playing a game.")
                return
            if participant in participants:
                # Can't invite people twice (including yourself).
                continue

            participants.append(participant)

        # Create list and initialise the game.
        handler = create_script(SPRHandler)
        handler.init_game(participants, "Invitation")

##############################################################################
#
# Game Handler
#
##############################################################################


class SPRHandler(DefaultScript):
    """This implements the game handler."""

    def at_script_creation(self):
        """
        Called when script is first created. Sets up values then idles.

        """
        # Script attributes.
        self.key = "game_handler_%i" % random.randint(1, 1000)
        self.desc = "handles games"
        self.interval = 60 * 2  # two minute timeout
        self.start_delay = True

        # Start in idle with no players.
        self.db.phase = None
        self.db.participants = {}

    #########################
    # At Game Initialisation
    #########################

    def init_game(self, participants, phase):
        """
        Initialises game values and starting state. Starts the game!
        Args:
            phase [string]: Used by at_start() to determine what phase to
                            initialise trainers for - Invitation / Action.
            participants [list]: All participants.
        """
        # Set a phase
        self.db.phase = phase
        # Create dictionary from list argument.
        self.db.participants = { participant : None for participant in participants }
        # Start fresh cycle of script.
        self.at_start()

    def at_start(self):
        """
        This is called on first start and by the script itself to initialise a 
        new phase. We need to re-assign this game handler to all characters 
        as well as re-assign the cmdset.
        """
        # Set up the phase.
        if self.db.phase == "Invitation" and self.db.participants:
            for participant in self.db.participants:
                self._init_invitation(participant)

        elif self.db.phase == "Action" and self.db.participants:
            for participant in self.db.participants:
                self._init_action(participant)

    #########################
    # Invitation stage
    #########################

    def _init_invitation(self, participant):
        """
        Run for each participant.
        Present players with an invitation to accept the game.
        Players are given a command set with acceptance commands.
        The game then waits for their response.
        """
        # Set up Participant.
        participant.ndb.game_handler = self
        participant.cmdset.add(self.InvitationCmdSet)
        participant.msg(list(self.db.participants)[0].key + " challenges you to Scissor Paper Rock. Accecpt? (Y/N)")

    class InvitationCmdSet(CmdSet):
        """Contains response commands"""
        key = "invitationcmdset"
        mergetype = "Merge"
        priority = 10
        no_exits = True

        def at_cmdset_creation(self):
            self.add(self.CmdInvitationResponse())
    
        class CmdInvitationResponse(COMMAND_DEFAULT_CLASS):
            """Invitation Response"""
            key = "accept"
            aliases = ["yes", "y", "no", "n", "decline"]
            help_category = "General"
    
            def func(self):
                """Invitation Response"""
    
                # Accept Challenge - Will progress to the Action Phase
                if any(i in ['yes', 'y', 'accept'] for i in self.cmdstring):
                    self.caller.msg("You have accepted the challenge. Waiting for Opponents.")
                    self.caller.ndb.game_handler.invitation_callback(self.caller, True)
                    return
    
                # Decline Challenge - Will stop the script.
                if any(i in ['no', 'n', 'decline'] for i in self.cmdstring):
                    self.caller.msg("You have declined the challenge. Cancelling game.")
                    self.caller.ndb.game_handler.invitation_callback(self.caller, False)
                    return

    def invitation_callback(self, caller, response):
        """
        Receives responses from players. Called by acceptance commands.
        On recieving an acceptance, the script continues to count down.
        When all players accept, the script moves to the action phase.
        If any player declines, the script stops.
        If anyone doesn't accept before the time runs out, the game stops.
        """
        if response:
            # Record acceptance in player dictionary.
            self.db.participants[caller] = True
            
            # If all have accepted: Trigger Action Phase
            if all(self.db.participants.values()):
                self.ndb.invitation_turn = True
                self.db.phase = "Action"
                self.force_repeat()

        # If anyone declines, rescind invitations and cancel battle.
        else:
            self.msg_all(caller.key + " has declined to the challenge. Cancelling game.",
                         exceptions=[caller])
            self.stop()

    #########################
    # Action Stage
    #########################

    def _init_action(self, participant):
        """
        Run for each participant.
        Present players with an invitation to select action.
        Players are given a command set with available actions.
        The game then waits for their response.
        """
        participant.ndb.game_handler = self
        # The problem happens here vvvvv
        participant.cmdset.add(self.ActionCmdSet)
        participant.msg("Select an action: [R]ock, [P]aper, [S]cissors?")

    class ActionCmdSet(CmdSet):
        """Contains action commands"""
        key = "actioncmdset"
        mergetype = "Merge"
        priority = 10
        no_exits = True

        def at_cmdset_creation(self):
            self.add(self.CmdActionResponse())

        class CmdActionResponse(COMMAND_DEFAULT_CLASS):
            """Action Response"""
            key = "rock"
            aliases = ["r", "paper", "p", "scissors", "s"]
            help_category = "General"
    
            def func(self):
                """Action Response"""
    
                # Rock Response
                if any(i in ['rock', 'r'] for i in self.cmdstring):
                    self.caller.msg("You have selected Rock. Awaiting opponents.")
                    self.caller.ndb.game_handler.action_callback(self.caller,
                                                                  "Rock")
                    return
    
                # Paper Response
                if any(i in ['paper', 'p'] for i in self.cmdstring):
                    self.caller.msg("You have selected Paper. Awaiting opponents.")
                    self.caller.ndb.game_handler.action_callback(self.caller,
                                                                  "Paper")
                    return
    
                # Scissors Response
                if any(i in ['scissors', 's'] for i in self.cmdstring):
                    self.caller.msg("You have selected Scissors. Awaiting opponents.")
                    self.caller.ndb.game_handler.action_callback(self.caller,
                                                                  "Scissors")
                    return

    def action_callback(self, caller, response):
        """
        Receives responses from players. Called by action commands.
        On recieving an action, the script continues to count down.
        When all players have made an action, the script resolves the game.
        If anyone doesn't respond before the time runs out, the game stops.
        
        Interacts with the trainers dictionary. On Player 1 responding:
                self.db.participants={Player1:"rock", Player2:None}
        """
        self.db.participants[caller] = response

        # If all have Responded: Trigger Action Phase
        if all(self.db.participants.values()):
            self.ndb.action_turn = True
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
        `invitation_turn` or `action_turn` NAttribute, set just before calling
        force_repeat.
        """
        # Set up for game phase. Called first time parties agree to play.
        if self.ndb.invitation_turn:
            # Set up players for action phase.
            del self.ndb.invitation_turn
            for participant in self.db.participants:
                participant.cmdset.remove(self.InvitationCmdSet)
                self.db.participants[participant] = None
                self._init_action(participant)
            # The action phase will start now!

        elif self.ndb.action_turn:
            # We're ready to determine who won!
            del self.ndb.action_turn
            self.action_resolution()
            # We could continue the game if instead of self.stop() we put:
            # for participants in self.db.participants:
            #   self._init_action(participant)
            self.stop()

        else:
            # turn timeout
            self.msg_all("Game has ended due to inaction.")
            self.stop()

    #########################
    # Resolve Game
    #########################

    def action_resolution(self):
        """
        All players have lodged an action:
            self.db.participants={Player1:"rock", Player2:"paper"}
        
        Decides who the winner is.
        """
        # action = {Player1:"rock", Player2:"paper"}
        actions = self.db.participants
        beaten_by = {"Rock": "Paper",
                     "Paper": "Scissors",
                     "Scissors": "Rock"}
        # results = {Player1:"rock", Player2:"paper"}
        result = dict(actions)

        for player in actions:
            # If your weakness is in player responses
            if beaten_by[actions[player]] in actions.values():
                result[player] = "lost."
            else:
                result[player] = "won."
        # results = {Player1:"lost", Player2:"won"}

        msg = ""
        for player in result:
            msg += player.key + " has " + result[player] + ". "
        # "Player1 has lost. Player 2 has won."
        self.msg_all(msg)

    #########################
    # Script Utilities
    #########################

    def msg_all(self, message, exceptions=()):
        """
        Send message to all participants
        """
        for participant in self.db.participants:
            if participant not in exceptions:
                participant.msg(message)

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
        del participant.ndb.game_handler
        
        # Clean up! Remove possible CmdSets
        try:
            participant.cmdset.remove(self.InvitationCmdSet)
        except:
            pass
        
        try:
            participant.cmdset.remove(self.GameCmdSet)
        except:
            pass

##############################################################################
#
# AI Combatant
#
##############################################################################


# class AICombatant(Trainer):
#     """
#     """
#     def at_msg_receive(self, text=None, from_obj=None, **kwargs):
#         """
#         This hook is called whenever someone sends a message to this
#         object using the `msg` method.
#         Args:
#             text (str, optional): The message received.
#             from_obj (any, optional): The object sending the message.
#         Kwargs:
#             This includes any keywords sent to the `msg` method.
#         Notes:
#             If this method returns False, the `msg` operation
#             will abort without sending the message.
#         """

#         if text is "You have been challenged to Scissor Paper Rock.":
#             # Accept Challenge
#             try:
#                 self.location.msg_contents("You dare challenge me?!")
#                 self.ndb.game_handler.invitation_callback(self.caller, True)
#                 return True
#             except:
#                 return True

#         if text is "Select an action: [R]ock, [P]aper, [S]cissors?":
#             # Choose Rock, Paper Scissors
#             try:
#                 self.ndb.combat_handler.action_callback(self.caller, random.choice(["Rock", "Paper", "Scissors"]))
#                 return True
#             except:
#                 return True

#         return True
