##### Arbitrage output
arbitrage_output = "#merlin-spam"

# watch the following markets
# markets = ["bitfloorUSD", "MtGoxUSD", "BtceUSD", "BitstampUSD", "CampBXUSD", "Bitcoin24USD", "VircurexUSD"]
markets = ["bitfloorUSD", "MtGoxUSD", "BitstampUSD", "CampBXUSD", "VircurexUSD"]
# private_markets = {"bflr": "Bitfloor", "mtgx": "MtGox", "bstp": "Bitstamp", "bctl": "BitcoinCentral"}
private_markets = {"bstp": "Bitstamp", "mtgx": "MtGox", "bflr": "Bitfloor"}

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

btce_key = "DLNP1XU8-72LB0C24-ICOCAKYY-U2NO627K-S6T1R8KX"
btce_secret = "863ac534d2f6a7c6de5b968ce3ee61aa5f83fd9a9ba4e184b6847f11e60704ad"

# SafeGuards
max_purchase = 150  # in USD
balance_margin = 0.05  # 5%
profit_thresh = 1  # in USD
perc_thresh = 0.1  # in %

#### Emailer Observer Config
smtp_host = 'FIXME'
smtp_login = 'FIXME'
smtp_passwd = 'FIXME'
smtp_from = 'FIXME'
smtp_to = 'FIXME'


market_expiration_time = 120  # in seconds: 2 minutes
