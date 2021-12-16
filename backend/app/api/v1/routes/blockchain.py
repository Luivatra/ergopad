import requests 

from wallet import Wallet # ergopad.io library
from config import Config, Network # api specific config
from fastapi import APIRouter
from typing import Optional
from pydantic import BaseModel
from time import time

# from base64 import b64encode
# from fastapi import Path
# from fastapi import Request

#region BLOCKHEADER
"""
Blockchain API
---------
Created: vikingphoenixconsulting@gmail.com
On: 20211009
Purpose: allow purchase/redeem tokens locked by ergopad scripts

Notes: 
** PREPARE FOR PROD
!! figure out proper payment amounts to send !!
- build route that tells someone how much they have locked
- set vestingBegin to proper timestamp (current setting is for testing)
.. set the periods correctly (30 days apart?)
- restart with PROD; move CFG back to docker .env
.. verify wallet address
- disable /payment route (only for testing)
.. set debug flag?
- log to database?
.. common events
.. purchase/token data
- add route to show value assigned to wallet?
- /utils/ergoTreeToAddress/{ergoTreeHex} can convert from ergotree (in R4)
- push changes
.. remove keys
.. merge to main
"""
#endregion BLOCKHEADER

DEBUG = True

#region LOGGING
import logging
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"
COLORS = {'WARNING': YELLOW, 'INFO': WHITE, 'DEBUG': BLUE, 'CRITICAL': YELLOW, 'ERROR': RED}
# logging.basicConfig(format=f"[%(asctime)s] %(levelname)s %(threadName)s %(name)s %(message)s", datefmt='%m-%d %H:%M', level=logging.DEBUG)
def formatter_message(message, use_color = True):
    if use_color: message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
    else: message = message.replace("$RESET", "").replace("$BOLD", "")
    return message
class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color = True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)
        
class ColoredLogger(logging.Logger):
    FORMAT = "[$BOLD%(name)-20s$RESET][%(levelname)-18s]  %(message)s ($BOLD%(filename)s$RESET:%(lineno)d)"
    COLOR_FORMAT = formatter_message(FORMAT, True)
    def __init__(self, name):
        logging.Logger.__init__(self, name, (logging.INFO, logging.DEBUG)[DEBUG])

        color_formatter = ColoredFormatter(self.COLOR_FORMAT)

        console = logging.StreamHandler()
        console.setFormatter(color_formatter)

        self.addHandler(console)
        return

logging.setLoggerClass(ColoredLogger)        
#endregion LOGGING

#region INIT
class TokenPurchase(BaseModel):
    wallet: str
    tokens: int
    sigusd: Optional[float] = None

try:
    CFG = Config[Network]
    CFG.ergopadTokenId = '0890ad268cd62f29d09245baa423f2251f1d77ea21443a27d60c3c92377d2e4d'
    headers            = {'Content-Type': 'application/json'}
    tokenInfo          = requests.get(f'{CFG.explorer}/tokens/{CFG.ergopadTokenId}')
    nodeWallet         = Wallet('3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG') # contains tokens
    buyerWallet        = Wallet('3WzKopFYhfRGPaUvC7v49DWgeY1efaCD3YpNQ6FZGr2t5mBhWjmw') # simulate buyer

    validWallets = {
        '3WzKopFYhfRGPaUvC7v49DWgeY1efaCD3YpNQ6FZGr2t5mBhWjmw': 'test buyer',
    }

except Exception as e:
    logging.error(f'Init {e}')
#endregion INIT

blockchain_router = r = APIRouter()

#region ROUTES

# current node info (and more)
@r.get("/info", name="blockchain:info")
def getInfo():
  try:
    st = time() # stopwatch
    nodeInfo = {}    
    res = requests.get(f'{CFG.node}/info', headers=dict(headers, **{'api_key': CFG.ergopadApiKey}))
    if res.ok:
      i = res.json()
      nodeInfo['network'] = Network
      nodeInfo['uri'] = CFG.node
      if 'parameters' in i:
        if 'height' in i['parameters']:
          nodeInfo['currentHeight'] = i['parameters']['height']
      if 'currentTime' in i:
        nodeInfo['currentTime'] = i['currentTime']
      nodeInfo['ergopadTokenId'] = CFG.ergopadTokenId
      nodeInfo['buyer'] = buyerWallet.address
      nodeInfo['seller'] = nodeWallet.address

    logging.debug(f'::TOOK {time()-st:0.4f}s')
    return nodeInfo

  except Exception as e:
    logging.error(f'getBoxesWithUnspentTokens {e}')
    return None

