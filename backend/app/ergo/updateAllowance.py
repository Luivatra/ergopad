import os
import requests
import inspect

from time import time
from argparse import ArgumentParser
from config import Config, Network # api specific config
from wallet import Wallet # ergopad.io library

### LOGGING
import logging
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{')

### ARGV
parser = ArgumentParser(description='ergo wallet')
parser.add_argument('-w', '--wallet', help='mainnet wallet address')
args = parser.parse_args()

### INIT
CFG = Config[Network]

assembler = 'http://38.15.40.14:8888'
ergonode  = 'http://38.15.40.14:9053'
headers   = {'Content-Type': 'application/json', 'api_key': CFG.apiKey}
myself    = lambda: inspect.stack()[1][3]

### FUNCTIONS
def getWhitelist():
    list = {}
    try:
        with open(f'whitelist.csv') as f:
            wl = f.readlines()
            for w in wl: 
                list[w.split(',')[2].rstrip()] = {
                    'amount': float(w.split(',')[0]),
                }
        return list

    except Exception as e:
        return {'status': 'error', 'def': myself(), 'message': e}

def getBlacklist():
    list = {}
    try:
        with open(f'blacklist.tsv') as f:
        bl = f.readlines()
        for l in bl:
            col = l.split('\t')
            list[col[0]] = {
                'timeStamp': col[1],
                'tokenAmount': col[2]
            }
        return list

    except Exception as e:
        return {'status': 'error', 'def': myself(), 'message': e}

def getScans(wallet):
    try:
        # find scans
        res = requests.get(f'{ergonode}/scan/listAll')

        # save new scans

    except Exception as e:
        return {'status': 'error', 'def': myself(), 'message': e}
    
    return res

def getPurchases():
    try:
        # find purchases
        res = requests.get(f'{ergonode}/...')

        # save new??

    except Exception as e:
        return {'status': 'error', 'def': myself(), 'message': e}
    
    return res


### MAIN
if __name__ == '__main__':
    # argv
    wallet = Wallet(args.wallet)

    # get lists
    whitelist = getWhitelist()
    blacklist = getBlacklist()
    
    # find assembler scans    
    scans = getScans(wallet)

    # status of recent purchases
    purchases = getPurchases(scans)
    
    # if recent success
        # update whitelist sigusd amount
        # remove from blacklist


### FIN
