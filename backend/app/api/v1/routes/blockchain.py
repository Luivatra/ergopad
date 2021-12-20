import requests, json, os
from starlette.responses import JSONResponse 
from wallet import Wallet # ergopad.io library
from config import Config, Network # api specific config
from fastapi import APIRouter, status
from typing import Optional
from pydantic import BaseModel
from time import time, ctime
from api.v1.routes.asset import get_asset_current_price

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
- set vestingBegin_ms to proper timestamp (current setting is for testing)
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
- set vestingBegin_ms to proper timestamp (current setting is for testing)
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
  amount: float
  isToken: Optional[bool] = True
  currency: Optional[str] = 'SigUSD'

try:
  # if DEBUG:
  validCurrencies    = {
    'seedsale': '82d030c7373263c0f048031bfd214d49fea6942a114a291e36120694b4304e9e',
    'sigusd'  : '03faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf04',
    'ergopad' : '5ff2d1cc22ebf959b1cc65453e4ee225b0fdaf4c38a12e3b4ba32ff769bed70f',
  }

  CFG = Config[Network]
  CFG.ergopadTokenId = validCurrencies['ergopad'] # mainnet test / 10M minted to 9gibNzudNny7MtB725qGM3Pqftho1SMpQJ2GYLYRDDAftMaC285
  CFG.seedTokenId    = validCurrencies['seedsale'] # mainnet test / 1k minted to 9f2sfNnZDzwFGjFRqLGtPQYu94cVh3TcE2HmHksvZeg1PY5tGrZ
  CFG.node           = 'http://192.168.1.81:9052'
  CFG.assembler      = 'http://assembler:5678'
  #CFG.ergopadApiKey  = 'headerbasketcandyjourney'
  headers            = {'Content-Type': 'application/json'}
  tokenInfo          = requests.get(f'{CFG.explorer}/tokens/{CFG.ergopadTokenId}')
  
  # mainnet
  #nodeWallet         = Wallet('9gibNzudNny7MtB725qGM3Pqftho1SMpQJ2GYLYRDDAftMaC285') # contains ergopad tokens
  #buyerWallet        = Wallet('9f2sfNnZDzwFGjFRqLGtPQYu94cVh3TcE2HmHksvZeg1PY5tGrZ') # simulate buyer / seed tokens

  # testnet
  nodeWallet         = Wallet('3WxMzA9TwMYh9M5ivSfHi5VqUDhUS6nX4B8ZQNqGLupZqZfivmUw') # contains tokens
  buyerWallet        = Wallet('3WzKuUxmG7HtfmZNxxHw3ArPzsZZR96yrNkTLq4i1qFwVqBXAU8M') # simulate buyer

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
    # CAREFULL!!! XXX nodeInfo['apikey'] = CFG.ergopadApiKey XXX
    nodeInfo['network'] = Network
    nodeInfo['ergopadTokenId'] = CFG.ergopadTokenId
    if DEBUG: 
      nodeInfo['buyer'] = buyerWallet.address
    nodeInfo['seller'] = nodeWallet.address 

    nodeInfo['vestingBegin_ms'] = f'{ctime(1643245200*1000)} UTC'
    nodeInfo['sigUSD'] = await get_asset_current_price('sigusd')
    nodeInfo['inDebugMode'] = ('PROD', '!! DEBUG !!')[DEBUG]

    logging.debug(f'::TOOK {time()-st:0.4f}s')
    return nodeInfo

  except Exception as e:
    logging.error(f'{myself()}: {e}')
    return {'status': 'error', 'def': myself(), 'message': e}

# info about token
@r.get("/tokenInfo/{tokenId}", name="blockchain:tokenInfo")
def getTokenInfo(tokenId):
  # tkn = requests.get(f'{CFG.node}/wallet/balances/withUnconfirmed', headers=dict(headers, **{'api_key': CFG.apiKey})
  try:
    tkn = requests.get(f'{CFG.explorer}/tokens/{tokenId}')
    return tkn.json()
  except Exception as e:
    logging.error(f'{myself()}: {e}')
    return {'status': 'error', 'def': myself(), 'message': e}

# assember follow info
@r.get("/followInfo/{followId}", name="blockchain:followInfo")
def followInfo(followId):    
  try:
    res = requests.get(f'{CFG.assembler}/result/{followId}')
    return res.json()
    
  except Exception as e:
    logging.error(f'{myself()}: {e}')
    return {'status': 'error', 'def': myself(), 'message': e}

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
    # return f'{CFG.node}/wallet/boxes/unspent?minInclusionHeight=0&minConfirmations={(0, -1)[allowMempool]}, apikey={CFG.ergopadApiKey}'
    return ergopadTokenBoxes

  except Exception as e:
    logging.error(f'{myself()}: {e}')
    return {'status': 'error', 'def': myself(), 'message': e}

