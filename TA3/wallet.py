from web3 import Web3
from firebase_admin import db
import time
from datetime import datetime


sepoliaUrl = "https://sepolia.infura.io/v3/7cc0d838c6304750ab8f26877179b0b3" 
web3 = Web3(Web3.HTTPProvider(sepoliaUrl))

class Account():
    def __init__(self, username):
        self.account = web3.eth.account.create()
        self.address = self.account.address
        self.privateKey = self.account.key.hex()
        self.addToDB(self.address, self.privateKey, username)
        
    def addToDB(self, address, privateKey, username):
        ref = db.reference("accounts/" + address + "/")

        ref.set({
            "address" : address,
            "privateKey" :privateKey,
            "username": username
        })

        print("✨✨ ⚡️⚡️ Account added to database! ⚡️⚡️ ✨✨")


class Wallet():
    def __init__(self):
        self.username = None

    def checkConnection(self):
        if web3.is_connected():
           return True
        else:
            return False
        
    def getBalance(self, address, currencyType):
        balance = web3.eth.get_balance(address)
        if(currencyType=='dollar'):
            conversionRate = 1826            
            balance = balance * conversionRate
        return web3.from_wei(balance, 'ether')
        
    
    def makeTransactions(self, senderAddress, receiverAddress, amount, privateKey):
        web3.eth.defaultAccount = senderAddress
        
        transaction = {
            "to": receiverAddress,
            "value": web3.to_wei(amount, "ether"),
            "nonce": web3.eth.get_transaction_count(senderAddress), 
            "gasPrice": web3.to_wei(10, 'gwei'),
            "gas": 21000 
        }

        signedTx = web3.eth.account.sign_transaction(transaction, privateKey)
        tnxHash = web3.eth.send_raw_transaction(signedTx.rawTransaction)
        return tnxHash.hex()
    
    def addTransactionHash(self, tnxHash, senderAddress, receiverAddress, amount):
        ref = db.reference('transactions/' + tnxHash)
        ref.set({
            "from":senderAddress,
            "to":receiverAddress,
            "tnxHash":tnxHash,
            "amount":amount,
            "time": time.time()
        })
        
    # SA3: Add filter parameter
    def getTransactions(self, address, currencyType, filter):
        asSender = list(db.reference('transactions/').order_by_child('from').equal_to(address).get().values())
        asReceiver = list(db.reference('transactions/').order_by_child('to').equal_to(address).get().values())
        allUserTnx = asSender + asReceiver
        # SA3: Check filter and set allUserTnx if its value is 'sent' then store asSender transactions in allUserTnx 
        # elseif check if the its value is 'received' then store asReceiver transactions in allUserTnx
        if(filter == 'sent'):
            allUserTnx = asSender
        elif(filter == 'received'):
            allUserTnx = asReceiver

        allUserTnx = sorted(allUserTnx, key=lambda txn: txn.get('time', 0), reverse=True)

        if(currencyType == 'dollar'):
            conversionRate = 1826     
            allUserTnx = list(map(lambda tnx: {**tnx, "amount": float(tnx["amount"]) * conversionRate}, allUserTnx))
        
        return allUserTnx
         
    def getAccounts(self):
        ref = db.reference('accounts/').order_by_child('username').equal_to(self.username)
        accounts = ref.get()
        accounts = list(accounts.values())
        return accounts

    def addUser(self, username, password):
        ref = db.reference('users/'+ username + "/")
        ref.set({'username': username, 'password': password})
        self.username = username
        return True
    
    def addAccountName(self, name, address):
        ref = db.reference("accounts/" + address + "/")
        ref.update({
            "accountName": name
        })