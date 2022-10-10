##"account.py" library ---VERSION 0.23---
## - REQUIRES: "entity.py"
## - For managing account data in Tank Battalion Online -
##Copyright (C) 2022  Lincoln V.
##
##This program is free software: you can redistribute it and/or modify
##it under the terms of the GNU General Public License as published by
##the Free Software Foundation, either version 3 of the License, or
##(at your option) any later version.
##
##This program is distributed in the hope that it will be useful,
##but WITHOUT ANY WARRANTY; without even the implied warranty of
##MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##GNU General Public License for more details.
##
##You should have received a copy of the GNU General Public License
##along with this program.  If not, see <https://www.gnu.org/licenses/>.

import entity
import random

class Account():
    def __init__(self,name="a name",password="123 is a bad password",bot=False): #this sets the beginning stats for any new account.
        #Account name and password
        self.name = name
        self.password = password
        
        #Currencies
        self.cash = 50.0 #50^ (^ can be decimal)
        self.experience = 0.0 #for specialization

        #Simple flag which tells whether this account is for a bot or not.
        self.bot = bot

        if(self.bot): #if we're a bot, zero our cash and experience.
            self.cash = 0
            self.experience = 0
            
        #Tank stats
        self.shells = [ #ammunition left in tank
            0, #hollow
            0, #regular
            0, #explosive
            0  #disk
            ]
        self.powerups = [
            None, #Improved Fuel: +35% speed.
            None, #Fuel Fire Suppressant: Extinguishes fire in gas tank. -10% speed
            None, #Dangerous Loading: +50% RPM, -10% HP per use
            None, #Explosive Tip: +25% Damage/shot, -5% Penetration, -5% Loading Speed, Inflicts fire in enemy's fuel tank.
            None, #Amped Gun: +25% Penetration, -10% HP per use
            None  #Extra Armor: -50% speed, -50% damage intake (+50% Armor)
            ]
        self.upgrades = [
            0, #gun
            0, #loading mechanism
            0, #armor
            0  #engine
            ]
        #negative numbers means specializing as heavy tank. Positive numbers mean specializing as light tank.
        self.specialization = 0

        # - This number is needed for calculating bullet costs -
        self.damage_multiplier = 1.00
        self.penetration_multiplier = 1.00 #this isn't used in calculating bullet costs, but I figured I'd add it since I use it later on in battle_client.py.

        # - How many of each shell may you own?? I can't just let people run around with disk shells all day because they saved their ^ -
        self.max_shells = [
            30,
            20,
            7,
            5
            ]

        # - The price of all things in the store -
        self.shell_prices = [
            1.0, #hollow: 1.0^
            3.5,
            20.0,
            25.0 #disk: 25.0^
            ]
        self.powerup_price = 5.0 #X^ per powerup
        self.upgrade_start_price = 5.0 #first upgrade starts at 2^. Next upgrades: pow(5^, upgrade#)

        # - The price of all things battle related -
        self.DEATH_COST = 25.0 #^
        self.KILL_REWARD = 10.0 #^
        self.CASH_DAMAGE_MULTIPLIER = 1.00

        # - How much % of original value do you gain when you get a refund?
        self.REFUND_PERCENT = 0.75

        # - Experience prices -
        self.EXP_DEATH_COST = 5.0 #experience
        self.EXP_KILL_REWARD = 7.5
        self.EXPERIENCE_DAMAGE_MULTIPLIER = 0.05
        self.HIT_EXPERIENCE = 1.25
        self.WHIFF_EXPERIENCE = 1

        #how many upgrades are we allowed to do on each part? How much can we specialize?
        self.upgrade_limit = 6 #6 upgrades/ +/-6 specialization on a tank allowed

    def __str__(self): #for if we want to print out the account's stats
        return (
            "Account name: " + self.name + "\n" +
            "Cash/Experience: " + str(self.cash) + " , " + str(self.experience) + "\n" +
            "Available resources: \n" +
            " - Shells: " + str(self.shells) + "\n" +
            " - Powerups: " + str(self.powerups) + "\n" +
            " - Upgrades: " + str(self.upgrades) + "\n" +
            "Specialization (- = heavy, + = light): " + str(self.specialization) + "\n" +
            "End of report."
            )

    def return_data(self,precision=2): #useful for gathering a useful set of information for netcode transmission. Encoded in a list in the same order as __str__().
        return [
            self.name,
            [round(self.cash,precision), round(self.experience,precision)],
            [self.shells,self.powerups,self.upgrades,self.specialization],
            round(self.damage_multiplier,precision),
            round(self.penetration_multiplier,precision),
            ]

    def enter_data(self,data): #Takes data returned from return_data() and inputs it into this Account() object.
        self.name = data[0]
        self.cash = data[1][0]
        self.experience = data[1][1]
        self.shells = data[2][0][:]
        self.powerups = data[2][1][:]
        self.upgrades = data[2][2][:]
        self.specialization = data[2][3]
        self.damage_multiplier = data[3]
        self.penetration_multiplier = data[4]

    def randomize_account(self): #scrambles the account data to create a unique account. Good for testing matchmaking or creating bots.
        self.specialization = random.randint(-6, +6) #randomize our tank's specialization
        for x in range(0,len(self.upgrades)): #randomize our tank's upgrade levels
            self.upgrades[x] = random.randint(0,6)
        for x in range(0,len(self.shells)): #randomize the shells in our tank
            self.shells[x] = random.randint(0,50)
        for x in range(0,len(self.powerups)): #randomize the powerups we own
            dice_roll = random.randint(0,1)
            if(dice_roll == 1):
                self.powerups[x] = True
        self.experience = random.randint(10,10000) #randomize experience
        self.cash = random.randint(25, 1000) #randomize cash amount

    def random_purchase(self): #randomly purchases one item.
        if(self.bot): #bots can have anything they like...
            self.cash = 1000000.0
            self.experience = 1000000.0
        decisions = ["upgrade","powerup","shell"]
        if(self.specialization == 0):
            decisions.append("specialize")
        decision = decisions[random.randint(0,len(decisions) - 1)]
        if(decision == "specialize"): #I programmed this a bit differently from everything else because
            rng_num = random.randint(-6,6)
        elif(decision == "powerup"):
            rng_num = random.randint(0,5)
        else:
            rng_num = random.randint(0,3)
        self.purchase(decision, rng_num)
        if(self.bot):
            self.cash = 0
            self.experience = 0

    def create_tank(self, image, team_name): #returns a tank object with all the account's tank stats taken into account.
        tank = entity.Tank(image, [self.name,team_name]) #create a generic tank object

        #Take into account upgrades:
        #if(self.upgrades[0] > 0):
        tank.damage_multiplier = pow(1.12, self.upgrades[0]) #gun
        tank.penetration_multiplier = pow(1.09, self.upgrades[0]) #gun
        #if(self.upgrades[1] > 0):
        tank.RPM *= pow(1.10, self.upgrades[1]) #loading mechanism
        #if(self.upgrades[2] > 0):
        tank.armor *= pow(1.14, self.upgrades[2]) #armor
        #if(self.upgrades[3] > 0):
        tank.speed *= pow(1.10, self.upgrades[3]) #engine speed

        # - Handle tank specialization -
        tank.damage_multiplier *= pow(1.07, -self.specialization)
        tank.penetration_multiplier *= pow(1.05, self.specialization)
        if(self.specialization > 0): #light?
            tank.RPM *= pow(1.06, self.specialization)
        else: #heavy?
            tank.RPM *= pow(0.98, self.specialization)
        tank.armor *= pow(1.10, -self.specialization)
        tank.speed *= pow(1.06, self.specialization)

        #Load the tank with shells and powerups
        tank.shells = self.shells
        tank.powerups = self.powerups.copy()

        #Update the tank's "start HP and armor" variables
        tank.start_HP = tank.HP
        tank.start_armor = tank.armor

        #return the tank now that it is characterized as heavy, light or medium, as well as stocked with ammunition,
        #powerups, and its upgrade stats.
        return tank

    #Return_tank() also calculates total money earned from battle.
    #You give the account() the tank you used in a battle; This function returns the cost to rebuy everything, rebuys necessary items,
    #  Handles cash gain/loss and experience gain/loss.
    def return_tank(self,tank,rebuy=False,bp_to_cash=True,experience=False,verbose=False):
        # - If we set this flag to True, convert our battle performance to cash -
        if(bp_to_cash):
            # - First, we handle cash -
            earned = 0.0
            # - Convert the tank's total damage to cash -
            self.cash += tank.total_damage * self.CASH_DAMAGE_MULTIPLIER
            earned += tank.total_damage * self.CASH_DAMAGE_MULTIPLIER
            # - Convert our death to negative cash (sad) -
            if(tank.destroyed == True):
                self.cash -= self.DEATH_COST
                earned -= self.DEATH_COST
            # - We also need to convert kills to cash -
            self.cash += tank.kills * self.KILL_REWARD
            earned += tank.kills * self.KILL_REWARD
            # - Second, we handle experience -
            old_experience = self.experience #bookmark what *was* our experience
            if(experience):
                self.experience += tank.kills * self.EXP_KILL_REWARD #kills
                if(tank.destroyed == True): #deaths
                    self.experience -= self.EXP_DEATH_COST
                # - Handle the hit/miss experience earned -
                total_shots = 0
                for x in range(0,len(tank.shells_used)):
                    total_shots += tank.shells_used[x]
                self.experience -= tank.missed_shots * self.WHIFF_EXPERIENCE #missed shots
                self.experience += (total_shots - tank.missed_shots) * self.HIT_EXPERIENCE #hit shots
                # - Handle damage -
                self.experience += tank.total_damage * self.EXPERIENCE_DAMAGE_MULTIPLIER
                # - Check if we're below 0 EXP and make sure that we aren't below 0 EXP if that's the case -
                if(self.experience < 0):
                    self.experience = 0
                print("[PLAYER " + str(tank.name) + "] Experience earned: " + str(self.experience - old_experience))
        # - Rebuy all powerups [REQUIRED, not optional] -
        pu_cost = 0.0
        for x in range(0,len(tank.powerups)):
            if(tank.powerups_used[x] > 0):
                for buy in range(0,tank.powerups_used[x]):
                    self.purchase("powerup",x)
                    pu_cost += self.powerup_price
            else: #did we collect more powerups off the map then we used?
                for refund in range(0,abs(tank.powerups_used[x])): #we gets money for that extra powerup.
                    self.cash += self.powerup_price
                    pu_cost -= self.powerup_price
        # - Rebuy all shells if we set rebuy to True -
        shell_cost = 0.0
        for x in range(0,len(self.shell_prices)): #how much would it cost to rebuy all shells?
            shell_cost += self.shell_prices[x] * tank.shells_used[x] * self.damage_multiplier
            if(rebuy): #if we have this setting on, rebuy all our shells.
                for buy in range(0,tank.shells_used[x]):
                    self.purchase("shell",x)
        print("[PLAYER " + str(tank.name) + "] Powerup costs: " + str(pu_cost) + " Shell costs: " + str(shell_cost))
        if(bp_to_cash):
            # - Print out how much we earned (before cost of anything like powerups/bullets, and after) -
            print("[PLAYER " + str(tank.name) + "] Earned before rebuy: " + str(earned) + " Earned after rebuy: " + str(earned - shell_cost - pu_cost))
        # - The last thing we do is make sure that our ^ balance is not negative -
        if(self.cash < 0): #a player can't be going *that* negative =)
            self.cash = 0.0 #make sure the value is still a float - I like floating point numbers!
        if(not verbose or not bp_to_cash):
            return shell_cost
        elif(bp_to_cash): #somebody does be wanting their stats? bp_to_cash MUST be True for this to work...
            return [earned, shell_cost, pu_cost, earned - shell_cost - pu_cost, self.experience - old_experience]

    def purchase(self, item, item_index, view_price=False): #if your account balance permits, purchase the item selected.
        if(item == "powerup"): #powerups?
            price = self.powerup_price
            #Check if account has powerup_price availible. If so, deduct powerup_price from account's balance.
            #Give the account the powerup.
            if(not view_price):
                if(self.cash >= price and self.powerups[item_index] != True):
                    self.cash -= price
                    self.powerups[item_index] = True #we now has powerup!
                else:
                    self.powerups[item_index] = None #powerup is not there =(
                    return False #we couldn't get item
        elif(item == "shell"): #ammunition?
            price = self.shell_prices[item_index] * self.damage_multiplier
            if(not view_price):
                if(self.cash >= price): #we has the money?
                    if(self.max_shells[item_index] > self.shells[item_index]): #we're not at our max?
                        self.cash -= price
                        self.shells[item_index] += 1
                    else:
                        return False
                else:
                    return False #we couldn't buy the item
        elif(item == "upgrade"): #an upgrade?
            price = pow(self.upgrade_start_price, self.upgrades[item_index] + 1)
            if(not view_price):
                if(self.upgrades[item_index] < self.upgrade_limit): #we haven't reached the upgrade cap yet?
                    if(self.cash >= pow(self.upgrade_start_price, self.upgrades[item_index] + 1)): #we has da money?
                        self.cash -= pow(self.upgrade_start_price, self.upgrades[item_index] + 1)
                        self.upgrades[item_index] += 1
                        # - Update the damage multiplier for your tank -
                        self.damage_multiplier = self.create_tank("image","dummy team").damage_multiplier
                        self.penetration_multiplier = self.create_tank("image","dummy team").penetration_multiplier
                    else: #we didn't have the cash... =(
                        return False
                else: #already upgraded to the max!
                    return False
        elif(item == "specialize"): #we're specializing our tank!
            price = pow(self.upgrade_start_price, abs(self.specialization + item_index))
            if(not view_price):
                # - Now, before we are allowed to check whether we have the experience, I need to make sure people sell their shells in their tank to avoid switching to heavy, selling shells and making 100s of ^ -
                noshells = True
                for x in self.shells:
                    if(x != 0):
                        noshells = False
                        break
                if(noshells):
                    if(abs(self.specialization + item_index) <= self.upgrade_limit): #we haven't reached the specialization cap?
                        if(self.experience >= price):
                            self.specialization += item_index
                            # - Update the damage multiplier for your tank -
                            self.damage_multiplier = self.create_tank("image","dummy team").damage_multiplier
                            self.penetration_multiplier = self.create_tank("image","dummy team").penetration_multiplier
                        else: #not enough experience...
                            return False
                    else: #no specialization allowed...
                        return False
                else:
                    return False
        if(view_price):
            return price
        return True #we were able to buy item!

    def refund(self, item, item_index, view_price=False): #return the item selected if you own it.
        success = False
        if(item == "powerup"): #powerups?
            price = self.powerup_price * self.REFUND_PERCENT
            if(not view_price and self.powerups[item_index] != False):
                self.cash += price
                self.powerups[item_index] = False
                success = True
        elif(item == "shell"): #ammunition?
            price = self.shell_prices[item_index] * self.REFUND_PERCENT
            if(not view_price and self.shells[item_index] > 0):
                self.cash += price
                self.shells[item_index] -= 1
                success = True
        elif(item == "upgrade"): #an upgrade?
            price = pow(self.upgrade_start_price, self.upgrades[item_index]) * self.REFUND_PERCENT
            if(not view_price and self.upgrades[item_index] > 0):
                self.cash += price
                self.upgrades[item_index] -= 1
                success = True
                # - Update the damage multiplier for your tank -
                self.damage_multiplier = self.create_tank("image","dummy team").damage_multiplier
                self.penetration_multiplier = self.create_tank("image","dummy team").penetration_multiplier
        if(view_price): #just lookin' around right now?
            return price
        elif(not success):
            return False
        return True #else we actually bought something.

###quick test to see whether the currency/purchasing system worked. It does!
##account = Account()
##account.experience = 10000000
##account.purchase("specialize",6)
##tank = account.create_tank("armor","team")
##print(tank)
