import requests
import math
import datetime
import json

from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import sessionmaker
from main import Block,Transaction

def semantic_analysis(tx):
    functs = {
        "BASIC_TRANSFER":basic_transfer_tx,
        "UPDATE_PROFILE":profile_update_tx,
        "FOLLOW":follow_tx,
        "CREATOR_COIN":creator_coins_tx,
        "SUBMIT_POST":submit_post_tx,
        "LIKE":like_tx,
        "BLOCK_REWARD":block_reward_tx,
        "BITCOIN_EXCHANGE":bitcoin_exchange_tx,
        "PRIVATE_MESSAGE":private_message_tx,
        "UPDATE_BITCOIN_USD_EXCHANGE_RATE":update_exchange_rate_tx,
        "NFT_BID":ntf_bid_tx,
        "CREATE_NFT":ntf_create_tx,
        "UPDATE_NFT":ntf_update_tx,
        "BURN_NFT":ntf_update_tx,
        "ACCEPT_NFT_TRANSFER":ntf_accept_transf_tx,
        "NFT_TRANSFER":ntf_transfer_tx,
        "ACCEPT_NFT_BID":ntf_accept_bid_tx,
        "CREATOR_COIN_TRANSFER":creator_coins_transfer_tx,
        "AUTHORIZE_DERIVED_KEY":authorize_derivated_key_tx
    }
    
    func = functs.get(json.loads(tx.tx_metadata)['TxnType'],None)
    if func is None:
        #TODO: Print type if you find any new kind of tx -> so will be added a parser function
        print(tx.tx_metadata['TxnType'])
    
    else: func(tx)


############## UTILITY FUNCTIONS ########################

def block_get():
    r = requests.get('https://api.bitclout.com/api/v1?block-hash={}'.format(
        "000000000000629f6a71def70792d30ee5fae895b20bf5a7b9538c10598e334a"))
    jsonino = r.json()
    i = 0
    for elem in jsonino['Transactions']:
        print(jsonino['Transactions'][i]['RawTransactionHex'])
        print(i)
        i += 1
    print(i)
    
def get_account_info(user_hash):
    payload = {
        "PublicKeyBase58Check": user_hash}
    endpointURL = "https://bitclout.com/api/v0/" + "get-single-profile"
    response = requests.post(endpointURL, json=payload).json()
    return response

def get_post(post_hash):
    
    payload = {"PostHashHex":post_hash,"FetchParents":False,"CommentOffset":0,"CommentLimit":1,"AddGlobalFeedBool":False}
    endpointURL = "https://bitclout.com/api/v0/get-single-post"
    data_post = requests.post(endpointURL, json=payload).json()
    return data_post

##################### TX SEMANTIC PARSING FUNCTIONS #########################
#(Studying each one step by step -> if you want to check the result uncomment the ones you want to analyse)

def basic_transfer_tx(tx):
    
    #Metadata , Input e Output taken by database should be deserialized
    tx_metadata = json.loads(tx.tx_metadata)
    tx_outputs = json.loads(tx.outputs)
    
    #Analysing BasicTransfer Metadata
    
    tx_id = tx.tx_id_base58
    tx_input_nanos = tx_metadata['BasicTransferTxindexMetadata']['TotalInputNanos'] / 10**9
    tx_receiver_nanos = tx_outputs[0]['AmountNanos'] / 10**9
    tx_fee = tx_metadata['BasicTransferTxindexMetadata']['FeeNanos'] / 10**9
    
    if(len(tx_outputs)==1):
        #Sender and receiver coincide
        try:
            tx_to = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
        except(Exception):
            tx_to = "NO_USERNAME"
        
        print("############################################# [ BASIC_TRANSFER ] ###############################################\n")
        
        print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]" \
        "\n -> {} sent himself {:.10f} [$DESO]"  \
        "\n Fee paid {:.10f} [$DESO]".format(tx_id,tx_input_nanos,tx_to,tx_receiver_nanos,tx_fee))
        
        print("----------------------------------------------------------------------------------------------------------------\n")
        
    
    else:
        #Get username of users involved
        try:
            tx_from = get_account_info(tx_metadata["AffectedPublicKeys"][1]["PublicKeyBase58Check"])['Profile']['Username']
        except(Exception):
            tx_from = "NO_USERNAME"
            
        try:
            tx_to = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
        except(Exception):
            tx_to = "NO_USERNAME"
        
        #Analyse the output
        tx_transactor_nanos = tx_outputs[1]['AmountNanos'] / 10**9
        
        print("############################################### [ BASIC_TRANSFER ] #############################################\n")
        
        print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]" \
            "\n -> {} gets {:.10f} [$DESO] as sender change"  \
            "\n -> {} gets {:.10f} [$DESO] as receiver" \
            "\n Fee paid {:.10f} [$DESO]\n".format(tx_id,tx_input_nanos,tx_from,tx_transactor_nanos,tx_to,tx_receiver_nanos,tx_fee))
        
        print("----------------------------------------------------------------------------------------------------------------\n")
    
