import backtrader as bt

class StochRSIStrategy(bt.Strategy):

    params = (
        ('params', dict()),
        ('quantity', None)
    )


    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.amount = None

        self.ema200 = bt.talib.EMA(self.datas[0],timeperiod=self.params.params['ema_period']) 
        self.short_k = (bt.talib.STOCHRSI(self.datas[0], timeperiod=self.params.params['short_period'], fastk_period=3, fastd_period=3, fastd_matype=0).fastk)
        self.short_d = (bt.talib.STOCHRSI(self.datas[0], timeperiod=self.params.params['short_period'], fastk_period=3, fastd_period=3, fastd_matype=0).fastd)

        self.long_k = (bt.talib.STOCHRSI(self.datas[0], timeperiod=self.params.params['long_period'], fastk_period=3, fastd_period=3, fastd_matype=0).fastk)
        self.long_d = (bt.talib.STOCHRSI(self.datas[0], timeperiod=self.params.params['long_period'], fastk_period=3, fastd_period=3, fastd_matype=0).fastd)
                
        
        self.long_crossover = bt.ind.CrossOver(self.long_k,self.long_d)
        self.short_crossover = bt.ind.CrossOver(self.short_k,self.short_d)



    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm

        self.order = None


    def next(self):

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.long_crossover > 0 and   self.long_k < 20 and self.long_d < 20 and self.dataclose > self.ema200:
                # Keep track of the created order to avoid a 2nd order
                self.amount = (self.broker.getvalue() * self.params.quantity) / self.dataclose[0]
                self.order = self.buy(size=self.amount)
                self.pos = "long"

            if self.short_crossover < 0 and   self.short_k > 75 and self.short_d > 75 and self.dataclose < self.ema200:
                # Keep track of the created order to avoid a 2nd order
                self.amount = (self.broker.getvalue() * self.params.quantity) / self.dataclose[0]
                self.order = self.sell(size=self.amount)
                self.pos = "short"
                
        else:
            if self.long_crossover < 0 and  self.long_k > 60 and self.long_d > 60 and self.pos == 'long':
                self.order = self.sell(size=self.amount)
            if self.short_crossover > 0 and  self.short_k < 20 and self.short_d < 20 and self.pos == 'short':
                self.order = self.buy(size=self.amount)
