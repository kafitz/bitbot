import abc


class Observer(object):
    __metaclass__ = abc.ABCMeta

    def begin_opportunity_finder(self, depths):
        pass

    def end_opportunity_finder(self, bitbot, deals):
        pass

    ## abstract
    @abc.abstractmethod
    def opportunity(self, profit, volume, buyprice, kask, sellprice, kbid, perc, weighted_buyprice, weighted_sellprice, available_volume, purchase_cap):
        pass