def profile_update_tx(tx):
    
    #Metadata , Input e Output taken by database should be deserialized
    tx_metadata = json.loads(tx.tx_metadata)
    tx_inputs = json.loads(tx.inputs)
    tx_outputs = json.loads(tx.outputs)
    
    #Analysing Profile Update Metadata
    
    tx_id = tx.tx_id_base58
    tx_input_nanos = tx_metadata['BasicTransferTxindexMetadata']['TotalInputNanos'] / 10**9
    
    try:
        user = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        user = "NO_USERNAME"
    
    
    tx_receiver_nanos = tx_outputs[0]['AmountNanos'] / 10**9
    tx_fee = tx_metadata['BasicTransferTxindexMetadata']['FeeNanos'] / 10**9
    
    #Analysing Profile Update Metadata
    profile = tx_metadata["UpdateProfileTxindexMetadata"]
    
    n_user = profile["NewUsername"]
    n_descr = profile["NewDescription"]
    n_pic = profile["NewProfilePic"]
    n_founder_reward = profile["NewCreatorBasisPoints"] / 100
    n_is_hidden = profile["IsHidden"]
    
    #TODO(DELETEME): This field is deprecated and should be deleted because we're not allowing staking to profiles
    n_stake_multiple_basis_points = profile["NewStakeMultipleBasisPoints"] / 100
    
    
    print("########################################## [ PROFILE UPDATE ] ##################################################\n")
    
    print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]" \
    "\n -> {} updated his profile ,getting as change {:.10f} [$DESO]"  \
    "\n Fee paid {:.10f} [$DESO]".format(tx_id,tx_input_nanos,user,tx_receiver_nanos,tx_fee))
    
    print("New profile data of the user {} :" \
    "\n -> Username : {} \n -> Description : {}"  \
    "\n -> Picture [Base64 String encoded as a link] : {}"  \
    "\n -> Founder Reward : {} % \n -> IsHidden : {} \n".format(user,n_user,n_descr,n_pic,n_founder_reward,n_is_hidden))
    
    print("----------------------------------------------------------------------------------------------------------------\n")
    
def follow_tx(tx):
    
    #Metadata , Input e Output taken by database should be deserialized
    tx_metadata = json.loads(tx.tx_metadata)
    tx_inputs = json.loads(tx.inputs)
    tx_outputs = json.loads(tx.outputs)
    
    #Analysing Follow Metadata
    
    tx_id = tx.tx_id_base58
    
    try:
        follower_username = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        follower_username = "NO_USERNAME"
        
    try:
        followed_username = get_account_info(tx_metadata["AffectedPublicKeys"][1]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        followed_username = "NO_USERNAME"
    
    tx_input_nanos = tx_metadata['BasicTransferTxindexMetadata']['TotalInputNanos'] / 10**9
    tx_follower_change = tx_outputs[0]['AmountNanos'] / 10**9
    tx_fee = tx_metadata['BasicTransferTxindexMetadata']['FeeNanos'] / 10**9
    
    is_unfollow = tx_metadata["FollowTxindexMetadata"]["IsUnfollow"]
    
    if(is_unfollow==False):
        
        print("################################################### [FOLLOW] ###################################################\n")
        
        print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]" \
        "\n -> {} started to follow {}, getting as change {:.10f} [$DESO]"  \
        "\n Fee paid {:.10f} [$DESO]\n".format(tx_id,tx_input_nanos,follower_username,followed_username,tx_follower_change,tx_fee))
        
        print("----------------------------------------------------------------------------------------------------------------\n")
    
    else:
        
        print("################################################## [UNFOLLOW] #################################################\n")
        
        print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]" \
        "\n -> {} stopped to follow {}, getting as change {:.10f} [$DESO]"  \
        "\n Fee paid {:.10f} [$DESO]\n".format(tx_id,tx_input_nanos,follower_username,followed_username,tx_follower_change,tx_fee))
        
        print("----------------------------------------------------------------------------------------------------------------\n")
    
    
