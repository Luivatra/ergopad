import requests 
from wallet import Wallet
from config import Config, Network
from base64 import b64encode
from fastapi import APIRouter
from fastapi import Path
from fastapi import Request
from time import time

#region BLOCKHEADER
"""
Blockchain API
---------
Created: vikingphoenixconsulting@gmail.com
On: 20211009
Purpose: Returns coin and token values by user, coin or wallet.

Notes: 
"""
#endregion BLOCKHEADER

#region LOGGING
import logging
logging.basicConfig(format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s", datefmt='%m-%d %H:%M', level=logging.DEBUG)
#endregion LOGGING

try:
  CFG = Config[Network]
  CFG.ergopadTokenId = '0890ad268cd62f29d09245baa423f2251f1d77ea21443a27d60c3c92377d2e4d'
  isSimulation = True
  headers = {'Content-Type': 'application/json'}
  tokenInfo = requests.get(f'{CFG.explorer}/tokens/{CFG.ergopadTokenId}')
  buyerWallet = Wallet('3WzKopFYhfRGPaUvC7v49DWgeY1efaCD3YpNQ6FZGr2t5mBhWjmw') # simulate buyer/3WzKopFYhfRGPaUvC7v49DWgeY1efaCD3YpNQ6FZGr2t5mBhWjmw
  nodeWallet = Wallet('3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG') # contains tokens/3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG
  # nodeWallet  = Wallet(CFG.ergopadWallet) # contains tokens
  # buyerWallet  = Wallet(CFG.buyerWallet) # simulate buyer

except Exception as e:
  logging.error(f'Init {e}')

blockchain_router = r = APIRouter()
#endregion INIT

#region ROUTES
#
# current node info
#
@r.get("/info", name="blockchain:info")
def getInfo():
  try:
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
    
    return nodeInfo

  except Exception as e:
    logging.error(f'getBoxesWithUnspentTokens {e}')
    return None

@r.get("/tokenInfo/{tokenId}", name="blockchain:tokenInfo")
def getTokenInfo(tokenId):
  # tkn = requests.get(f'{CFG.node}/wallet/balances/withUnconfirmed', headers=dict(headers, **{'api_key': CFG.apiKey})
  try:
    tkn = requests.get(f'{CFG.explorer}/tokens/{tokenId}')
    return tkn.json()
  except Exception as e:
    return {'status': 'error', 'details': f'{CFG.explorer}/tokens/{tokenId}', 'exception': e}

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

# ergoscript
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
        val buyer = PK("{buyerWallet.address}").propBytes
        val seller = PK("{nodeWallet.address}").propBytes // ergopad.io
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
        val buyerPK = PK("{buyerWallet.address}") // SELF.R4[Coll[Byte]].get
        val sellerPK = PK("{nodeWallet.address}") //.propBytes // ergopad.io

        // buyer can only spend after vesting period is complete
        val isVested = {{
          buyerPK && // getOrElse(INPUTS(0).id) // .R4[Coll[Byte]].get
          CONTEXT.preHeader.timestamp > {params['vestingPeriodEpoch']}
        }}

        // abandonded; seller allowed recovery of tokens
        val isExpired = {{
          sellerPK &&
          CONTEXT.preHeader.timestamp > {params['expiryEpoch']}
        }}

        // check for proper tokenId?
        // isValidToken = SELF.tokens(0)._1 == "{params['ergopadTokenId']}"        
        sigmaProp(isVested || isExpired) // sigmaProp(isValidToken && (isVested || isExpired))
      }}"""

    if name == 'heightLock':
      script = f"""sigmaProp(OUTPUTS(0).R4[Long].getOrElse(0L) >= {params['heightLock']})"""

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

# smartcontract- height lock
@r.get("/purchase/{qty}", name="blockchain:purchase")
def purchaseToken(qty:int=-1, tokenId=CFG.ergopadTokenId, scScript='neverTrue'):

  try:
    # nodeInfo = getInfo()
    ergopadTokenBoxes = getBoxesWithUnspentTokens(tokenId)
    vestingBegin = int(time()) # now !! TODO: change this
    vestingPeriods = 3 # CFG.vestingPeriods
    vestingDuration = 10 # TODO: should match site wording/contract
    convertToSeconds = 60 # vestingDuration in minutes, *60 hours, *24 days, *7 weeks, ... make def for month/year calcs
    expiryEpoch = vestingBegin + 2*(vestingPeriods*vestingDuration*convertToSeconds)
    txFee = CFG.txFee # * CFG.vestingPeriods ??
    txMin = 100000 # .01 ergs; CFG.txMin
    txTotal = txMin * vestingPeriods # without fee
    scPurchase = getErgoscript('ergopad', {'buyerWallet': buyerWallet.address})
    logging.debug(f'smart contract: {scPurchase}')

    # 1 outbox per vesting period to lock spending until vesting complete
    outBox = []
    for i in range(vestingPeriods):
      # in event the requested tokens do not divide evenly by vesting period, add remaining to final output
      remainder = (0, qty%vestingPeriods)[i == vestingPeriods-1]
      params = {
        'vestingPeriodEpoch': vestingBegin + i*vestingDuration*convertToSeconds,
        'expiryEpoch': expiryEpoch,
        'buyerWallet': buyerWallet.address,
        'nodeWallet': nodeWallet.address,
        'ergopadTokenId': tokenId
      }
      logging.debug(params)
      scVesting = getErgoscript('vestingLock', params=params)
      logging.info(f'vesting period {i}: {params["vestingPeriodEpoch"]}')

      # create outputs for each vesting period; add remainder to final output, if exists
      outBox.append({
        'address': scVesting, # buyerWallet.address,
        # 'script': ??,
        'value': txMin,
        'register': {
          'R4': buyerWallet.ergoTree(),
          'R5': nodeWallet.ergoTree()
          # 'R4': vestingBegin + i*vestingDuration*convertToSeconds
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
        'returnTo': buyerWallet.address,
        'startWhen': {
            'erg': txFee*2 + txTotal, # nergAmount + 2*minTx + txFee
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
        'details': f'send {txTotal+txFee*2} ({txTotal/CFG.nanoergsInErg} ergs + {txFee*2/CFG.nanoergsInErg} fee) to {scPurchase}',
        'fin': fin.json(), 
        'smartContract': scPurchase, 
        'followId': id, 
        'request': request
    })
  
  except Exception as e:
    logging.error(f'purchaseToken: {e}')
    return({'status': 'fail', 'id': -1, 'tokenId': tokenId, 'description': e})

@r.get("/sendPayment/{address}/{nergs}", name="blockchain:sendpayment")
def sendPayment(address, nergs):
  # TODO: require login/password or something; disable in PROD
  try:
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
    # pay = requests.post(f'{CFG.buyer}/wallet/payment/send', headers={'Content-Type': 'application/json', 'api_key': CFG.buyerApiKey}, json=sendMe)
    pay = requests.post(f'http://ergonode2:9052/wallet/payment/send', headers={'Content-Type': 'application/json', 'api_key': 'goalspentchillyamber'}, json=sendMe)

    # relock wallet
    if not isWalletLocked:
        logging.info('relock wallet')

    return {'status': 'success', 'detail': f'payment: {pay.json()}'}

  except Exception as e:
    return {'status': 'fail', 'detail': f'sendPayment\n{sendMe}', 'exception': e}    
