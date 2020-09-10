"""
Auto Combat System.

This game system uses Evennia Scripts. Scripts are a class which call a 
series of function on repeat after a set time period. 
The life cycle of class looks like:

At_Start - Called when the script is created and when repeated.
At_Repeat - Called after the set time period and recalls At_Start
At_Stop - Interrupts the loop.

At_Start <-
   |      |
 X secs   |   Interrupt with At_Stop
   |      |
   v      |
At_Repeat--

We can use this cycle to base our game system on. 

We create a typeclass that has health and some helper functions.
We create an attack class to begin combat.
We then create a script that on At_Repeat triggered every 10 seconds, will
calculate and subtract damage from both parties until one flees or one is 
unable to battle.

INSTRUCTIONS:
1. You need to have yourself and another player/NPC use the Combat_Class.

1.1 Add the Combat_Class to typeclass.object.Charater as a mixin.
import combat
    class Character(DefaultCharacter, combat.Combat_Class):
OR
1.2 You can '@type self = path.to.file.Combat_Class' in game then
'@create foe:path.to.file.Combat_Class' to create the NPC.

2. You need to have the 

"""
import random
from evennia import DefaultScript
import itertools
from django.conf import settings
from evennia import create_script
from evennia import CmdSet
from evennia import DefaultCharacter
from evennia.utils.utils import class_from_module


COMMAND_DEFAULT_CLASS = class_from_module(settings.COMMAND_DEFAULT_CLASS)

##############################################################################
#
# Combat Typeclass
#
##############################################################################

class Combat_Class(DefaultCharacter):
    """
    Typeclass for Combat.
    
    Gives the character health and the following functions:
    
    obj.health
    obj.max_health
    obj.full_health()
    obj.heal()
    obj.dmg()
    obj.attack_dmg()
    obj.at_death()
    """

    def at_object_creation(self):
        """
        Called only once, when object is first created
        """
        super().at_object_creation()

        # Current Health. Max health is calculated on demand.
        self.db.health = 10
        self.cmdset.add(CombatCmdSet(), permanent=True)

    @property
    def health(self):
        """
        Shows current health.

        Returns:
            current_health (str): Characters current health.

        Returned if:
            obj.heatlh
        """
        return int(self.db.health)

    @property
    def max_health(self):
        """
        Calculate characters's max health.

        Returns:
            max_health (int): Max health determined by rules.

        Returned if:
            obj.max_health
        """
        # Put your rules here
        return 10

    def full_health(self):
        """
        Resets health to maximum.

        Returns:
            health (int): Current health after fill.

        Returned if:
            obj.full_health()
        """
        self.db.health = self.max_health
        return self.health

    def heal(self, value):
        """
        Support addition between between health and int, capping at max health.

        Returns:
            health (int): Current health after addition.

        Returned if:
            obj.heal(5)
        """
        if isinstance(value, int):
            if (self.health + value) > self.max_health:
                self.full_health()
                return self.health
            else:
                self.db.health += value
                return self.health
        else:
            raise ValueError

    def dmg(self, value):
        """
        Support subtraction between health and int, capping at 0

        Returns:
            health (int): Current health after subtraction.

        Returned if:
            obj.heatlh.dmg(5)
        """
        if isinstance(value, int):
            if (self.health - value) < 0:
                self.db.health = 0
                self.at_death()
                return False
            else:
                self.db.health -= value
                return True
        else:
            raise ValueError

    def attack_dmg(self, target):
        """
        Calculate characters attack damage.

        Returns:
            attack damage (int): The damage to be applied to your target.

        Returned if:
            obj.attack_dmg(target)
        """
        # Put your damage calculations here.
        return random.randint(1, 2) 

    def at_death(self):
        """
        Put your death specific functionality here.
        
        """
        self.msg("Your life flashes before your eyes... Wow, you've played a lot of comuputer games...")
        # The battle automatically when you reach zero health.
        self.ndb.combat_handler.stop()
        self.full_health()
        self.msg("You miraculously recover, but you lost the battle.")

##############################################################################
#
# Rock Paper Scissors Battle Command
#
##############################################################################


class CombatCmdSet(CmdSet):
    """
    All characters have this command.
    """
    key = "Combatcmdset"
    priority = 1

    def at_cmdset_creation(self):
        self.add(CmdAttack())