# ergoscripts
@r.get("/script/{name}/{params}", name="blockchain:getErgoscript")
def getErgoscript(name, params={}):
  try:
    if name == 'alwaysTrue':
      script = f"""{{
        val x = 1
        val y = 1

        sigmaProp( x == y && HEIGHT < {params['timestamp']})
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
        val buyerPK = PK("{params['buyerWallet']}")
        val sellerPK = PK("{params['nodeWallet']}")
        val sellerOutput = OUTPUTS(0).propositionBytes == sellerPK.propBytes
        val returnFunds = {{
          val total = INPUTS.fold(0L, {{(x:Long, b:Box) => x + b.value}}) - 2000000
          OUTPUTS(0).value >= total && OUTPUTS(0).propositionBytes == buyerPK.propBytes && OUTPUTS.size == 2
        }}
        sigmaProp((returnFunds || sellerOutput) && HEIGHT < {params['timestamp']})
      }}"""

    if name == 'vestingLock':
      script = f"""{{
        // only buyer or seller allowed to unlock
        val buyerPK = PK("{params['buyerWallet']}")
        val sellerPK = PK("{params['nodeWallet']}") // ergopad.io

        // val isValidToken = SELF.tokens(0)._1 == "{params['ergopadTokenId']}"        

        // buyer can only spend after vesting period is complete
        val isVested = {{
            OUTPUTS(0).propositionBytes == buyerPK.propBytes && 
            CONTEXT.preHeader.timestamp > {params['vestingPeriodEpoch']}L
        }}

        // abandonded; seller allowed recovery of tokens
        val isExpired = {{
            OUTPUTS(0).propositionBytes == sellerPK.propBytes &&
            CONTEXT.preHeader.timestamp > {params['expiryEpoch']}L
        }}

        // check for proper tokenId?
        sigmaProp(isVested || isExpired)
      }}"""

    # get the P2S address (basically a hash of the script??)
    # logging.debug(script)
    p2s = requests.post(f'{CFG.assembler}/compile', headers=headers, json=script)
    smartContract = p2s.json()['address']
    # logging.debug(f'p2s: {p2s.content}')
    # logging.info(f'smart contract: {smartContract}')

    return smartContract
  
  except Exception as e:
    logging.error(f'{myself()}: {e}')
    return {'status': 'error', 'def': myself(), 'message': e}

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
    logging.error(f'{myself()}: {e}')
    return {'status': 'error', 'def': myself(), 'message': e}

# redeem/disburse tokens after lock
@r.get("/redeem/{box}", name="blockchain:redeem")
def redeemToken(box:str):

  txFee_nerg = CFG.txFee # 
  txBoxTotal_nerg = 0
  scPurchase = getErgoscript('alwaysTrue',{'timestamp': int(time())})
  # redeem
  outBox = [{
    'address': buyerWallet.address,
    'value': txFee_nerg,
    'assets': [{ 
      'tokenId': validCurrencies['ergopad'],
      'amount': 2
    }]
  }]
  request = {
    'address': scPurchase,
    'returnTo': buyerWallet.address,
    'startWhen': {
        'erg': txFee_nerg + txBoxTotal_nerg, 
    },
    'txSpec': {
        'requests': outBox,
        'fee': txFee_nerg,          
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
        'details': f'send {txFee_nerg} to {scPurchase}',
    })
  
  except Exception as e:
    logging.error(f'{myself()}: {e}')
    return {'status': 'error', 'def': myself(), 'message': e}

