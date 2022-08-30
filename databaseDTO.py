import json
import sys

from sqlalchemy import create_engine, Column, String, Integer, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy import MetaData

# Global vars
engine = create_engine('postgresql://chilledpanda:chilledpanda@localhost:5432/deso_blockchain')
metadata_obj = None
session = None
tx_infos = ['TransactionIDBase58Check', 'RawTransactionHex','Input', 'Outputs', 'TransactionType', 'BlockHashHex', 'TransactionMetadata']

Base = declarative_base()


class Block(Base):
    __tablename__ = 'block'

    block_hash = Column(String, primary_key=True)
    version = Column(Integer)
    tx_number = Column(Integer)
    prev_block_hash = Column(String)
    timestamp = Column(Integer)
    block_height = Column(Integer)
    tx_merkle_root = Column(String)
    block_nonce = Column(String)
    extra_nonce = Column(String)

    def __init__(self, b_hash, version, tx_number, prev_hash, timestamp, b_height, tx_merkle_root, b_nonce, extra_nonce):
        self.block_hash = b_hash
        self.version = version
        self.tx_number = tx_number
        self.prev_block_hash = prev_hash
        self.timestamp = timestamp
        self.block_height = b_height
        self.tx_merkle_root = tx_merkle_root
        self.block_nonce = b_nonce
        self.extra_nonce = extra_nonce

    def __str__(self):
        return ' BlockHash: {self.block_hash}\n Version: {self.version}\n PrevBlockHash: {self.prev_block_hash}\n TimeStamp: {self.timestamp}\n BlockHeight: {self.block_height}\n TxMerkleRoot: {self.tx_merkle_root}\n BlockNonce: {self.block_nonce}\n ExtraNonce: {self.extra_nonce}\n'.format(self=self)


class Transaction(Base):
    __tablename__ = 'transaction'

    tx_id_base58 = Column(String, primary_key=True)
    tx_raw_hex = Column(String)
    inputs = Column(String)
    outputs = Column(String)
    signature_hex = Column(String)
    tx_metadata = Column(String)
    tx_type = Column(String)
    tx_transactor_base58 = Column(String)
    block_hash = Column(String, ForeignKey('block.block_hash'))

    def __init__(self, block_hash, type, transactor, id_base58, raw_hex, inputs, outputs, sign_hex, metadata):
        self.block_hash = block_hash
        self.tx_type = type
        self.tx_id_base58 = id_base58
        self.tx_transactor_base58 = transactor
        self.tx_raw_hex = raw_hex
        self.inputs = inputs
        self.outputs = outputs
        self.signature_hex = sign_hex
        self.tx_metadata = metadata
    
    def __str__(self):
        return ' BlockHash: {self.block_hash}\n Type: {self.tx_type}\n TxIdBase58: {self.tx_id_base58}\n Transactor: {self.tx_transactor_base58}\n TxRawHex: {self.tx_raw_hex}\n Inputs: {self.inputs}\n Outputs: {self.outputs}\n SignatureHex: {self.signature_hex}\n TransactionMetadata: {self.tx_metadata}\n'.format(self=self)

#UTILITY FUNCTIONS

def block_is_in_db(b_hash):
    global session
    block_check = session.query(Block).filter_by(block_hash=b_hash).first()
    return block_check is not None

def tx_is_in_db(tx_hash):
    global session
    block_check = session.query(Transaction).filter_by(tx_id_base58=tx_hash).first()
    return block_check is not None

#-----------------------------------

def bootstrap_db():
    global session
    global metadata

    # Establishing DB connection
    engine = create_engine(
        'postgresql://zicco:chilledpanda@localhost:5432/deso_blockchain')
    Session = sessionmaker(bind=engine)
    session = Session()
    metadata = MetaData(bind=engine)

    if(not inspect(engine).has_table("block")):
        Block.__table__.create(engine)
                    
    if(not inspect(engine).has_table("transaction")):
        Transaction.__table__.create(engine)

    # Running options
    for arg in sys.argv:
        if (arg[0] == '-'):
            for op in arg[1:]:
                match op:
                    case 'n':  # Recreate database
                        for tbl in reversed(metadata.sorted_tables):
                            engine.execute(tbl.delete())
                        
                        if(not inspect(engine).has_table("block")):
                            Block.__table__.create(engine)
                    
                        if(not inspect(engine).has_table("transaction")):
                            Transaction.__table__.create(engine)
    
                        