def creator_coins_tx(tx):
    
    #Metadata , Input e Output taken by database should be deserialized
    tx_metadata = json.loads(tx.tx_metadata)
    tx_inputs = json.loads(tx.inputs)
    tx_outputs = json.loads(tx.outputs)
    
    #Analysing CreatorCoinsTX Metadata
    tx_id = tx.tx_id_base58
    
    try:
        transactor_username = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        transactor_username = "NO_USERNAME"
    
    try:
        creator_username = get_account_info(tx_metadata["AffectedPublicKeys"][1]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        creator_username = "NO_USERNAME"
    
    tx_input_nanos = tx_metadata['BasicTransferTxindexMetadata']['TotalInputNanos'] / 10**9
    tx_transactor_change = tx_outputs[0]['AmountNanos'] / 10**9
    tx_fee = tx_metadata['BasicTransferTxindexMetadata']['FeeNanos'] / 10**9
    
    cc_meta = tx_metadata["CreatorCoinTxindexMetadata"]
    op_type = cc_meta["OperationType"]
    
    if(op_type=="buy"):
        
        deso_used = cc_meta["DeSoToSellNanos"] / 10**9
        
        print("############################################# [CREATOR COIN (BUY)] #############################################\n")
        
        print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]" \
        "\n -> {} spent {:.10f} [$DESO], to buy {}'s creator coin, getting as change {:.10f} [$DESO]"  \
        "\n Fee paid {:.10f} [$DESO]\n".format(tx_id,tx_input_nanos,transactor_username,deso_used,creator_username,tx_transactor_change,tx_fee))
    
        print("----------------------------------------------------------------------------------------------------------------\n")
        
    else:
        
        creator_coins_sold = cc_meta["CreatorCoinToSellNanos"] / 10**9
        
        tx_output = tx_metadata["TxnOutputs"][0]["AmountNanos"]
        gain = tx_metadata["CreatorCoinTxindexMetadata"]["DESOLockedNanosDiff"]*-1 
        sell_fee = math.floor(gain / 10000) + 1
    
        total_output = (tx_output + gain - sell_fee)/10**9
        
        print("############################################# [CREATOR COIN (SELL)] ############################################\n")

        print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]" \
        "\n -> {} sold {:.10f} of {}'s creator coin for {:.10f} [$DESO] , getting as change {:.10f} [$DESO]"  \
        "\n Fee paid {:.10f} [$DESO]\n".format(tx_id,tx_input_nanos,transactor_username,creator_coins_sold,creator_username,gain/10**9,total_output,tx_fee))

        print("----------------------------------------------------------------------------------------------------------------\n")
        
def submit_post_tx(tx):
    
    #Metadata , Input e Output taken by database should be deserialized
    tx_metadata = json.loads(tx.tx_metadata)
    tx_inputs = json.loads(tx.inputs)
    tx_outputs = json.loads(tx.outputs)
    
    #Analysing SubmitPost Metadata

    tx_id = tx.tx_id_base58
    
    tx_input_nanos = tx_metadata['BasicTransferTxindexMetadata']['TotalInputNanos'] / 10**9
    tx_fee = tx_metadata['BasicTransferTxindexMetadata']['FeeNanos'] / 10**9
    
    post_hash = tx_metadata["SubmitPostTxindexMetadata"]["PostHashBeingModifiedHex"]
    
    data_post = get_post(post_hash)
    
    txt = data_post['PostFound']['Body']
    
    if data_post['PostFound']['ImageURLs'] is None : imagesURLs=[]
    else: imagesURLs = data_post['PostFound']['ImageURLs']
    
    if data_post['PostFound']['VideoURLs'] is None : videoURLs=[]
    else: videoURLs = data_post['PostFound']['VideoURLs']
    
    try:
        poster_username = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
            poster_username = "NO_USERNAME"
    
    try:
        reposted_username = get_account_info(tx_metadata["AffectedPublicKeys"][1]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        #It's a post
        print("#################################################### [POST] ####################################################\n")

        print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]".format(tx_id,tx_input_nanos))
        print('-> {} posted : \n "{}"'.format(poster_username,txt))
                
        if(imagesURLs or videoURLs) : 
            print("Media Attached:")
            for url in imagesURLs : print("-Image -> "+ url)
            for url in videoURLs : print("-Video -> "+ url)
        
        print("\nFee paid {:.10f} [$DESO]\n".format(tx_fee))
        
        print("----------------------------------------------------------------------------------------------------------------\n")
        
        return
    
    #O/W It's a repost
    print("################################################### [REPOST] ###################################################\n")
    
    print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]".format(tx_id,tx_input_nanos))
    print('-> {} reposted {} : \n "{}"'.format(poster_username,reposted_username,txt))
            
    if(imagesURLs or videoURLs) : 
        print("\n Media Attached:")
        for url in imagesURLs : print("-Image -> "+ url)
        for url in videoURLs : print("-Video -> "+ url)
    
    print("\nFee paid {:.10f} [$DESO]\n".format(tx_fee))
    
    print("----------------------------------------------------------------------------------------------------------------\n")


