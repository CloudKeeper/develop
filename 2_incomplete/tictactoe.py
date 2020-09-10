"""
- Win Conditions
- Can overwrite positions.
- make sure script dies at reload.

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
We'll set up the script to have a variable "script.db.phase". When At_Start is 
called the script will check the "phase" it is in and take different actions:

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
	  
At_Repeat will be called when the player who has the "turn" responds OR 
At_Repeat will be called after the time limit has ran out.

If a player has refused to play, or the timer has finished without the "turn"
player responding, the game will call Stop() and close the game.

If all players have accepted the invitation, it will move to the action phase.
If the "turn" player has selected an action, it will proceed to the next turn.
"""
import random
from evennia import DefaultScript
import itertools
from django.conf import settings
from evennia import create_script
from evennia import CmdSet
from trainers.typeclasses import Trainer
from evennia.utils.utils import class_from_module
from evennia.utils import evform

COMMAND_DEFAULT_CLASS = class_from_module(settings.COMMAND_DEFAULT_CLASS)

##############################################################################
#
# Rock Paper Scissors Battle Command
#
##############################################################################


class TicTacToeCmdSet(CmdSet):
    """
    All characters have this command, so challenges to play TicTacToe
    can happen at any time!
    """
    key = "tictactoecmdset"
    priority = 1

    def at_cmdset_creation(self):
        self.add(CmdTicTacToe())


class CmdTicTacToe(COMMAND_DEFAULT_CLASS):
    """
    Initiates a game of TicTacToe or handles game input if inside a game.
    
    Usage:
        tictactoe <participant>
        
    Challenge a player to start a game with and starts the game scripts.
    """
    key = "tictactoe"
    aliases = ["ttt"]
    help_category = "General"

    def func(self):
        """We want to send a list of player objects to the Game Handler"""
        caller = self.caller
        participants = [caller]

        # ---------------------------------------------------------------------
        # Take action in current Tic Tac Toe game.
        # ---------------------------------------------------------------------
        if caller.ndb.game_handler:
            # Check game is in the right phase
            if caller.ndb.game_handler.db.phase == "Action":
                # Check caller has the turn.
                if caller == caller.ndb.game_handler.db.turn_order[0]:
                    args = self.args.lower()
                    coordinates_to_list = {"a1":0, "b1":1, "c1":2,
                                           "a2":3, "b2":4, "c2":5,
                                           "a3":6, "b3":7, "c3":8}
                    
                    if args in coordinates_to_list:
                        if caller.ndb.game_handler.db.game_field[coordinates_to_list[args]] == " ":
                            caller.ndb.game_handler.action_callback(caller, args)
                        else:
                            caller.msg("That position on the board is already filled.")
                    else:
                        caller.msg("Usage: 'tictactoe b2'.")
                else:
                    caller.msg("It is not your turn yet. Waiting for your Opponent.")
                    return
            else:
                caller.msg("You have a waiting game invitation to 'Accept' or 'Decline'.")
                return
        
        # ---------------------------------------------------------------------
        # Challenge a player to Tic Tac Toe.
        # ---------------------------------------------------------------------
        else:
            # Handle no input
            if not self.args:
                caller.msg("Play with whom?")
                return
    
            # Obtain suitable players from listed.
            # Only one other person can play tictactoe
            participant = caller.search(self.args)
    
            if not participant:
                # Only players at your location can play.
                caller.msg(self.args + " could not be located.")
                return
            if not isinstance(participant, Trainer):
                # Only players can play.
                caller.msg(self.args + " is not able to play a game.")
                return
            if participant.ndb.game_handler:
                # Can only play one game at a time.
                caller.msg(self.args + " is already playing a game.")
                return
            if participant in participants:
                # This can only be where you've targets yourself.
                caller.msg(self.args + " you cannot play by yourself.")
    
            participants.append(participant)
            
            # Create list and initialise the game.
            handler = create_script(TicTacToeHandler)
            handler.init_game(participants, "Invitation")

##############################################################################
#
# Game Handler
#
##############################################################################