# info about token
@r.get("/tokenInfo/{tokenId}", name="blockchain:tokenInfo")
def getTokenInfo(tokenId):
  # tkn = requests.get(f'{CFG.node}/wallet/balances/withUnconfirmed', headers=dict(headers, **{'api_key': CFG.apiKey})
  try:
    tkn = requests.get(f'{CFG.explorer}/tokens/{tokenId}')
    return tkn.json()
  except Exception as e:
    return {'status': 'error', 'details': f'{CFG.explorer}/tokens/{tokenId}', 'exception': e}

# assember follow info
@r.get("/followInfo/{tokenId}", name="blockchain:followinfo")
def followInfo(followId):    
    try:
        res = f'http://localhost:8080/result/{followId}'
        return res.json()
    
    except Exception as e:
        return {'status': 'fail', 'details': e}    

# find unspent boxes with tokens
@r.get("/unspentTokens", name="blockchain:unspentTokens")
def getBoxesWithUnspentTokens(tokenId=CFG.ergopadTokenId, allowMempool=True):
  try:
    tot = 0
    ergopadTokenBoxes = {}    

    res = requests.get(f'{CFG.node}/wallet/boxes/unspent?minInclusionHeight=0&minConfirmations={(0, -1)[allowMempool]}', headers=dict(headers, **{'api_key': CFG.ergopadApiKey}))
    if res.ok:
      assets = res.json()
      for ast in assets:
        if 'box' in ast:
          if ast['box']['assets'] != []:
            for tkn in ast['box']['assets']:
              if 'tokenId' in tkn and 'amount' in tkn:
                logging.info(tokenId)
                if tkn['tokenId'] == tokenId:
                  tot += tkn['amount']
                  if ast['box']['boxId'] in ergopadTokenBoxes:
                    ergopadTokenBoxes[ast['box']['boxId']].append(tkn)
                  else:
                    ergopadTokenBoxes[ast['box']['boxId']] = [tkn]
                  logging.debug(tkn)

      logging.info(f'found {tot} ergopad tokens in wallet')

    # invalid wallet, no unspent boxes, etc..
    else:
      logging.error('unable to find unspent boxes')

    # return CFG.node
    return ergopadTokenBoxes

  except Exception as e:
    logging.error(f'getBoxesWithUnspentTokens {e}')
    return({'status': 'fail', 'tokenId': tokenId, 'description': e})

# ergoscripts
@r.get("/script/{name}", name="blockchain:script")
def getErgoscript(name, params={}):
  try:
    if name == 'alwaysTrue':
      script = f"""{{
        val x = 1
        val y = 1

        sigmaProp( x == y )
      }}"""

    if name == 'neverTrue':
      script = "{ 1 == 0 }"

    # params = {'buyerWallet': '3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG'}
    if name == 'ergopad':      
      script = f"""{{
        val buyer = PK("{params['buyerWallet']}").propBytes
        val seller = PK("{params['nodeWallet']}").propBytes // ergopad.io
        val isValid = {{
            // 
            val voucher = OUTPUTS(0).R4[Long].getOrElse(0L)

            // voucher == voucher // && // TODO: match token
            buyer == INPUTS(0).propositionBytes
        }}

        sigmaProp(1==1)
      }}"""

    if name == 'vestingLock':
      script = f"""{{
        // only buyer or seller allowed to unlock
        val buyerPK = PK("{params['buyerWallet']}")
        val sellerPK = PK("{params['nodeWallet']}") // ergopad.io

        // val isValidToken = SELF.tokens(0)._1 == "{params['ergopadTokenId']}"        

        // buyer can only spend after vesting period is complete
        val isVested = {{
            buyerPK && 
            CONTEXT.preHeader.timestamp > {params['vestingPeriodEpoch']}L
        }}

        // abandonded; seller allowed recovery of tokens
        val isExpired = {{
            sellerPK &&
            CONTEXT.preHeader.timestamp > {params['expiryEpoch']}L
        }}

        // check for proper tokenId?
        sigmaProp(isVested || isExpired) // sigmaProp(isValidToken && (isVested || isExpired))
      }}"""

    # get the P2S address (basically a hash of the script??)
    logging.debug(script)
    p2s = requests.post(f'{CFG.assembler}/compile', headers=headers, json=script)
    smartContract = p2s.json()['address']
    logging.debug(f'p2s: {p2s.content}')
    logging.info(f'smart contract: {smartContract}')

    return smartContract
  
  except Exception as e:
    logging.error(f'getErgoscript {e}')
    return None