def like_tx(tx):
    
    #Metadata , Input e Output taken by database should be deserialized
    tx_metadata = json.loads(tx.tx_metadata)
    tx_inputs = json.loads(tx.inputs)
    tx_outputs = json.loads(tx.outputs)
    
    tx_id = tx.tx_id_base58
    
    tx_input_nanos = tx_metadata['BasicTransferTxindexMetadata']['TotalInputNanos'] / 10**9
    tx_fee = tx_metadata['BasicTransferTxindexMetadata']['FeeNanos'] / 10**9
    
    isunlike = tx_metadata["LikeTxindexMetadata"]["IsUnlike"]
    post_hash = tx_metadata["LikeTxindexMetadata"]["PostHashHex"]
    
    try:
        liker_username = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        liker_username = "NO_USERNAME"
    
    try:
        poster_username = get_account_info(tx_metadata["AffectedPublicKeys"][1]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        poster_username = "NO_USERNAME"
    
    print("#################################################### [LIKE] ####################################################\n")
    
    print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]".format(tx_id,tx_input_nanos))
    if(isunlike==False) :
        print("-> {} liked {}'s post \n with the ID : {} \n ".format(liker_username,poster_username,post_hash))
    else :
        print("-> {} unliked {}'s post \n with the ID : {} \n ".format(liker_username,poster_username,post_hash))
    
    print("\nFee paid {:.10f} [$DESO]\n".format(tx_fee))
    
    print("----------------------------------------------------------------------------------------------------------------\n")
    
    
def block_reward_tx(tx):
    
    #Metadata , Input e Output taken by database should be deserialized
    tx_metadata = json.loads(tx.tx_metadata)
    tx_inputs = json.loads(tx.inputs)
    tx_outputs = json.loads(tx.outputs)
    
    tx_id = tx.tx_id_base58
    reward = tx_outputs[0]["AmountNanos"] / 10**9
    
    try:
        miner_username = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        miner_username = "NO_USERNAME"
    
    print("################################################### [REWARD] ###################################################\n")
    
    print("TRANSACTION ID {} : Input -> None [$DESO]" \
            "\n -> {} gets {:.10f} [$DESO] as miner" \
            "\n No Fee paid [$DESO]".format(tx_id,miner_username,reward))
    
    print("----------------------------------------------------------------------------------------------------------------\n")
    
    
    
def bitcoin_exchange_tx(tx):
    
    #Metadata , Input e Output taken by database should be deserialized
    tx_metadata = json.loads(tx.tx_metadata)
    
    tx_id = tx.tx_id_base58
    exchange_metadata = tx_metadata["BitcoinExchangeTxindexMetadata"]
    btc_addr = exchange_metadata['BitcoinSpendAddress']
    btc_spent = exchange_metadata['SatoshisBurned'] / 10**9
    deso_gen = exchange_metadata["NanosCreated"] / 10**9
    fee = tx_metadata["BasicTransferTxindexMetadata"]["FeeNanos"]/ 10**9
    
    #Ci sono i campi TotalNanosPurchasedBefore e TotalNanosPurchasedAfter e BitcoinTxnHash da valutare 
        
    try:
        buyer_username = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        buyer_username = "NO_USERNAME"
    
    print("############################################### [ BTC_EXCHANGE ] ###############################################\n")
    
    print("TRANSACTION ID {} : Input -> None [$DESO]" \
            "\n -> {} bought {:.10f} [$DESO] for {:.10f} [BTC]" \
            "\n Bitcoin Address:{}"
            "\n Fee paid {} [$DESO]\n".format(tx_id,buyer_username,deso_gen,btc_spent,btc_addr,fee))
    
    print("----------------------------------------------------------------------------------------------------------------\n")
    