class TicTacToeHandler(DefaultScript):
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
        self.db.game_field = [" ", " ", " ",
                              " ", " ", " ",
                              " ", " ", " "]
        self.db.participants = {}
        self.db.turn_order = []

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
        participant.msg(list(self.db.participants)[0].key + " challenges you to Tic Tac Toe. Accecpt? (Y/N)")

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

    def _game_board(self, title = ""):
        """
        Returns the game board.
        """

        text = {"FORM": """
                ◓═══════════◓
                 xAxxxxxxxxx
                ◓═══════════◓
                    A B C
                  1 -┃-┃-
                    ━╋━╋━
                  2 -┃-┃-
                    ━╋━╋━
                  3 -┃-┃-
                ◓═══════════◓\
                """}
        form = str(evform.EvForm(form=text, cells={"A": title}))      
        
        for position in self.db.game_field:
            form = form.replace("-", position, 1)
        return form

    def _init_action(self, participant):
        """
        Run for each participant.
        Both players are presented the board and prompted to take an action if
        the player has the 'turn'. Both players may forfeit the match.
        Players are given a command set with available actions.
        The game then waits for their response.
        """
        
        participant.ndb.game_handler = self
        participant.cmdset.add(self.ActionCmdSet)
        if self.db.turn_order.index(participant) == 0:
            participant.msg(self._game_board("YOUR TURN"))
        else:
            participant.msg(self._game_board("OPP. TURN"))

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
            key = "forfeit"
            help_category = "General"
    
            def func(self):
                """Action Response"""
                # Add later.


    def action_callback(self, caller, response):
        """
        Receives responses from players. Called by tictactoe command.
        
        gets "a1" and has to update game_field at appropriate entry
        """
        coordinates_to_list = {"a1":0, "b1":1, "c1":2,
                               "a2":3, "b2":4, "c2":5,
                               "a3":6, "b3":7, "c3":8}
        #Allow direct entry if response is an int.
        
        # Convert response to game_field position and insert callers
        self.db.game_field[coordinates_to_list[response]] = self.db.participants[caller]
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
            # Only one player can respond at a time. Create turn order
            # from participant list and randomise turn order.
            self.db.turn_order = list(self.db.participants.keys())
            random.shuffle(self.db.turn_order)
            
            # Assign players their icon - X or O
            values = ["X", "O"]
            self.db.participants = dict(zip(list(self.db.turn_order), values))
            self.msg_all(str(self.db.participants))
            self.msg_all(str(self.db.turn_order))
            # Set up players for action phase.
            del self.ndb.invitation_turn
            for participant in self.db.participants:
                participant.cmdset.remove(self.InvitationCmdSet)
                self._init_action(participant)
            # The action phase will start now!

        # Check for win condition else prepare for next turn.
        elif self.ndb.action_turn:
            # Check win condition.
            self.action_resolution()
            # Next players turn.
            order = self.db.turn_order
            order[0], order[1] = order[1], order[0]
            
            # Set up players for next turn.
            del self.ndb.action_turn
            for participant in self.db.participants:
                participant.cmdset.remove(self.ActionCmdSet)
                self._init_action(participant)

        else:
            # turn timeout
            self.msg_all("Game has ended due to inaction.")
            self.stop()

    #########################
    # Resolve Game
    #########################

    def action_resolution(self):
        """
        Decides who the winner is.
        """
        positions = self.db.game_field
        lines = [[0,1,2], [3,4,5], [6,7,8], # Rows
                 [0,3,6], [1,4,7], [2,5,8], # Columns
                 [0,4,8], [2,4,6]]          # Diagonals
        
        for line in lines:
            if positions[line[0]] == positions[line[1]] == positions[lines[2]]:
                # Weed out empty positions.
                if positions[line[0]] in ["X", "O"]:
                    # Find the winner
                    winner = list(self.db.participants.keys())[list(self.db.participants.values()).index(positions[line[0]])]
                    winner.msg("You have one Tic Tac Toe!")
                    self.msg_all(winner.key + " has won Tic Tac Toe.", [winner])
                    self.stop()

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
            participant.cmdset.remove(self.ActionCmdSet)
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
