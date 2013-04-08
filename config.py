##### Arbitrage output
arbitrage_output = "#merlin-test"
deal_output = "#botbottest"

# watch the following markets
# markets = ["bitfloorUSD", "MtGoxUSD", "BtceUSD", "BitstampUSD", "CampBXUSD", "Bitcoin24USD", "VircurexUSD"]
markets = ["BitfloorUSD", "MtGoxUSD", "BitstampUSD", "CampBXUSD"]
# private_markets = {"bflr": "Bitfloor", "mtgx": "MtGox", "bstp": "Bitstamp", "bctl": "BitcoinCentral"}
private_markets = {"bstp": "Bitstamp", "mtgx": "MtGox", "bflr": "Bitfloor"}

# buy_markets = {"bflr": "Bitfloor", "btce": "BTCe", "bc24": "Bitcoin24"}
# sell_markets = {"bstp": "Bitstamp", "mtgx": "MtGox"}

# observers if any
# ["Logger", "TraderBot", "TraderBotSim", "HistoryDumper", "Emailer", "Database"]
observers = ["Logger", "Database"]


#### Trader Bot Config
# Access to Private APIs
mtgox_key = "a224882a-5884-402a-af08-dd58bc59f1a0"
mtgox_secret = "JO4j70yJhttMjypG8A/TeqkdtMV/aC+37c+t5mvjMy13wLU4ymFG0F52hECjEpKREAoQl4qkrdbgBGxMFIdSUg=="

bitcoincentral_username = "fitzatschool@gmail.com"
bitcoincentral_password = "wmitAY5h*3%NHvX0"

bitstamp_user = "27368"
bitstamp_password = "1TOsEZms3yaRxNoH"

bitfloor_key = "e27dcdb8-8388-4227-bfc0-ca641c3bc797"
bitfloor_secret = "puEtkb4qab/68Tx6o1wnsKuypQClg9P4a1OrjSlbjpzmn+l9/HslL2lzY1Z4SU3CMbRyuBlaDRaLeAl5b/HAug=="
bitfloor_passphrase = 'dP7Wmoa*G8WAIU2S'

btce_key = "G9N9IB1J-RKQA0K45-B1CLR6IT-4A1QQYLX-WJG9OXD5"
btce_secret = "9ae4b00b25b9d7e285dcfac11caf6924da029e858bad4b5b06c210405a3dd587"

bitcoin24_user = "crooton"
bitcoin24_key = "CXftzt6uzwYXuh5eZbRrKCJwRqGxUR37"

# SafeGuards
max_amount = 0.43  # in BTC
balance_margin = 0.00  # 0%
profit_thresh = 0.01  # in %
perc_thresh = 0.1  # in %

#### Emailer Observer Config
smtp_host = 'FIXME'
smtp_login = 'FIXME'
smtp_passwd = 'FIXME'
smtp_from = 'FIXME'
smtp_to = 'FIXME'


market_expiration_time = 120  # in seconds: 2 minutes