def private_message_tx(tx):
    
    tx_metadata = json.loads(tx.tx_metadata)
    tx_inputs = json.loads(tx.inputs)
    tx_outputs = json.loads(tx.outputs)
    
    tx_id = tx.tx_id_base58
    tx_input_nanos = tx_metadata['BasicTransferTxindexMetadata']['TotalInputNanos'] / 10**9
    
    try:
        msg_sender_username = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        msg_sender_username = "NO_USERNAME"
        
    try:
        msg_receiver_username = get_account_info(tx_metadata["AffectedPublicKeys"][1]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        msg_receiver_username = "NO_USERNAME"
        
    #Analyse the output
    tx_fee = tx_metadata['BasicTransferTxindexMetadata']['FeeNanos'] / 10**9
    msg_time = datetime.datetime.fromtimestamp(tx_metadata['PrivateMessageTxindexMetadata']['TimestampNanos'] // 10**9)
    
    print("############################################## [ PRIVATE_MSG ] ###############################################\n")
    
    print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]" \
        "\n -> {} sent a message to {} on {} UTC" \
        "\n Fee paid {:.10f} [$DESO]\n".format(tx_id,tx_input_nanos,msg_sender_username,msg_receiver_username,msg_time,tx_fee))
    
    print("----------------------------------------------------------------------------------------------------------------\n")


def update_exchange_rate_tx(tx):
    
    print("############################################## [ RATE_EXCHANG ] ###############################################\n")
    
    print("Bitcoin/USD transaction rate has been updated!")
            
    print("----------------------------------------------------------------------------------------------------------------\n")


def ntf_bid_tx(tx):
    
    tx_metadata = json.loads(tx.tx_metadata)
    tx_inputs = json.loads(tx.inputs)
    tx_outputs = json.loads(tx.outputs)
    
    tx_id = tx.tx_id_base58
    tx_input_nanos = tx_metadata['BasicTransferTxindexMetadata']['TotalInputNanos'] / 10**9
    
    try:
        bidder = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        bidder = "NO_USERNAME"
        
    try:
        ntf_owner = get_account_info(tx_metadata["AffectedPublicKeys"][1]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        ntf_owner = "NO_USERNAME"
        
    #Analyse the output
    tx_fee = tx_metadata['BasicTransferTxindexMetadata']['FeeNanos'] / 10**9
    bid_amount =  tx_metadata['NFTBidTxindexMetadata']['BidAmountNanos']
    NTF_Hash = tx_metadata['NFTBidTxindexMetadata']['NFTPostHashHex']
    
    print("############################################## [ NFT_BID ] ###############################################\n")
    
    print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]" \
        "\n -> {} bidded on {}'s NTF {:.10f} [$DESO]" \
        "\n -> NTF's Hash : {}" \
        "\n Fee paid {:.10f} [$DESO]\n".format(tx_id,tx_input_nanos,bidder,ntf_owner,bid_amount,NTF_Hash,tx_fee))
    
    print("----------------------------------------------------------------------------------------------------------------\n")

def ntf_create_tx(tx):
    
    tx_metadata = json.loads(tx.tx_metadata)
    
    tx_id = tx.tx_id_base58
    tx_input_nanos = tx_metadata['BasicTransferTxindexMetadata']['TotalInputNanos'] / 10**9
    post_hash = tx_metadata["CreateNFTTxindexMetadata"]["NFTPostHashHex"]
    
    try:
        nft_creator = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        nft_creator = "NO_USERNAME"
        
    #Analyse the output
    tx_fee = tx_metadata['BasicTransferTxindexMetadata']['FeeNanos'] / 10**9
    

    print("############################################## [ NFT_CREATE ] ###############################################\n")
    
    print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]" \
        "\n -> {} created an NTF on the post {}" \
        "\n Fee paid {:.10f} [$DESO]\n".format(tx_id,tx_input_nanos,nft_creator,post_hash,tx_fee))
    
    print("----------------------------------------------------------------------------------------------------------------\n")
    