# redeem/disburse tokens after lock
@r.get("/redeem/{box}", name="blockchain:redeem")
def redeemToken(box:str):

  txFee             = CFG.txFee # 
  txBoxTotal        = 0

  # redeem
  outBox = []
  request = {
    'address': "",
    'returnTo': buyerWallet.address,
    'startWhen': {
        'erg': txFee*2 + txBoxTotal, # nergAmount + 2*minTx + txFee
    },
    'txSpec': {
        'requests': outBox,
        'fee': txFee,          
        'inputs': ['$userIns', box],
        'dataInputs': [],
    },
  }

  # make async request to assembler
  # logging.info(request); exit(); # !! testing
  res = requests.post(f'{CFG.assembler}/follow', headers=headers, json=request)    
  logging.debug(request)

  try:
    return({
        'status': 'success', 
        'details': f'',
    })
  
  except Exception as e:
    logging.error(f'purchaseToken: {e}')
    return({'status': 'fail', 'id': -1, 'description': e})

# purchase tokens
@r.post("/purchase/", name="blockchain:purchase")
# def purchaseToken(qty:int=-1, tokenId=CFG.ergopadTokenId, scScript='neverTrue'):
def purchaseToken(tokenPurchase: TokenPurchase):  
  try:
    tokenId           = CFG.ergopadTokenId
    qty               = tokenPurchase.tokens
    ergopadTokenBoxes = getBoxesWithUnspentTokens(tokenId)
    vestingPeriods    = 9 # CFG.vestingPeriods
    vestingDuration   = 5 # mins 
    convertToSeconds  = 60 # vestingDuration in minutes, *60 hours, *24 days, *7 weeks, ... make def for month/year calcs
    # vestingBegin      = 1639785600000 # ms Date and time (GMT): Saturday, December 18, 2021 12:00:00 AM -- int(time()) + vestingDuration*convertToSeconds # now !! TODO: change this
    vestingBegin      = int(time()*1000) # ms -- https://www.unixtimestamp.com/index.php
    expiryEpoch       = vestingBegin + 2*(vestingPeriods*vestingDuration*convertToSeconds)
    txFee             = 10000000 # CFG.txFee # 
    txMin             = 100000 # .01 ergs; remove after reload ENV
    txBoxTotal        = txFee * vestingPeriods # per vesting box
    txSigUSDPerToken  = 1.23 # 1.23 sigusd
    txSigUSD2Ergs     = 7.5 # 1 Erg = 7.5 SigUSDs
    nergsPerErg       = 1000000000
    nergsPerToken     = int(txSigUSDPerToken*txSigUSD2Ergs*nergsPerErg)
    nergTotal         = qty*nergsPerToken + txBoxTotal + txFee*2 # fee needs to allow for return
    scPurchase        = getErgoscript('alwaysTrue', {'ergAmount': txMin, 'toAddress': tokenPurchase.wallet}) # scPurchase = getErgoscript('alwaysTrue', {'ergAmount': txMin, 'toAddress': buyerWallet.address})
    logging.debug(f'smart contract: {scPurchase}')

    # make sure wallet is on list of valid addresses
    if tokenPurchase.wallet not in validWallets:
        return({'status': 'fail', 'description': f'wallet, {tokenPurchase.wallet} not on list of valid wallet addresses.'})

    # 1 outbox per vesting period to lock spending until vesting complete
    outBox = []
    for i in range(vestingPeriods):
      # in event the requested tokens do not divide evenly by vesting period, add remaining to final output
      remainder = (0, qty%vestingPeriods)[i == vestingPeriods-1]
      params = {
        'vestingPeriodEpoch': vestingBegin + i*vestingDuration*convertToSeconds,
        'expiryEpoch': expiryEpoch,
        'buyerWallet': tokenPurchase.wallet,
        'nodeWallet': nodeWallet.address,
        'ergopadTokenId': tokenId
      }
      scVesting = getErgoscript('vestingLock', params=params)
      logging.info(f'vesting period {i}: {params["vestingPeriodEpoch"]}')

      # create outputs for each vesting period; add remainder to final output, if exists
      r4 = '0e'+hex(len(bytearray.fromhex(buyerWallet.ergoTree())))[2:]+buyerWallet.ergoTree() # convert to bytearray
      outBox.append({
        'address': scVesting,
        'value': 2*txFee, # txMin,
        'registers': {
          'R4': r4
        #  'R5': nodeWallet.ergoTree()
        },
        'assets': [{ 
          'tokenId': tokenId,
          'amount': int(qty/vestingPeriods + remainder)
        }]
      })

    # create transaction with smartcontract, into outbox(es), using tokens from ergopad token box
    logging.info(f'build request')
    logging.debug(f'smart contract: {scPurchase}')
    logging.debug(f'outBox: {outBox}')
    request = {
        'address': scPurchase,
        'returnTo': tokenPurchase.wallet,
        'startWhen': {
            'erg': nergTotal # qty*nergsPerToken + txFee*2 + txBoxTotal, # nergAmount + 2*minTx + txFee
        },
        'txSpec': {
            'requests': outBox,
            'fee': txFee,
            'inputs': ['$userIns']+list(ergopadTokenBoxes.keys()),
            'dataInputs': [],
        },
    }

    # make async request to assembler
    # return({'request': request}) # !! testing
    res = requests.post(f'{CFG.assembler}/follow', headers=headers, json=request)    
    logging.debug(request)

    id = res.json()['id']
    fin = requests.get(f'{CFG.assembler}/result/{id}')
    logging.info({'status': 'success', 'fin': fin.json(), 'followId': id, 'request': request})
    return({
        'status': 'success', 
        # 'details': f'send {txBoxTotal+txFee*2} ({txBoxTotal/CFG.nanoergsInErg} ergs + {txFee*2/CFG.nanoergsInErg} fee) to {scPurchase}',
        'details': f'send {nergTotal} ({qty*nergsPerToken} token cost + {txBoxTotal/CFG.nanoergsInErg} ergs + {txFee*2/CFG.nanoergsInErg} fee) to {scPurchase}',
        'fin': fin.json(), 
        'smartContract': scPurchase, 
        'followId': id, 
        'request': request
    })
    logging.debug(f'::TOOK {time()-st:.2f}s')
  
  except Exception as e:
    logging.error(f'purchaseToken: {e}')
    return({'status': 'fail', 'id': -1, 'tokenId': tokenId, 'description': e})

