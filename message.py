import random, os, time, sys
from nano25519.nano25519 import ed25519_oop as ed25519
from pyblake2 import blake2b
from bitstring import BitArray
import binascii
from configparser import SafeConfigParser
from modules import nano
import pyqrcode
import emoji

RAW_AMOUNT = 1000000000000000000000000 # 1e24

def get_reply(account, index, wallet_seed):
    pending = nano.get_pending(str(account))
    while len(pending) > 0:
        rx_amount = nano.receive_xrb(int(index), account, wallet_seed)
        pending = nano.get_pending(str(account))
    return rx_amount

def wait_for_reply(account):
    pending = nano.get_pending(str(account))
    while len(pending) == 0:
       pending = nano.get_pending(str(account))
       time.sleep(2)

def numfy(s):
    number = 0
    for e in [ord(c) for c in s]:
        number = (number * 0x110000) + e
    return number

def denumfy(number):
    l = []
    while(number != 0):
        l.append(chr(number % 0x110000))
        number = number // 0x110000
    return ''.join(reversed(l))


parser = SafeConfigParser()
config_files = parser.read('config.ini')

if len(config_files) == 0:
    #Generate random seed
    print('Generate random seed')
    full_wallet_seed = hex(random.SystemRandom().getrandbits(256))
    wallet_seed = full_wallet_seed[2:].upper()

    cfgfile = open("config.ini",'w')
    parser.add_section('wallet')
    parser.set('wallet', 'seed', wallet_seed)
    parser.set('wallet', 'index', '0')
    index = 0

    parser.write(cfgfile)
    cfgfile.close()

else:
    print("Config file successfully loaded")
    index = int(parser.get('wallet', 'index'))
    wallet_seed = parser.get('wallet', 'seed')

priv_key, pub_key = nano.seed_account(str(wallet_seed), 0)
public_key = str(binascii.hexlify(pub_key), 'ascii')

account = nano.account_xrb(str(public_key))

print('\rWelcome to a p2p emoji sending service on the Nano Network')
print('Please be aware that the internal seed is not encrypted so please be careful')
print()

print("\nConnecting to Nano Network...")
previous = nano.get_previous(str(account))
pending = nano.get_pending(str(account))

if (len(previous) == 0) and (len(pending) == 0):
	print("Account not open, please send value to "+ account +" to activate")
	time.sleep(2)
	print("Closing Channel")
	sys.exit()

pending = nano.get_pending(str(account))
if (len(previous) == 0) and (len(pending) > 0):
    print("Opening Account")
    nano.open_xrb(int(index), account, wallet_seed)

pending = nano.get_pending(str(account))

while len(pending) > 0:
    pending = nano.get_pending(str(account))
    nano.receive_xrb(int(index), account, wallet_seed)

print("Account Address: ", account)

#Check Balance
balance = int(nano.get_balance(nano.get_previous(account)))
if balance < 10000:
	print("Please send 0.1 Nano to this address")
else:
	print('You have ' + str(balance) + ' to send emojis')

host = int(input("To open channel press 1, else [Enter] to join existing: "))
target_account = input("Enter recieving account address: ")

if host == 1:
    print()
    print('Channel Opened')
    nano.send_xrb(target_account, 1, account, 0, wallet_seed)
else:
    print("Waiting for host...")
    wait_for_reply(account)
    while len(pending) > 0:
        nano.receive_xrb(int(index), account, wallet_seed)
        pending = nano.get_pending(str(account))

wait_for_reply(account)

while 1:
	text_emoji = ''
	while text_emoji == '':
		text_emoji = input('\nEmoji cheat sheet at (https://www.webfx.com/tools/emoji-cheat-sheet/)\nSend emoji or type !random for random emoji: ')

	if text_emoji == "!random":
		lines = open('CheatSheet.txt').read().splitlines()
		text_emoji = random.choice(lines)
	
	elif text_emoji == "!quit":
		print("Closing Channel")
		sys.exit()

	emoji_img = emoji.emojize(text_emoji,use_aliases=True)
	print("Sending: " + emoji_img + "  -- " + text_emoji)
	print("Price :" + str(numfy(emoji_img)) + " nanos\n")

	#send message via network and change string to base 10
	message_num = numfy(emoji_img)
	nano.send_xrb(target_account, message_num, account, 0, wallet_seed)

	print('Waiting for reply...')
	wait_for_reply(account)

	print('Found reply')

	rx_amount = get_reply(account, index, wallet_seed)
	text_emoji = denumfy(int(rx_amount))
	print()
	print(text_emoji)
	print('\nType !quit to close')


