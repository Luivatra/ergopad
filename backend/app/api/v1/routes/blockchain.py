import requests, os
from starlette.responses import JSONResponse 

from wallet import Wallet # ergopad.io library
from config import Config, Network # api specific config
from fastapi import APIRouter, status
from typing import Optional
from pydantic import BaseModel
from time import time, ctime
from api.v1.routes.asset import get_asset_current_price

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
- /utils/ergoTreeToAddress/{ergoTreeHex} can convert from ergotree (in R4)

** PREPARE FOR PROD
!! figure out proper payment amounts to send !!

Later
- build route that tells someone how much they have locked
?? log to database?
.. common events
.. purchase/token data
- add route to show value assigned to wallet?
- build route that tells someone how much they have locked
- set vestingBegin to proper timestamp (current setting is for testing)
.. set the periods correctly (30 days apart?)

Complete
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
- set vestingBegin to proper timestamp (current setting is for testing)
.. set the periods correctly (30 days apart?)
"""
#endregion BLOCKHEADER

DEBUG = True

#region LOGGING
import logging
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{')

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

#region INIT
class TokenPurchase(BaseModel):
  wallet: str
  tokens: Optional[int] = 0
  sigusd: float

try:
  CFG = Config[Network]
  # CFG.ergopadTokenId = '0890ad268cd62f29d09245baa423f2251f1d77ea21443a27d60c3c92377d2e4d'
  if DEBUG:
    CFG.ergopadTokenId = '191dd93523e052d9be49680508f675f82e461ef5452d60143212beb42b7f62a8'
  else: 
    CFG.ergopadTokenId = ''
  CFG.node           = 'http://73.203.30.137:9053'
  CFG.assembler      = 'http://73.203.30.137:8080'
  CFG.ergopadTokenId = '0890ad268cd62f29d09245baa423f2251f1d77ea21443a27d60c3c92377d2e4d'
  headers            = {'Content-Type': 'application/json'}
  tokenInfo          = requests.get(f'{CFG.explorer}/tokens/{CFG.ergopadTokenId}')
  # mainnet
  nodeWallet         = Wallet('9f2sfNnZDzwFGjFRqLGtPQYu94cVh3TcE2HmHksvZeg1PY5tGrZ') # contains tokens
  buyerWallet        = Wallet('9h71e3KiuJNq6NYshHmcJFtkWni13PysHCCwQKzTeo1d1d92spF') # simulate buyer
  # testnet
  # nodeWallet         = Wallet('3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG') # contains tokens
  # buyerWallet        = Wallet('3WzKopFYhfRGPaUvC7v49DWgeY1efaCD3YpNQ6FZGr2t5mBhWjmw') # simulate buyer

except Exception as e:
  logging.error(f'Init {e}')
#endregion INIT

blockchain_router = r = APIRouter()

#region ROUTES
# current node info (and more)
@r.get("/info", name="blockchain:info")
async def getInfo():
  try:
    st = time() # stopwatch
    nodeInfo = {}    

    # ergonode
    res = requests.get(f'{CFG.node}/info', headers=dict(headers, **{'api_key': CFG.ergopadApiKey}), timeout=2)
    if res.ok:
      i = res.json()
      # nodeInfo['network'] = Network
      # nodeInfo['uri'] = CFG.node
      nodeInfo['ergonodeStatus'] = 'ok'
      if 'parameters' in i:
        if 'height' in i['parameters']:
          nodeInfo['currentHeight'] = i['parameters']['height']
      if 'currentTime' in i:
        nodeInfo['currentTime_ms'] = i['currentTime']
    else:
      nodeInfo['ergonode'] = 'error'

    # assembler
    res = requests.get(f'{CFG.assembler}/state', headers=headers, timeout=2)
    if res.ok:
      nodeInfo['assemblerIsFunctioning'] = res.json()['functioning']      
      nodeInfo['assemblerStatus'] = 'ok'
    else:
      nodeInfo['assemblerIsFunctioning'] = 'invalid'
      nodeInfo['assemblerStatus'] = 'error'

    # wallet and token
    nodeInfo['name'] = myself()
    nodeInfo['network'] = Network
    nodeInfo['ergopadTokenId'] = CFG.ergopadTokenId
    if DEBUG: 
      nodeInfo['buyer'] = buyerWallet.address
    nodeInfo['seller'] = nodeWallet.address 

    nodeInfo['vestingBegin'] = f'{ctime(1643245200)} UTC'
    nodeInfo['sigUSD'] = await get_asset_current_price('sigusd')
    nodeInfo['inDebugMode'] = ('PROD', '!! DEBUG !!')[DEBUG]

    logging.debug(f'::TOOK {time()-st:0.4f}s')
    return nodeInfo

  except Exception as e:
    logging.error(f'{myself()}: {e.message}')
    return {'status': 'error', 'def': myself(), 'message': e.message}

# info about token
@r.get("/tokenInfo/{tokenId}", name="blockchain:tokenInfo")
def getTokenInfo(tokenId):
  # tkn = requests.get(f'{CFG.node}/wallet/balances/withUnconfirmed', headers=dict(headers, **{'api_key': CFG.apiKey})
  try:
    tkn = requests.get(f'{CFG.explorer}/tokens/{tokenId}')
    return tkn.json()
  except Exception as e:
    logging.error(f'{myself()}: {e.message}')
    return {'status': 'error', 'def': myself(), 'message': e.message}

# assember follow info
@r.get("/followInfo/{followId}", name="blockchain:followInfo")
def followInfo(followId):    
  try:
    res = requests.get(f'{CFG.assembler}/result/{followId}')
    return res.json()
    
  except Exception as e:
    logging.error(f'{myself()}: {e.message}')
    return {'status': 'error', 'def': myself(), 'message': e.message}

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
    logging.error(f'{myself()}: {e.message}')
    return {'status': 'error', 'def': myself(), 'message': e.message}

# ergoscripts
@r.get("/script/{name}", name="blockchain:getErgoscript")
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

    if name == 'walletLock':
      script = f"""{{
        sigmaProp(OUTPUTS(0).propositionBytes == fromBase64("{nodeWallet.address}"))
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
    logging.error(f'{myself()}: {e.message}')
    return {'status': 'error', 'def': myself(), 'message': e.message}

# find vesting/vested tokens
@r.get("/vesting/{wallet}", name="blockchain:redeem")
def findVestingTokens(wallet:str):
  try:
    tokenId     = CFG.ergopadTokenId
    blockHeight = 642500 # tokens were created after this
    total       = 0
    boxes       = []

    res = requests.get(f'{ergonode}/wallet/transactions?minConfirmations=0&minInclusionHeight={blockHeight}', headers=dict(headers, **{'api_key': CFG.ergopadApiKey}))
    if res.ok: 
      logging.info('ok')
      # returns array of dicts
      for transaction in res.json():
        # logging.info('transaction...')
        # found boxes
        if 'outputs' in transaction:
          # logging.info('output...')
          # find assets
          for output in transaction['outputs']:
            if 'assets' in output:
              # logging.info('assets...')
              # search tokens
              for asset in output['assets']:
                if 'tokenId' in asset:
                  # logging.info('tokens...')
                  # find ergopad token specifically, going to smart contract
                  if asset['tokenId'] == tokenId and output['address'] != nodeWallet.address:
                    # logging.info('ergopad...')

                    fin = f"""
                      transactionId: {transaction['id']}
                      boxId: {output['boxId']}
                      value: {output['value']}
                      amount: {asset['amount']}
                      creationHeight: {output['creationHeight']}
                    """
                    # fin = f"boxId: {output['boxId']}"
                    boxes.append(output['boxId'])
                    total += 1
                    if fin is None:
                      logging.debug('found, but missing info')
                    else:
                      logging.debug('\n'.join([f.lstrip() for f in fin.split('\n') if f]))

    logging.info(f'{total} ergopad transactions found...')
    # serialize boxes and find wallets in R4

  except Exception as e:
    logging.error(f'{myself()}: {e.message}')
    return {'status': 'error', 'def': myself(), 'message': e.message}

# redeem/disburse tokens after lock
@r.get("/redeem/{box}", name="blockchain:redeem")
def redeemToken(box:str):

  txFee = CFG.txFee # 
  txBoxTotal = 0

  # redeem
  outBox = []
  request = {
    'address': "",
    'returnTo': buyerWallet.address,
    'startWhen': {
        'erg': txFee + txBoxTotal, 
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
    logging.error(f'{myself()}: {e.message}')
    return {'status': 'error', 'def': myself(), 'message': e.message}

# purchase tokens
@r.post("/purchase/", name="blockchain:purchaseToken")
# def purchaseToken(qty:int=-1, tokenId=CFG.ergopadTokenId, scScript='neverTrue'):
async def purchaseToken(tokenPurchase: TokenPurchase):  
  tokenId = CFG.ergopadTokenId
  try:
    buyerWallet       = Wallet(tokenPurchase.wallet)
    amtSigusd         = tokenPurchase.sigusd    
    qtyTokens         = amtSigusd/.011 # seed round / # qty               = tokenPurchase.tokens
    ergopadTokenBoxes = getBoxesWithUnspentTokens(tokenId)
    vestingPeriods    = 9 # CFG.vestingPeriods
    vestingDuration_s = (30*24*60*60, 5*60)[DEBUG] # 5m if debug, else 30 days
    vestingBegin      = 1000*(1643245200, int((time()+120)))[DEBUG] # in debug mode, choose now +2m
    expiryEpoch       = vestingBegin + 365*24*60*60*1000 # 1 year
    txFee             = 2*10000000 # CFG.txFee # 
    txBoxTotal        = txFee * vestingPeriods # per vesting box
    nergsPerErg       = 1000000000
    price             = 5.3 # price             = await get_asset_current_price('sigusd')
    nergTotal         = int(amtSigusd/price*nergsPerErg) # sigusd / current price    
    scPurchase        = getErgoscript('walletLock', {'wallet': nodeWallet.ergoTree()}) # scPurchase        = getErgoscript('alwaysTrue', {'toAddress': buyerWallet.address}) # scPurchase = getErgoscript('alwaysTrue', {'ergAmount': txFee, 'toAddress': buyerWallet.address})
    # logging.debug(f'smart contract: {scPurchase}')

    # check whitelist
    whitelist = {}
    with open(f'whitelist.csv') as f:
      wl = f.readlines()
      for w in wl: 
        whitelist[w.split(',')[2].rstrip()] = {
          'sigusd': float(w.split(',')[0]),
          'tokens': round(float(w.split(',')[1]))
        }

    if buyerWallet.address in whitelist: logging.debug('found wallet in whitelist: {buyerWallet.address}')
    logging.debug(f'sigusd: {amtSigusd}: whitelistSigusd{whitelist[buyerWallet.address]["sigusd"]}')

    # make sure buyer is whitelisted
    if buyerWallet.address not in whitelist:
      return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=f'wallet, {buyerWallet.address} invalid or not on whitelist')

    # make sure buyer remains under sigusd limit
    if amtSigusd > whitelist[buyerWallet.address]['sigusd']:
      return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=f'wallet, {buyerWallet.address} may only request up to {whitelist[buyerWallet.address]["sigusd"]} sigusd')

    # 1 outbox per vesting period to lock spending until vesting complete
    # pay ergopad for tokens
    outBox = [{
        'address': nodeWallet.address,
        'value': nergTotal
    }]
    for i in range(vestingPeriods):
      # in event the requested tokens do not divide evenly by vesting period, add remaining to final output
      remainder = (0, qtyTokens%vestingPeriods)[i == vestingPeriods-1]
      params = {
        'vestingPeriodEpoch': vestingBegin + i*vestingDuration_s,
        'expiryEpoch': expiryEpoch,
        'buyerWallet': buyerWallet.address,
        'nodeWallet': nodeWallet.address,
        'ergopadTokenId': tokenId
      }
      scVesting = getErgoscript('vestingLock', params=params)
      logging.info(f'vesting period {i}: {params["vestingPeriodEpoch"]}')

      # create outputs for each vesting period; add remainder to final output, if exists
      r4 = '0e'+hex(len(bytearray.fromhex(buyerWallet.ergoTree())))[2:]+buyerWallet.ergoTree() # convert to bytearray
      outBox.append({
        'address': scVesting,
        'value': txFee,
        'registers': {
          'R4': r4
        #  'R5': nodeWallet.ergoTree()
        },
        'assets': [{ 
          'tokenId': tokenId,
          'amount': int(qtyTokens/vestingPeriods + remainder)
        }]
      })

    # create transaction with smartcontract, into outbox(es), using tokens from ergopad token box
    logging.info(f'build request')
    request = {
        'address': scPurchase,
        'returnTo': buyerWallet.address,
        'startWhen': {
            'erg': nergTotal + txFee + txBoxTotal,
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
    # logging.debug(request)

    id = res.json()['id']
    fin = requests.get(f'{CFG.assembler}/result/{id}')
    logging.info({'status': 'success', 'fin': fin.json(), 'followId': id, 'request': request})
    return({
        'status': 'success', 
        'details': f'send {nergTotal + txBoxTotal + txFee*2} ({nergTotal/nergsPerErg} token cost + {txBoxTotal/nergsPerErg} ergs + {txFee*2/nergsPerErg} fee) to {scPurchase}',
        'fin': fin.json(), 
        'smartContract': scPurchase, 
        'followId': id, 
        'ergs': (nergTotal + txBoxTotal + txFee*2)/nergsPerErg,
        'request': request
    })
    logging.debug(f'::TOOK {time()-st:.2f}s')
  
  except Exception as e:
    logging.error(f'{myself()}: {e.message}')
    return {'status': 'error', 'def': myself(), 'message': e.message}

# TEST - send payment from test wallet
@r.get("/sendPayment/{address}/{nergs}", name="blockchain:sendPayment")
def sendPayment(address, nergs):
  # TODO: require login/password or something; disable in PROD
  try:
    if not DEBUG:
      return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=f'not found')
      # return {'status': 'fail', 'detail': f'only available in DEBUG mode'}    

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
    logging.error(f'{myself()}: {e.message}')
    return {'status': 'error', 'def': myself(), 'message': e.message}

### MAIN
if __name__ == '__main__':
    print('API routes: ...')
