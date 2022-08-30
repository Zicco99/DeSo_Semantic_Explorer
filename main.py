import time
import requests
import json
import random

from databaseDTO import block_is_in_db, bootstrap_db, clean_insert, dirty_insert
from progress.bar import Bar


#Endpoints
last_block_endp = "https://bitclout.com/api/v1?"
block_info_endp = "https://bitclout.com/api/v1/block"

# A custom http request that retries with a growing interval
def http_request(type,block_hash):
    try_num=0
    while(True):
        try:
            if(type=="lastblock"):
                r = requests.get(last_block_endp)
            if(type=="header"):
                r = requests.post(block_info_endp, json={"HashHex": block_hash})
            if(type=="fullblock"):
                r = requests.post(block_info_endp, json={"HashHex": block_hash,"FullBlock":True})
            return r.json()
        except(requests.exceptions.ConnectionError, json.decoder.JSONDecodeError) as err:
            time.sleep(2**try_num + random.random()*0.01) #Exponential
            try_num+=1



    
def fetch_block(curr_block_hash,prev_block_hash):
    #It's useful to understand when the algorithm stopped in fetching from previous runs (prevents script crashes or data lose)
    in_db = block_is_in_db(curr_block_hash)

    if(not in_db): # The block is not in the DB  -> all transactions should be insered (clean insert)
        
        #Get block data (full block -> transaction list included)
        block_data = http_request("fullblock",curr_block_hash)
        clean_insert(block_data)
    
    else: # Check if the previous block is not the database 
          # if there is not, a previous run stopped here and some transactions could miss -> check which are missing and complete (dirty_insert)
          # otherwise the block has been added as well as all its transactions -> skip
        if (not block_is_in_db(prev_block_hash)):
            block_data = http_request("fullblock",curr_block_hash)
            print(block_data)
            dirty_insert(block_data)
        

def iterative_fetch():

    print("Starting fetching progress:")

    #Get last block hash and its height
    curr_block_header = http_request("lastblock",None)['Header']

    curr_block_hash =  curr_block_header['BlockHashHex']
    prev_block_hash =  curr_block_header['PrevBlockHashHex']

    remaining_blocks = http_request("header",curr_block_hash)['Header']['Height']

    #Start fetching
    with Bar('Processing',max = remaining_blocks) as bar:
        for i in range(remaining_blocks):

            fetch_block(curr_block_hash,prev_block_hash)

            curr_block_hash = prev_block_hash
            prev_block_hash = http_request("header",prev_block_hash)['Header']['PrevBlockHashHex']
            bar.next()

if __name__ == '__main__':

    #Establishing DB connection + parse argv
    bootstrap_db()

    #Start fetching 
    iterative_fetch()

    #Close DB connection
    """ session.close """

    #Particular blocks hashes:
    #00000000003e997ad827fbd44c040e7cbeddf8c5014a2128064a5879a0282196 (zicco99 ops)
    #00000000000068985ffa6adcb5ed373efd060b0ab80ef3ee609571269b44d518 (Bitcoin Exchange)


    
  
    