class CmdAttack(COMMAND_DEFAULT_CLASS):
    """
    Initiates combat
    
    Usage:
        attack <participant>
        
    Locates a target to start an auto-battle with.
    """
    key = "attack"
    aliases = []
    help_category = "General"

    def func(self):
        """Find a suitable target to attack"""
        caller = self.caller
        participants = [caller]

        # Handle no input
        if not self.args:
            caller.msg("Attack whom?")
            return

        # Obtain suitable target
        target = caller.search(self.args)

        if not target:
            # No target located.
            caller.msg(self.args + " could not be located.")
            return
        if not isinstance(target, Combat_Class):
            # Can only attack our typeclass.
            caller.msg(self.args + " is not able to battle.")
            return
        if target.ndb.combat_handler:
            # Can only battle one person at a time.
            caller.msg(self.args + " is already in battle.")
            return
        
        participants.append(target)

        # Initialise battle.
        handler = create_script(CombatHandler)
        handler.init_game(participants)

##############################################################################
#
# Game Handler
#
##############################################################################


class CombatHandler(DefaultScript):
    """This implements the game handler."""

    def at_script_creation(self):
        """
        Called when script is first created. Starts combat immediately
        
        """
        # Script attributes.
        self.key = "combat_handler_%i" % random.randint(1, 1000)
        self.desc = "handles Combat"
        self.interval = 3  # turn times of 10 seconds.
        self.start_delay = True
        self.persistent = False
        self.db.participants = []

    #########################
    # At Game Initialisation
    #########################

    def init_game(self, participants):
        """
        Initialises game values and starts combat.
        Args:
            phase [string]: Used by at_start() to determine what phase to
                            initialise trainers for - Invitation / Action.
            participants [list]: All participants.
        """
        # Fill in combat parties.
        self.db.participants = participants
        # Start combat.
        self.at_start()

    def at_start(self):
        """
        This is called on first start and on reload in case the server restarts. 
        We need to re-assign this game handler to all characters as well as 
        re-assign the combat commands.
        """
        # Set up the phase.
        for participant in self.db.participants:
            participant.ndb.combat_handler = self
            participant.cmdset.add(self.CombatCmdSet)
        self.msg_all("You enter into combat!")

    class CombatCmdSet(CmdSet):
        """Contains response commands"""
        key = "combatcmdset"
        mergetype = "Merge"
        priority = 10
        no_exits = True

        def at_cmdset_creation(self):
            self.add(self.CmdFlee())
    
        class CmdFlee(COMMAND_DEFAULT_CLASS):
            """
            Flee from the battle
            
            Calls the Flee function in the combat_handler
            """
            key = "flee"
            aliases = ["run"]
            help_category = "General"
    
            def func(self):
                """Flee from battle"""
                self.caller.ndb.combat_handler.at_flee(self.caller)
                return

    def at_flee(self, caller):
        """
        Simply stops combat.
        """
        # Add your flee calculations here.
        self.msg_all(caller.key + " flees combat.")
        self.stop()

    #########################
    # Repeat Script
    #########################

    def at_repeat(self):
        """
        Called every 10 seconds.
        """
        # Calculate action order here
        order = list(self.db.participants)
        random.shuffle(order)
        
        attacker = order[0]
        defender = order[1]

        # Attackers Turn
        self.msg_all(attacker.key + " takes the initiative!")
        inflict_dmg = attacker.attack_dmg(defender)
        self.msg_all(attacker.key + " inflicts " + str(inflict_dmg) + " damage!")

        # Inflict damage and check if dead.
        if not defender.dmg(inflict_dmg):
            attacker.msg("You down your opponent!")
            self.stop()

        # Defenders Turn
        self.msg_all(defender.key + " makes a counter attack!")
        inflict_dmg = defender.attack_dmg(attacker)
        self.msg_all(defender.key + " inflicts " + str(inflict_dmg) + " damage!")
        
        # Inflict damage and check if dead.
        if not attacker.dmg(inflict_dmg):
            defender.msg("You down your opponent!")
            self.stop()
        
        # If everyone is still alive, repeat cycle.
        

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
            del participant.ndb.combat_handler
            try:
                participant.cmdset.remove(self.CombatCmdSet)
            except:
                pass