# TEST - send payment from test wallet
@r.get("/sendPayment/{address}/{nergs}", name="blockchain:sendpayment")
def sendPayment(address, nergs):
  # TODO: require login/password or something; disable in PROD
  try:
    if not DEBUG:
      return {'status': 'fail', 'detail': f'only available in DEBUG mode'}    

    sendMe = ''
    isWalletLocked = False
    
    # !! add in check for wallet lock, and unlock/relock if needed
    lck = requests.get(f'http://ergonode2:9052/wallet/status', headers={'Content-Type': 'application/json', 'api_key': 'goalspentchillyamber'})
    logging.info(lck.content)
    if lck.ok:
        if lck.json()['isUnlocked'] == False:
            ulk = requests.post(f'http://ergonode2:9052/wallet/unlock', headers={'Content-Type': 'application/json', 'api_key': 'goalspentchillyamber'}, json={'pass': 'crowdvacationancientamber'})
            logging.info(ulk.content)
            if ulk.ok: isWalletLocked = False
            else: isWalletLocked = True
        else: isWalletLocked = True
    else: isWalletLocked = True

    # unlock wallet
    if isWalletLocked:
        logging.info('unlock wallet')

    # send nergs to address/smartContract from the buyer wallet
    # for testing, address/smartContract is 1==1, which anyone could fulfill
    sendMe = [{
        'address': address,
        'value': int(nergs),
        'assets': [],
    }]
    pay = requests.post(f'http://ergonode2:9052/wallet/payment/send', headers={'Content-Type': 'application/json', 'api_key': 'goalspentchillyamber'}, json=sendMe)

    # relock wallet
    if not isWalletLocked:
        logging.info('relock wallet')

    return {'status': 'success', 'detail': f'payment: {pay.json()}'}

  except Exception as e:
    return {'status': 'fail', 'detail': f'sendPayment\n{sendMe}', 'exception': e}    

### MAIN
if __name__ == '__main__':
    print('API routes: ...')