# purchase tokens
@r.post("/purchase/", name="blockchain:purchaseToken")
async def purchaseToken(tokenPurchase: TokenPurchase):  
  tokenId = CFG.ergopadTokenId
  try:
    buyerWallet        = Wallet(tokenPurchase.wallet)
    amount             = tokenPurchase.amount
    currency           = tokenPurchase.currency
    isToken            = tokenPurchase.isToken

    ergopadTokenBoxes  = getBoxesWithUnspentTokens(tokenId)
    vestingPeriods     = 9 # CFG.vestingPeriods
    vestingDuration_ms = 1000*(30*24*60*60, 5*60)[DEBUG] # 5m if debug, else 30 days
    vestingBegin_ms    = 1000*(1643245200, int((time()+120)))[DEBUG] # in debug mode, choose now +2m
    expiryEpoch_ms     = vestingBegin_ms + 365*24*60*60*1000 # 1 year
    txFee_nerg         = 1000000
    txBoxTotal_nerg    = txFee_nerg*(1+vestingPeriods) # per vesting box + output box
    nergsPerErg        = 1000000000
     # scPurchase        = getErgoscript('alwaysTrue', {'toAddress': buyerWallet.address}) # scPurchase = getErgoscript('alwaysTrue', {'ergAmount': txFee_nerg, 'toAddress': buyerWallet.address})

    # given amount from web form, find tokens to send and ergs to receive
    price              = 5.3 # await get_asset_current_price('sigusd')
    sendAmount_nerg    = txFee_nerg + txBoxTotal_nerg
    coinAmount_nerg    = 0.0 # init
    tokenAmount        = amount # init
    if not isToken:
      coinAmount_nerg  = int(amount/price*nergsPerErg) # sigusd/price, 1 amount@5.3 = .188679 ergs
      sendAmount_nerg += coinAmount_nerg # additional send amount for coins
      tokenAmount      = amount/.011 # seed round, 1 amount/sigusd = 90.9090 tokens

    # check whitelist
    whitelist = {}
    try:
      with open(f'whitelist.csv') as f:
        wl = f.readlines()
        for w in wl: 
          whitelist[w.split(',')[2].rstrip()] = {
            'amount': float(w.split(',')[0]),
            # 'tokens': round(float(w.split(',')[1]))
          }

    except:
      logging.error(f'ERR: reading whitelist')
      return {'status': 'error', 'message': f'ERR: reading whitelist'}

    # make sure buyer is whitelisted
    if buyerWallet.address not in whitelist:
      logging.debug(f'wallet not found in whitelist: {buyerWallet.address}')
      return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=f'wallet, {buyerWallet.address} invalid or not on whitelist')

    # make sure buyer remains under amount limit
    if amount > whitelist[buyerWallet.address]['amount']:
      logging.debug(f'amount ({amount}) exceeds whitelist amount ({whitelist[buyerWallet.address]["amount"]})')
      return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=f'wallet, {buyerWallet.address} may only request up to {whitelist[buyerWallet.address]["sigusd"]} sigusd')

    # 1 outbox per vesting period to lock spending until vesting complete
    logging.info(f'wallet: ok\nwhitelist: ok\nergs: {coinAmount_nerg} at price {price}')

    # pay ergopad for tokens with coins or tokens
    if isToken:
      outBox = [{
          'address': nodeWallet.address,
          'value': txFee_nerg,
          'assets': [{
            'tokenId': validCurrencies['seedsale'],
            'amount': tokenAmount,
          }]
      }]
    else:
      outBox = [{
          'address': nodeWallet.address,
          'value': coinAmount_nerg
      }]
    # box per vesting period
    for i in range(vestingPeriods):
      # in event the requested tokens do not divide evenly by vesting period, add remaining to final output
      remainder = (0, tokenAmount%vestingPeriods)[i == vestingPeriods-1]
      params = {
        'vestingPeriodEpoch': vestingBegin_ms + i*vestingDuration_ms,
        'expiryEpoch': expiryEpoch_ms,
        'buyerWallet': buyerWallet.address,
        'nodeWallet': nodeWallet.address,
        'ergopadTokenId': tokenId
      }
      scVesting = getErgoscript('vestingLock', params=params)
      logging.info(f'vesting period {i}: {ctime(int(params["vestingPeriodEpoch"])/1000)})')

      # create outputs for each vesting period; add remainder to final output, if exists
      r4 = '0e'+hex(len(bytearray.fromhex(buyerWallet.ergoTree())))[2:]+buyerWallet.ergoTree() # convert to bytearray
      outBox.append({
        'address': scVesting,
        'value': txFee_nerg,
        'registers': {
          'R4': r4
        },
        'assets': [{ 
          'tokenId': tokenId,
          'amount': int(tokenAmount/vestingPeriods + remainder)
        }]
      })
    
    scPurchase = getErgoscript('walletLock', {'nodeWallet': nodeWallet.address, 'buyerWallet': buyerWallet.address, 'timestamp': int(time())})
    # create transaction with smartcontract, into outbox(es), using tokens from ergopad token box
    logging.info(f'build request')
    request = {
        'address': scPurchase,
        'returnTo': buyerWallet.address,
        'startWhen': {
            'erg': sendAmount_nerg,
        },
        'txSpec': {
            'requests': outBox,
            'fee': txFee_nerg,
            'inputs': ['$userIns']+list(ergopadTokenBoxes.keys()),
            'dataInputs': [],
        },
    }
    logging.debug(f'\n::REQUEST::::::::::::::::::\n{json.dumps(request)}\n::REQUEST::::::::::::::::::\n')

    # make async request to assembler
    res = requests.post(f'{CFG.assembler}/follow', headers=headers, json=request)    

    id = res.json()['id']
    fin = requests.get(f'{CFG.assembler}/result/{id}')
    logging.info({'status': 'success', 'fin': fin.json(), 'followId': id})
    return({
        'status'        : 'success', 
        'message'       : f'send {sendAmount_nerg} to {scPurchase}',
        'total'         : sendAmount_nerg/nergsPerErg,
        'coins'         : coinAmount_nerg/nergsPerErg,
        'boxes'         : txBoxTotal_nerg/nergsPerErg,
        'fees'          : txFee_nerg/nergsPerErg,
        'assembler'     : json.dumps(fin.json()),
        'smartContract' : scPurchase, 
        'request'       : json.dumps(request),
    })
    logging.debug(f'::TOOK {time()-st:.2f}s')
  
  except Exception as e:
    logging.error(f'{myself()}: {e}')
    return {'status': 'error', 'def': myself(), 'message': e}

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
    logging.error(f'{myself()}: {e}')
    return {'status': 'error', 'def': myself(), 'message': e}

### MAIN
if __name__ == '__main__':
    print('API routes: ...')
