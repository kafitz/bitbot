import logging
from observer import Observer


class Logger(Observer):
    def opportunity(self, profit, purchase_volume, buyprice, kask, sellprice, kbid, perc, weighted_buyprice, weighted_sellprice, available_volume, purchase_cap):
    	buy_total = purchase_volume * weighted_buyprice
        logging.info("profit: $%.4f USD. %4f BTC/$%.2f [%.1f BTC]: buy $%.4f (%s), sell $%.4f (%s). ~%.2f%%" %
            (profit, purchase_volume, buy_total, available_volume, weighted_buyprice, kask, weighted_sellprice, kbid, perc))