def ntf_update_tx(tx):
    
    tx_metadata = json.loads(tx.tx_metadata)
    
    tx_id = tx.tx_id_base58
    tx_input_nanos = tx_metadata['BasicTransferTxindexMetadata']['TotalInputNanos'] / 10**9
    post_hash = tx_metadata["UpdateNFTTxindexMetadata"]["NFTPostHashHex"]
    on_sale = tx_metadata["UpdateNFTTxindexMetadata"]["IsForSale"]
    
    try:
        nft_creator = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        nft_creator = "NO_USERNAME"
        
    #Analyse the output
    tx_fee = tx_metadata['BasicTransferTxindexMetadata']['FeeNanos'] / 10**9
    
    if(on_sale):
        print("############################################## [ NFT_UPDATE ] ###############################################\n")
        
        print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]" \
            "\n -> {} updated an NTF on the post {}, now it's on sale " \
            "\n Fee paid {:.10f} [$DESO]\n".format(tx_id,tx_input_nanos,nft_creator,post_hash,tx_fee))
        
        print("----------------------------------------------------------------------------------------------------------------\n")
    else:
        print("############################################## [ NFT_UPDATE ] ###############################################\n")
        
        print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]" \
            "\n -> {} updated an NTF on the post {}, took off from sale " \
            "\n Fee paid {:.10f} [$DESO]\n".format(tx_id,tx_input_nanos,nft_creator,post_hash,tx_fee))
        
        print("----------------------------------------------------------------------------------------------------------------\n")

def ntf_burn_tx(tx):
    
    tx_metadata = json.loads(tx.tx_metadata)
    
    tx_id = tx.tx_id_base58
    tx_input_nanos = tx_metadata['BasicTransferTxindexMetadata']['TotalInputNanos'] / 10**9
    
    try:
        nft_creator = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        nft_creator = "NO_USERNAME"
        
    #Analyse the output
    tx_fee = tx_metadata['BasicTransferTxindexMetadata']['FeeNanos'] / 10**9

    print("############################################## [ NTF_BURN ] ###############################################\n")
    
    print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]" \
        "\n -> {} burned an NTF" \
        "\n Fee paid {:.10f} [$DESO]\n".format(tx_id,tx_input_nanos,nft_creator,tx_fee))
    
    print("----------------------------------------------------------------------------------------------------------------\n")

def ntf_accept_transf_tx(tx):
    
    tx_metadata = json.loads(tx.tx_metadata)
    
    tx_id = tx.tx_id_base58
    tx_input_nanos = tx_metadata['BasicTransferTxindexMetadata']['TotalInputNanos'] / 10**9
    
    try:
        nft_creator = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        nft_creator = "NO_USERNAME"
        
    #Analyse the output
    tx_fee = tx_metadata['BasicTransferTxindexMetadata']['FeeNanos'] / 10**9

    print("############################################## [ TRANSFER_ACC ] ###############################################\n")
    
    print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]" \
        "\n -> {} accepted an NTF-Transfer" \
        "\n Fee paid {:.10f} [$DESO]\n".format(tx_id,tx_input_nanos,nft_creator,tx_fee))
    
    print("----------------------------------------------------------------------------------------------------------------\n")

