##"account.py" library ---VERSION 0.41---
## - For managing account data in Tank Battalion Online -
##Copyright (C) 2024  Lincoln V.
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

import entity, netcode #my own libraries
import random, math, time #other people's libraries

# - Define what data types are allowed to pass unrestricted through enter_data() -
DATA_TYPES = [
    ["<class 'str'>",
    ["<class 'float'>", "<class 'float'>"],
    [["<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>"], "<class 'list'>", ["<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>"], "<class 'int'>"],
    "<class 'float'>",
    "<class 'float'>",
    ["<class 'str'>", "<class 'str'>", "<class 'str'>", ["<class 'str'>", "<class 'int'>", "<class 'float'>", ["<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>"]]]],

    ["<class 'str'>",
    ["<class 'float'>", "<class 'float'>"],
    [["<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>"], "<class 'list'>", ["<class 'int'>","<class 'int'>","<class 'int'>","<class 'int'>"], "<class 'int'>"],
    "<class 'float'>",
    "<class 'float'>",
    ["<class 'NoneType'>"]]
    ]
PU_DATA_TYPES = ["<class 'NoneType'>", "<class 'bool'>"]

# - Constants for purchase DETAILS -
# - What are the stats of the various bullets? -
shell_specs = [ #Format: [damage, penetration]
    [8, 8], #hollow
    [12, 12], #regular
    [20, 7], #explosive
    [18, 14] #disk
    ]
upgrade_details = [
    "D.M./P.M. ",
    "RPM ",
    "Armor ",
    "Speed "
    ]

# - How many of each shell may you own?? I can't just let people run around with disk shells all day because they saved their ^ -
max_shells = [
    50, #hollow
    20,
    7,
    5 #disk
    ]

# - The price of all things in the store -
shell_prices = [
    0.5, #hollow
    6.0,
    27.5,
    25.0 #disk
    ]
powerup_price = 12.5 #X^ per powerup
upgrade_start_price = 1000.0 #sqrt(self.upgrade_increment * upgrade_num) + self.upgrade_start_price = cost
upgrade_increment = 375*375 #sqrt(self.upgrade_increment * upgrade_num) + self.upgrade_start_price = cost

specialization_start_price = 1000.0 #sqrt(self.specialization_increment * upgrade_num) + self.specialization_start_price = cost
specialization_increment = 6500.0*6500.0 #sqrt(self.specialization_increment * upgrade_num) + self.specialization_start_price = cost

# - The price of all things battle related -
KILL_REWARD = 25.0 #^ - This value should be at least double the cost of a powerup, since you'll often want to use powerups when killing another tank
DEATH_COST = KILL_REWARD * 2.5 #^
CASH_DAMAGE_MULTIPLIER = 1.00 #all shell prices are calculated with this constant in mind, so don't change it unless you're planning to heavily overhaul the cost of everything.

# - How much % of original value do you gain when you get a refund?
REFUND_PERCENT = 0.75

# - Experience prices -
EXP_KILL_REWARD = 10.0 #exp += self.EXP_KILL_REWARD
EXP_DEATH_COST = 2.5 * EXP_KILL_REWARD #exp += -self.EXP_DEATH_COST
EXPERIENCE_DAMAGE_MULTIPLIER = 0.025 #exp += damage * self.EXPERIENCE_DAMAGE_MULTIPLIER
HIT_EXPERIENCE = 1.0 #exp += shots * self.HIT_EXPERIENCE
WHIFF_EXPERIENCE = HIT_EXPERIENCE * 5 #exp += -shots * self.WHIFF_EXPERIENCE

#how many upgrades are we allowed to do on each part? How much can we specialize?
upgrade_limit = 6 #6 upgrades/ +/-6 specialization on a tank allowed