def clean_insert(block_data): # The block is not in the DB  -> all transactions should be insered
    header = block_data['Header']

    # Constructing block obj
    block = Block(b_hash=header['BlockHashHex'], version=header['Version'],
                  tx_number=len(block_data["Transactions"]), prev_hash=header['PrevBlockHashHex'],
                  timestamp=header['TstampSecs'], b_height=header['Height'],
                  tx_merkle_root=header['TransactionMerkleRootHex'], b_nonce=str(
                      header['Nonce']),
                  extra_nonce=str(header['ExtraNonce']))
    try:
        #Insert block into DB
        session.add(block)
        session.commit()
    except Exception as e:
        session.rollback()
        print(e)
        exit(-1)

    for tx in block_data["Transactions"]:
        # Some info could be null or not defined -> if key does not exits then the value must be None
        info = {}
        for key_info in tx_infos:
            try:
                info[key_info] = tx[key_info]
            except (KeyError):
                info[key_info] = None
        
        m = info['TransactionMetadata']

        transaction = Transaction(header['BlockHashHex'], m["TxnType"], m["TransactorPublicKeyBase58Check"],
                    info['TransactionIDBase58Check'], info['RawTransactionHex'], 
                    json.dumps(info['Inputs']), json.dumps('Outputs'), info['SignatureHex'],
                    info['TransactionMetadata'])

        #Insert transation into DB
        try:
            session.add(transaction)
            session.commit()
        except Exception as e:
            session.rollback()
            print(e)
            exit(-1)
    

def dirty_insert(block_data): #Block is already in the DB but transaction may miss, check which misses and add
    header = block_data['Header']

    for tx in block_data["Transactions"]:
        if(not tx_is_in_db(tx['TransactionIDBase58Check'])):
            info = {}
            print("\n\n\n\n l")
            print(tx.keys())
            print("\n\n\n\n l")

            print(tx["Input"])

            for key_info in tx_infos:
                try:
                    info[key_info] = tx[key_info]
                    print("{} - {}".format(key_info,info[key_info]))
                except (KeyError):
                    info[key_info] = None

            m = info['TransactionMetadata']

            transaction = Transaction(header['BlockHashHex'], m["TxnType"], m["TransactorPublicKeyBase58Check"],
                        info['TransactionIDBase58Check'], info['RawTransactionHex'], 
                        json.dumps(info['Inputs']), json.dumps('Outputs'), info['SignatureHex'],
                        info['TransactionMetadata'])
            
            print(transaction)

            """ {'BlockHashHex': '00000000000078a7f1a68c8bf056a7f17cad16bc1c9d379bea381972366300f8', 'TxnIndexInBlock': 0, 'TxnType': 'BLOCK_REWARD', 'TransactorPublicKeyBase58Check': '8mkU8yaVLs', 'AffectedPublicKeys': [{'PublicKeyBase58Check': 'BC1YLgANZLxhAKqPLAKt3P9ye1FVw6Lfa3gd4U4kYvEFTnJZauuPKg2', 'Metadata': 'BasicTransferOutput'}], 'TxnOutputs': [{'PublicKey': 'AkC3VAxaDXOUuDFtBoAtQwUyL5f1gmDTcQy6Zt7JMNgb', 'AmountNanos': 100120772}], 'BasicTransferTxindexMetadata': {'TotalInputNanos': 0, 'TotalOutputNanos': 100120772, 'FeeNanos': 0, 'UtxoOpsDump': '', 'UtxoOps': None, 'DiamondLevel': 0, 'PostHashHex': ''}}

            """

            #Insert transation into DB
            try:
                session.add(transaction)
                session.commit()
            except Exception as e:
                session.rollback()
                print(e)
                exit(-1)