def ntf_transfer_tx(tx):
     
    tx_metadata = json.loads(tx.tx_metadata)
    
    tx_id = tx.tx_id_base58
    tx_input_nanos = tx_metadata['BasicTransferTxindexMetadata']['TotalInputNanos'] / 10**9
    
    try:
        sender = get_account_info(tx_metadata["AffectedPublicKeys"][1]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        sender = "NO_USERNAME"
    
    try:
        receiver = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        receiver = "NO_USERNAME"
        
    #Analyse the output
    tx_fee = tx_metadata['BasicTransferTxindexMetadata']['FeeNanos'] / 10**9
    nft_hash = tx_metadata['NFTTransferTxindexMetadata']['NFTPostHashHex']
    
    print("############################################## [ NFT_TRANSFER ] ###############################################\n")
    
    print("TRANSACTION ID {} : Input -> {:.10f} [$DESO] " \
        "\n -> {}'s NFT has been sent to {}, waiting for a Nft-Transfer-Accept" \
        "\n NFT Hash: {}" \
        "\n Fee paid {:.10f} [$DESO]\n".format(tx_id,tx_input_nanos,sender,receiver,nft_hash,tx_fee))
    
    print("----------------------------------------------------------------------------------------------------------------\n")
    


def ntf_accept_bid_tx(tx):
    
    tx_metadata = json.loads(tx.tx_metadata)
    
    tx_id = tx.tx_id_base58
    tx_input_nanos = tx_metadata['BasicTransferTxindexMetadata']['TotalInputNanos'] / 10**9
    
    try:
        seller = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        seller = "NO_USERNAME"
    
    try:
        buyer = get_account_info(tx_metadata["AffectedPublicKeys"][1]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        buyer = "NO_USERNAME"
        
    #Analyse the output
    tx_fee = tx_metadata['BasicTransferTxindexMetadata']['FeeNanos'] / 10**9
    nft_hash = tx_metadata['AcceptNFTBidTxindexMetadata']['NFTPostHashHex']
    bid_amount = tx_metadata['AcceptNFTBidTxindexMetadata']['BidAmountNanos'] / 10**9
    coin_bonus = tx_metadata['AcceptNFTBidTxindexMetadata']['CreatorCoinRoyaltyNanos'] / 10**9
    
    print("############################################## [ BID_ACCEPT ] ###############################################\n")
    
    print("TRANSACTION ID {} : Input -> {:.10f} [$DESO] " \
        "\n -> {} bough {}'s NFT at the cost of {:.10f} getting: " \
        "\n NFT Hash: {}" \
        "\n {}'s coin got as fedelity bonus: {}" \
        "\n Fee paid {:.10f} [$DESO]\n".format(tx_id,tx_input_nanos,buyer,seller,bid_amount,nft_hash,buyer,coin_bonus,tx_fee))
    
    print("----------------------------------------------------------------------------------------------------------------\n")
    

def creator_coins_transfer_tx(tx):
    
    tx_metadata = json.loads(tx.tx_metadata)
    
    tx_id = tx.tx_id_base58
    tx_input_nanos = tx_metadata['BasicTransferTxindexMetadata']['TotalInputNanos'] / 10**9
    
    try:
        sender = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        sender = "NO_USERNAME"
    
    try:
        receiver = get_account_info(tx_metadata["AffectedPublicKeys"][1]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        receiver = "NO_USERNAME"
        
    #Analyse the output
    tx_fee = tx_metadata['BasicTransferTxindexMetadata']['FeeNanos'] / 10**9
    creator_user = tx_metadata['CreatorCoinTransferTxindexMetadata']['CreatorUsername']
    creator_coins = tx_metadata['CreatorCoinTransferTxindexMetadata']['CreatorCoinToTransferNanos'] / 10**9
    
    print("############################################## [ CC_TRANSFER ] ###############################################\n")
    
    print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]" \
        "\n -> {} sent {:.10f} {}'s coin to {}" \
        "\n Fee paid {:.10f} [$DESO]\n".format(tx_id,tx_input_nanos,sender,creator_coins,creator_user,receiver,tx_fee))
    
    print("----------------------------------------------------------------------------------------------------------------\n")
    
    
def authorize_derivated_key_tx(tx):
    tx_metadata = json.loads(tx.tx_metadata)
    
    tx_id = tx.tx_id_base58
    tx_input_nanos = tx_metadata['BasicTransferTxindexMetadata']['TotalInputNanos'] / 10**9
    
    try:
        auth = get_account_info(tx_metadata["AffectedPublicKeys"][0]["PublicKeyBase58Check"])['Profile']['Username']
    except(Exception):
        auth = "NO_USERNAME"
        
    #Analyse the output
    tx_fee = tx_metadata['BasicTransferTxindexMetadata']['FeeNanos'] / 10**9

    print("############################################## [ DERIVAT_KEY ] ###############################################\n")
    
    print("TRANSACTION ID {} : Input -> {:.10f} [$DESO]" \
        "\n -> {} authorized a Derivated Key" \
        "\n Fee paid {:.10f} [$DESO]\n".format(tx_id,tx_input_nanos,auth,tx_fee))
    
    print("----------------------------------------------------------------------------------------------------------------\n")
    
if __name__ == '__main__':
    
    engine = create_engine('postgresql://chilledpanda:chilledpanda@localhost:5432/deso_blockchain')
    
    Session = sessionmaker(bind=engine)

    session = Session()
    
    blocks = session.query(Block).all()
     
    for tx in session.query(Transaction).filter_by(block_hash="00000000003e997ad827fbd44c040e7cbeddf8c5014a2128064a5879a0282196").all():
        semantic_analysis(tx)
    