class Account():
    def __init__(self,name="a name",password="123 is a bad password",bot=False,requested_rating=None): #this sets the beginning stats for any new account.
        #Account name and password
        self.name = name
        self.password = password

        #Player settings (these are stored in the server so that different people don't overwrite saved settings locally)
        #Settings list: ["Back","","Key config","Deadzone","KB/JS",
        #   "Shell 1","Shell 2","Shell 3","Shell 4","Powerup 1",
        #   "Powerup 2","Powerup 3","Powerup 4","Powerup 5","Powerup 6",
        #   "Up","Left","Down","Right","Shoot",
        #   "Escape Battle","Cursor Modifier","PTT Key","","GFX Quality",
        #   "Music Volume","SFX Volume","Skip Back One Track","Skip Forward One Track"]
        #NOTE: skip back & forward, blank entries, the "back" key all have undisplayed values in the settings menu...which I will save here to avoid indexing problems
        self.settings = [None]

        #Last time a player received free items is recorded so I can give them free hollow shells every 24 hrs.
        self.last_free_stuff = time.time()
        
        #Currencies
        self.cash = 50.0 #50^ (^ can be decimal)
        self.experience = 0.0 #for specialization

        #Simple flag which tells whether this account is for a bot or not.
        self.bot = bot

        if(self.bot): #if we're a bot, zero our cash and experience. Also, we might need to know exactly what the bot's requested intelligence rating is when we actually get the bot going.
            self.cash = 0
            self.experience = 0
            self.requested_rating = requested_rating
            
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
            [float(round(self.cash,precision)), float(round(self.experience,precision))],
            [self.shells,self.powerups,self.upgrades,self.specialization],
            float(round(self.damage_multiplier,precision)),
            float(round(self.penetration_multiplier,precision)),
            self.settings[:]
            ]

    def enter_data(self,data): #Takes data returned from return_data() and inputs it into this Account() object.
        global DATA_TYPES, PU_DATA_TYPES
        verify = False
        for x in DATA_TYPES:
            if(netcode.data_verify(data, x)):
                verify = True
                break
        if(verify): #we still haven't verified our powerup list...
            pu_verify = False
            for d in data[2][1]:
                vf_element = False
                for x in PU_DATA_TYPES:
                    if(netcode.data_verify(d, x)):
                        vf_element = True
                        break
                if(vf_element == False):
                    pu_verify = False
                    break
                else:
                    pu_verify = True
            if(pu_verify):
                self.name = data[0]
                self.cash = data[1][0]
                self.experience = data[1][1]
                self.shells = data[2][0][:]
                self.powerups = data[2][1][:]
                self.upgrades = data[2][2][:]
                self.specialization = data[2][3]
                self.damage_multiplier = data[3]
                self.penetration_multiplier = data[4]
                self.settings = data[5][:]
            else:
                print("[ACCOUNT.py] Couldn't verify data packet on pu_verify! Data: " + str(data))
        else:
            print("[ACCOUNT.py] Couldn't verify data packet on main verify! Data: " + str(data))

    def check_free_stuff(self): #gives a player a free stock of hollow shells every 24hrs. This is to keep players from becoming completely broke if they have some bad battles.
        global max_shells
        if(time.time() - self.last_free_stuff >= 24 * 60 * 60): #it's been 24hrs since last time we got free stuff? The player gets free hollow shells.
            self.shells[0] = max_shells[0]
            self.last_free_stuff = time.time()

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
        #I programmed specialization a bit differently from everything else for some reason...You don't request to specialize "1 more step heavy", you request to buy the specialization value you would like to be in total.
        if(decision == "specialize"):
            rng_num = random.randint(-6,6)
        elif(decision == "powerup"):
            rng_num = random.randint(0,len(self.powerups) - 1)
        else:
            rng_num = random.randint(0,len(self.shells) - 1)
        self.purchase(decision, rng_num)
        if(self.bot):
            self.cash = 0
            self.experience = 0

    def bot_purchase(self):
        self.cash = 10000000.0 #set our cash and experience to good values
        self.experience = 100000000.0
        # - Now we make a decision based on how much ammunition we own -
        decisions = ["shell"]
        # - Take the sum of all our shells in our tank -
        sum_shells = 0
        for x in self.shells:
            sum_shells += x
        # - Take the sum of the maximum amount of shells we could have -
        sum_max_shells = 0
        for x in max_shells:
            sum_max_shells += x
        if(sum_shells > 0): #avoid div0 errors
            if(sum_shells / (sum_max_shells / 2.5) >= 1): #we can get upgrades + powerups since we already have a good amount of shells
                decisions.append("powerup")
                decisions.append("upgrade")
                decisions.append("specialization")
        # - If we don't have the minimum amount of shells, the only thing which will be purchased is shells -
        random.shuffle(decisions) #pick a random purchase option
        decision = decisions[0]
        #I programmed specialization a bit differently from everything else for some reason...You don't request to specialize "1 more step heavy", you request to buy the specialization value you would like to be in total.
        if(decision == "specialize"):
            rng_num = random.randint(-6,6)
        elif(decision == "powerup"):
            rng_num = random.randint(0,len(self.powerups) - 1)
        else:
            # - I used a goofy algorithm here to prioritize buying cheaper shells over the others -
            rng_num = int((len(self.shells) - 1) - round(math.sqrt(random.randint(0,(len(self.shells) - 1) * (len(self.shells) - 1))),0))
        successful_purchase = False
        purchase_timer = 0 #We may only run this loop a max of X times, so that we don't end up in a never-ending loop.
        while not successful_purchase and purchase_timer < 12: #X is defined here (see above comment)
            success = self.purchase(decision, rng_num)
            successful_purchase = success
            purchase_timer += 1
            # - Assuming the purchase was *not* successful, we can try decreasing our rng_num down to 0,
            #   - and then wrapping it back to its max value to see if there's anything we can buy possibly
            if(rng_num > 0):
                rng_num -= 1
            else: #we're already at 0? Each option has its own max value, so I have to set rng_num manually for each individual choice.
                if(decision == "powerup"):
                    rng_num = len(self.powerups) - 1
                elif(decision == "upgrade"):
                    rng_num = len(self.upgrades) - 1
                elif(decision == "shell"):
                    rng_num = len(self.shells) - 1
        # - Reset our cash and experience values -
        self.cash = 0
        self.experience = 0

    def bot_refund(self):
        # - Now we make a decision based on how much ammunition we own -
        decisions = ["shell"]
        # - Take the sum of all our shells in our tank -
        sum_shells = 0
        for x in self.shells:
            sum_shells += x
        # - Take the sum of the maximum amount of shells we could have -
        sum_max_shells = 0
        for x in max_shells:
            sum_max_shells += x
        if(sum_shells > 0): #avoid div0 errors
            if(sum_shells / (sum_max_shells / 3.5) <= 1): #we can sell upgrades + powerups if we don't have enough shells
                decisions.append("powerup")
                decisions.append("upgrade")
        random.shuffle(decisions) #pick a random purchase option
        decision = decisions[0]
        if(decision == "powerup"):
            rng_num = random.randint(0,len(self.powerups) - 1)
        else:
            rng_num = random.randint(0,len(self.shells) - 1)
        successful_refund = False
        refund_timer = 0 #We may only run this loop a max of X times, so that we don't end up in a never-ending loop.
        while not successful_refund and refund_timer < 12: #X is defined here (see above comment)
            success = self.refund(decision, rng_num)
            successful_refund = success
            refund_timer += 1
            # - Assuming the refund was *not* successful, we can try decreasing our rng_num down to 0,
            #   - and then wrapping it back to its max value to see if there's anything we can refund possibly
            if(rng_num > 0):
                rng_num -= 1
            else: #we're already at 0? Each option has its own max value, so I have to set rng_num manually for each individual choice.
                if(decision == "powerup"):
                    rng_num = len(self.powerups) - 1
                elif(decision == "upgrade"):
                    rng_num = len(self.upgrades) - 1
                elif(decision == "shell"):
                    rng_num = len(self.shells) - 1
        # - Reset our cash and experience values -
        self.cash = 0
        self.experience = 0

    def create_tank(self, image, team_name, upgrade_offsets=[0,0,0,0], skip_image_load=False, team_num=0, team_ct=2): #returns a tank object with all the account's tank stats taken into account.
        tank = entity.Tank(image, [self.name,team_name], skip_image_load, team_num, team_ct) #create a generic tank object

        #Take into account upgrades:
        tank.damage_multiplier = pow(1.12, self.upgrades[0] + upgrade_offsets[0]) #gun
        tank.penetration_multiplier = pow(1.09, self.upgrades[0] + upgrade_offsets[0]) #gun
        tank.RPM *= pow(1.10, self.upgrades[1] + upgrade_offsets[1]) #loading mechanism
        tank.armor *= pow(1.14, self.upgrades[2] + upgrade_offsets[2]) #armor
        tank.speed *= pow(1.10, self.upgrades[3] + upgrade_offsets[3]) #engine speed

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
        tank.powerups = self.powerups[:]

        #Update the tank's "start HP and armor" variables
        tank.start_HP = tank.HP
        tank.start_armor = tank.armor

        #Update the tank's upgrade statistics
        tank.update_acct_stats()

        #return the tank now that it is characterized as heavy, light or medium, as well as stocked with ammunition,
        #powerups, and its upgrade stats.
        return tank

    #Return_tank() also calculates total money earned from battle.
    #You give the account() the tank you used in a battle; This function returns the cost to rebuy everything, rebuys necessary items,
    #  Handles cash gain/loss and experience gain/loss.
    def return_tank(self,tank,rebuy=False,bp_to_cash=True,experience=False,verbose=False):
        global CASH_DAMAGE_MULTIPLIER, DEATH_COST, KILL_REWARD
        global EXP_KILL_REWARD, EXP_DEATH_COST, WHIFF_EXPERIENCE, HIT_EXPERIENCE, EXPERIENCE_DAMAGE_MULTIPLIER
        global powerup_price, shell_prices
        # - If we set this flag to True, convert our battle performance to cash -
        if(bp_to_cash):
            # - First, we handle cash -
            earned = 0.0
            # - Convert the tank's total damage to cash -
            self.cash += tank.total_damage * CASH_DAMAGE_MULTIPLIER
            earned += tank.total_damage * CASH_DAMAGE_MULTIPLIER
            if(verbose):
                print(" - Damage dealt: " + str(round(tank.total_damage,1)) + " -> ^ earned from Damage: " + str(round(earned,1)))
                last_earned = earned
            # - Convert our death to negative cash (sad) -
            if(tank.destroyed == True):
                self.cash -= DEATH_COST
                earned -= DEATH_COST
                if(verbose):
                    print(" - ^ Lost from death: " + str(round(earned - last_earned,1)))
                    last_earned = earned
            # - We also need to convert kills to cash -
            self.cash += tank.kills * KILL_REWARD
            earned += tank.kills * KILL_REWARD
            if(verbose):
                print(" - Kills: " + str(tank.kills) + " -> ^ earned from kills: " + str(round(earned - last_earned,1)))
            # - Second, we handle experience -
            old_experience = self.experience #bookmark what *was* our experience
            if(experience):
                self.experience += tank.kills * EXP_KILL_REWARD #kills
                if(verbose):
                    print(" - Experience from kills: " + str(round(tank.kills * EXP_KILL_REWARD,1)))
                if(tank.destroyed == True): #deaths
                    self.experience -= EXP_DEATH_COST
                    if(verbose):
                        print(" - " + str(round(EXP_DEATH_COST,1)) + " experience lost from death")
                # - Handle the hit/miss experience earned -
                total_shots = 0
                for x in range(0,len(tank.shells_used)):
                    total_shots += tank.shells_used[x]
                bookmarked_exp = self.experience
                self.experience -= tank.missed_shots * WHIFF_EXPERIENCE #missed shots
                self.experience += (total_shots - tank.missed_shots) * HIT_EXPERIENCE #hit shots
                if(verbose):
                    print(" - Experience gained from accuracy: " + str(round(self.experience - bookmarked_exp,1)))
                # - Handle damage -
                bookmarked_exp = self.experience
                self.experience += tank.total_damage * EXPERIENCE_DAMAGE_MULTIPLIER
                if(verbose):
                    print(" - Experience gained from damage: " + str(round(self.experience - bookmarked_exp,1)))
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
                    pu_cost += powerup_price
            else: #did we collect more powerups off the map then we used?
                for refund in range(0,abs(tank.powerups_used[x])): #we gets money for that extra powerup.
                    self.cash += powerup_price
                    pu_cost -= powerup_price
        # - Rebuy all shells if we set rebuy to True -
        shell_cost = 0.0
        for x in range(0,len(shell_prices)): #how much would it cost to rebuy all shells?
            shell_cost += shell_prices[x] * tank.shells_used[x] * self.damage_multiplier
            if(rebuy): #if we have this setting on, rebuy all our shells.
                for buy in range(0,tank.shells_used[x]):
                    self.purchase("shell",x)
        # - Sell extra shells (e.g. if we got explosive shells during the game and we have 9/7 shells, sell 2) -
        for x in range(0,len(shell_prices)):
            while(self.shells[x] > max_shells[x]):
                self.refund("shell",x)
                shell_cost -= shell_prices[x] * self.damage_multiplier
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
        global powerup_price, shell_prices, upgrade_start_price, upgrade_increment
        global specialization_start_price, specialization_increment
        global upgrade_limit, max_shells, shell_specs, upgrade_details
        details = None #this variable allows this function to return details on EXACTLY what you're planning on purchasing if view_price == True.
        if(item == "powerup"): #powerups?
            price = powerup_price * self.damage_multiplier
            details = None #no details on powerup
            #Check if account has powerup_price availible. If so, deduct powerup_price from account's balance.
            #Give the account the powerup.
            if(not view_price):
                if(self.cash >= price and self.powerups[item_index] != True):
                    self.cash -= price
                    self.powerups[item_index] = True #we now has powerup!
                else:
                    if(self.powerups[item_index] != True):
                        self.powerups[item_index] = None #make sure powerup is not there and everyone else knows it =(
                    return False #we couldn't get item
        elif(item == "shell"): #ammunition?
            price = shell_prices[item_index] * self.damage_multiplier
            details = "Base D/P - " + str(round(shell_specs[item_index][0],1)) + "/" + str(round(shell_specs[item_index][1],1))
            if(not view_price):
                if(self.cash >= price): #we has the money?
                    if(max_shells[item_index] > self.shells[item_index]): #we're not at our max?
                        self.cash -= price
                        self.shells[item_index] += 1
                    else:
                        return False
                else:
                    return False #we couldn't buy the item
        elif(item == "upgrade"): #an upgrade?
            #OLD PRICE: #price = pow(self.upgrade_start_price, self.upgrades[item_index] + 1)
            price = math.sqrt(upgrade_increment * (self.upgrades[item_index] + 1)) + upgrade_start_price
            # - Calculate the purchase details, which is basically how much of an upgrade this purchase will be -
            if(view_price):
                old_tank = self.create_tank("image","dummy team",[0,0,0,0],True)
                upgrade_offset = []
                for x in self.upgrades:
                    upgrade_offset.append(0)
                upgrade_offset[item_index] += 1
                detailed_diffs = self.create_tank("image","dummy team",upgrade_offset,True)
                diffs_list = []
                difference = None
                for x in range(0,len(self.upgrades)): #calculate what's different from our current stats
                    diffs_list.append([])
                    for y in range(0,len(detailed_diffs.account_stats[x])):
                        diffs_list[x].append(0)
                        diffs_list[x][y] = detailed_diffs.account_stats[x][y] - old_tank.account_stats[x][y]
                    if(0 not in diffs_list[x]):
                        difference = diffs_list[x]
                        break #we've found the purchase difference!
                variables_str = "" #Move our purchase difference stats into a string which we can return later
                if(difference != None): #this if statement is here to prevent trying to iterate through a NoneType variable.
                    for b in difference:
                        variables_str += "+" + str(round(b,1)) + "/"
                    variables_str = variables_str[0:len(variables_str) - 1]
                    details = upgrade_details[x] + variables_str
                else:
                    details = ""
            # - Now the purchase can begin -
            if(not view_price):
                if(self.upgrades[item_index] < upgrade_limit): #we haven't reached the upgrade cap yet?
                    if(self.cash >= price): #we has da money?
                        self.cash -= price
                        self.upgrades[item_index] += 1
                        # - Update the damage multiplier for your tank -
                        self.damage_multiplier = self.create_tank("image","dummy team",[0,0,0,0],True).damage_multiplier
                        self.penetration_multiplier = self.create_tank("image","dummy team",[0,0,0,0],True).penetration_multiplier
                    else: #we didn't have the cash... =(
                        return False
                else: #already upgraded to the max!
                    return False
        elif(item == "specialize"): #we're specializing our tank!
            #OLD PRICE: #price = pow(self.upgrade_start_price, abs(self.specialization + item_index))
            price = math.sqrt(specialization_increment) * abs(self.specialization + item_index) + specialization_start_price
            if(not view_price):
                # - Now, before we are allowed to check whether we have the experience, I need to make sure people sell their shells in their tank to avoid switching to heavy, selling shells and making 100s of ^ -
                noshells = True
                for x in self.shells:
                    if(x != 0):
                        noshells = False
                        break
                if(noshells):
                    if(abs(self.specialization + item_index) <= upgrade_limit): #we haven't reached the specialization cap?
                        if(self.experience >= price):
                            self.specialization += item_index
                            # - Update the damage multiplier for your tank -
                            self.damage_multiplier = self.create_tank("image","dummy team",[0,0,0,0],True).damage_multiplier
                            self.penetration_multiplier = self.create_tank("image","dummy team",[0,0,0,0],True).penetration_multiplier
                        else: #not enough experience...
                            return False
                    else: #no specialization allowed...
                        return False
                else:
                    return False
        if(view_price):
            return [price, details]
        return True #we were able to buy item!

    def refund(self, item, item_index, view_price=False): #return the item selected if you own it.
        global powerup_price, shell_prices, upgrade_start_price, upgrade_increment
        global specialization_start_price, specialization_increment
        global upgrade_limit, max_shells, shell_specs, upgrade_details
        global REFUND_PERCENT
        success = False
        details = None
        if(item == "powerup"): #powerups?
            price = powerup_price * self.damage_multiplier * REFUND_PERCENT
            if(not view_price and self.powerups[item_index] != False):
                self.cash += price
                self.powerups[item_index] = None
                success = True
        elif(item == "shell"): #ammunition?
            price = shell_prices[item_index] * self.damage_multiplier * REFUND_PERCENT
            details = "Base D/P - " + str(round(shell_specs[item_index][0],1)) + "/" + str(round(shell_specs[item_index][1],1))
            if(not view_price and self.shells[item_index] > 0):
                self.cash += price
                self.shells[item_index] -= 1
                success = True
        elif(item == "upgrade"): #an upgrade?
            #OLD PRICE: #price = pow(self.upgrade_start_price, self.upgrades[item_index]) * self.REFUND_PERCENT
            price = (math.sqrt(upgrade_increment * self.upgrades[item_index]) + upgrade_start_price) * REFUND_PERCENT
            # - Calculate the purchase details, starting with HOW much of a downgrade this refund will be -
            if(view_price):
                old_tank = self.create_tank("image","dummy team",[0,0,0,0],True)
                upgrade_offset = []
                for x in self.upgrades:
                    upgrade_offset.append(0)
                upgrade_offset[item_index] -= 1
                detailed_diffs = self.create_tank("image","dummy team",upgrade_offset,True)
                diffs_list = []
                difference = None
                for x in range(0,len(self.upgrades)): #calculate what's different from our current stats
                    diffs_list.append([])
                    for y in range(0,len(detailed_diffs.account_stats[x])):
                        diffs_list[x].append(0)
                        diffs_list[x][y] = detailed_diffs.account_stats[x][y] - old_tank.account_stats[x][y]
                    if(0 not in diffs_list[x]):
                        difference = diffs_list[x]
                        break #we've found the purchase difference!
                variables_str = "" #Move our purchase difference stats into a string which we can return later
                if(difference != None): #this if statement is here to prevent trying to iterate through a NoneType variable.
                    for b in difference:
                        variables_str += str(round(b,1)) + "/"
                    variables_str = variables_str[0:len(variables_str) - 1]
                    details = upgrade_details[x] + variables_str
                else:
                    details = ""
            # - Now we try refund -
            if(not view_price and self.upgrades[item_index] > 0):
                self.cash += price
                self.upgrades[item_index] -= 1
                success = True
                # - Update the damage multiplier for your tank -
                self.damage_multiplier = self.create_tank("image","dummy team",[0,0,0,0],True).damage_multiplier
                self.penetration_multiplier = self.create_tank("image","dummy team",[0,0,0,0],True).penetration_multiplier
        if(view_price): #just lookin' around right now?
            return [price, details]
        elif(not success):
            return False
        return True #else we actually bought something.

### - Quick test to see whether the currency/purchasing system worked. It does! -
##account = Account()
##account.experience = 1000000
##account.cash = 1000000
##pu_opts = ["upgrade","shell","powerup","specialize"]
##pu_ranges = [[0,4], [0,4], [0,6], [-6,7]]
##for opts in range(0,len(pu_opts)):
##    for rpt in range(0,50):
##        for x in range(pu_ranges[opts][0],pu_ranges[opts][1]):
##            account.purchase(pu_opts[opts], x, False)
##            account.purchase(pu_opts[opts], x, True)
##tank = account.create_tank("armor","team")
##print(tank)
