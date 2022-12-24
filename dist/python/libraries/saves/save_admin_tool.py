##"save_admin_tool.py" ---VERSION 0.01---
## - A small program to assist managing TBO accounts
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

import pickle
import sys
sys.path.insert(0, "../")
import account

# - Grab the data for start -
print("[START] Opening player data vault...")
pickle_file = open("player_data.pkl","rb+")
data = pickle.load(pickle_file)
pickle_file.close()
print("[SUCCESS] Successfully opened player data.")

def print_names(data):
    for x in data: #print out the names, passwords, cash, experience of each player
        print(str(x.name) + ", " + str(x.password) + ", " + str(round(x.cash,2)) + "^, " + str(round(x.experience,2)) + " EXP")

def delete_account(data):
    account_name = input("[DELETE] Which account do you want to delete (name) ? ")
    account_password = input("[DELETE] Which account do you want to delete (password) ? ")
    deleted = False
    for x in range(0,len(data)):
        if(data[x].name == account_name and data[x].password == account_password):
            del(data[x])
            print("[DELETE] Account deleted successfully.")
            deleted = True
            break
    if(not deleted):
        print("[DELETE] Could not find the specified account! Exiting...")

def create_account(data):
    account_name = input("[CREATE] Provide a name to create a new account: ")
    account_password = input("[CREATE] Provide a password for the new account: ")
    data.append(account.Account(account_name, account_password))
    print("[CREATE] Successfully created account!")

def modify_account(data):
    account_name = input("[MODIFY] Which account do you want to modify (name) ? ")
    account_password = input("[MODIFY] Which account do you want to modify (password) ? ")
    found = False
    for x in range(0,len(data)):
        if(data[x].name == account_name and data[x].password == account_password):
            print("[MODIFY] Account located.")
            command = input("[MODIFY] What do you want to do to the account? ")
            try: #make sure we catch any errors the person may have made while typing this command in
                exec("data[x]" + command) #execute the command requested
                print("[MODIFY] Command executed successfully.")
            except: #the administrator made a typo???
                print("[MODIFY] LOL you made a typo while modifying an account...Please try again.")
            found = True
            break
    if(not found):
        print("[MODIFY] Failed to locate account! Exiting...")

def command_help(commands):
    for x in commands:
        print("Command name: " + x[0] + " \n - Command description: " + x[3])

# - Create a list of commands the admin can perform -
commands = []

commands.append(["print accounts",print_names,data,"Prints out information about all accounts"]) #format: [command name, function, parameter (only 1 allowed)]
commands.append(["delete account",delete_account,data,"Allows you to delete an account of your choice"])
commands.append(["modify account",modify_account,data,"Allows you to modify any aspect of an account by utilizing the commands in account.py - Example: .purchase('shell',3)"])
commands.append(["create account",create_account,data,"Allows you to create a new account without needing to utilize the server's account creation functionality"])
commands.append(["help",command_help,commands,"Prints out this set of messages"])

command = ""
while command != "exit":
    #Get a command to execute
    command = input("[COMMAND] Please enter a command: ")

    found = False
    for x in commands: #find whether we entered a valid command
        if(x[0] == command):
            x[1](x[2]) #run the command
            found = True
    if(not found and command != "exit"):
        print("[COMMAND] Invalid command.")

# - This is the clean-up proceedure...Save our data, and...that's it for now! -
save = input("[SAVE] Do you want to save the changes you made? [yes, no] Anything but 'yes' will qualify as 'no': ")
if(save == "yes"):
    pickle_file = open("player_data.pkl","wb+")
    pickle.dump(data, pickle_file)
    print("[SAVE] Successfully saved data.")
    pickle_file.flush()
    pickle_file.close()
else:
    print("[SAVE] Skipped saving data...Changes have not been saved.")

# - Done! -
print("[EXIT]")
