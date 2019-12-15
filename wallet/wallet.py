from constants import *
import subprocess
import json
from bit import PrivateKeyTestnet
from bit.network import NetworkAPI, satoshi_to_currency
import web3
from eth_account import Account
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.gas_strategies.time_based import medium_gas_price_strategy

conn = Web3.HTTPProvider("http://127.0.0.1:8545")
w3 = Web3(conn)
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
w3.eth.setGasPriceStrategy(medium_gas_price_strategy)

# Welcome Block
print()
print('Welcome to the Mulit-Asset Fintech Wallet!')
print()
print('With this application you can create new Bitcoin Testnet and Ethereum wallets')
print()
print('The following commands are avalible :')
print('derive_wallets(mnemonic, coins) - Returns a dictionary object of 5 wallet address for each coin in coins arguement.')
print('derive_mnemonic(num_words) - Returns word list')
print('def priv_to_acct(coin, pk) - Returns wallet address from private key')
print('def create_tx(coin, account_from_pk, account_to, amount) - {Internal Function of send_tx()} Returns a raw transaction')
print('def send_tx(coin, account_from_pk, account_to, amount) - Sends crypto transaction')
print()
print('To create all avalibe wallets call: derive_wallets(derive_mnemonic(15), [BTCTEST, ETH])')
print('To send a tx call: send_tx(coin, account_from_pk, account_to, amount)')
print()

# Functions
def derive_mnemonic(num_words):
    '''
    Returns a BIP39 word list (mnemoic phrase).
    
    Args: 
    num_words: int, must be one of the following: 12, 15, 18, 21, or 24
    '''
    bashCommand1 = f'php ./derive -g --gen-key --gen-words={num_words} --format=json'
    output = json.loads(subprocess.check_output(bashCommand1, shell=True))
    mnemonic = output[0]['mnemonic']
    return mnemonic


def derive_wallets(mnemonic, coins):
    '''
    Returns a dictionary object of 5 wallet address for each coin in coins arguement.
    
    Args:
    mnemonic = str, a single string of 12, 15, 18, 21, or 24 words matching BIP39 specifications.
    coins = [list], a list of coins to create wallet address for
    
    Supported coins: ETH, BTCTEST
    '''
    coin_dic={}
    for coin in coins:
        bashCommand2 = f'php ./derive -g --format=json --coin={coin} --numderive=5 --mnemonic {mnemonic}'
        addresses = json.loads(subprocess.check_output(bashCommand2, shell=True))
        coin_dic.update( {
            coin:addresses
        })
    return coin_dic


def priv_to_acct(coin, pk):
    '''
    Returns an Account object derived from a private key (pk)
    
    Args:
    coin = str, cryptocurrecy the private key was derived from
    pk = str, a private key matching the coin arguements network requirements
    
    Supported coins: ETH, BTCTEST
    '''
    if coin == ETH:
        return Account.privateKeyToAccount(pk)
    elif coin == BTCTEST:
        return PrivateKeyTestnet(pk)
    else:
        return 'Invalid coin, please enter BTCTEST or ETH'
    
    
def create_tx(coin, account_from_pk, account_to, amount):
    '''
    An internal function of send_tx().  Returns a dictionary object with the raw transaction data in preperation to be sent.
    
    Args:
    coin = str, cryptocurrency the transaction belongs to
    account_from_pk = str, the private key for the account the transaction is be to sent from
    account_to = str, the account the transaction is being sent to
    amount = float, the amount to be sent
    
    Supported coins: ETH, BTCTEST
    '''
    account_from = priv_to_acct(coin, account_from_pk)
    if coin == ETH:
        gas_est = w3.eth.estimateGas(
        {
        
            'from':account_from.address,
            'to':account_to,
            'value':amount,
        }
        )
        return {
        'from':account_from.address,
        'to':account_to,
        'value':amount,
        'gasPrice':w3.eth.gasPrice,
        'gas':gas_est,
        'nonce': w3.eth.getTransactionCount(account_from.address)
        }
    
    if coin == BTCTEST:
        return PrivateKeyTestnet.prepare_transaction(account_from.address, [(account_to, amount, BTC)])
    else:
        return 'Invalid coin, please enter BTCTEST or ETH'
    
    
def send_tx(coin, account_from_pk, account_to, amount):
    '''
    Processes and sends a cryptocurrency transaction on the corresponding network
    
    Args:
    coin = str, cryptocurrency the transaction belongs to
    account_from_pk = str, the private key for the account the transaction is be to sent from
    account_to = str, the account the transaction is being sent to
    amount = float, the amount to be sent
    
    Supported coins: ETH, BTCTEST
    '''
    tx = create_tx(coin, account_from_pk, account_to, amount)
    account_from = priv_to_acct(coin, account_from_pk)
    if coin == ETH:
        signed_tx = account_from.sign_transaction(tx)
        return w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    
    elif coin == BTCTEST:
        signed_tx = account_from.sign_transaction(tx)
        return NetworkAPI.broadcast_tx_testnet(signed_tx)
        
    else:
        return 'Invalid coin, please enter BTCTEST or ETH'
