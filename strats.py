import backtrader as bt

import sys
import os
##Indicators 

from backtrader.indicators import Indicator, MovAv, RelativeStrengthIndex, Highest, Lowest
class StochasticRSI(Indicator):
      """
      K - The time period to be used in calculating the %K. 3 is the default.
      D - The time period to be used in calculating the %D. 3 is the default.
      RSI Length - The time period to be used in calculating the RSI
      Stochastic Length - The time period to be used in calculating the Stochastic
  
      Formula:
      %K = SMA(100 * (RSI(n) - RSI Lowest Low(n)) / (RSI HighestHigh(n) - RSI LowestLow(n)), smoothK)
      %D = SMA(%K, periodD)
  
      """
      lines = ('fastk', 'fastd',)
  
      params = (
          ('k_period', 3),
          ('d_period', 3),
          ('rsi_period', 14),
          ('stoch_period', 14),
          ('movav', MovAv.Simple),
          ('rsi', RelativeStrengthIndex),
          ('upperband', 80.0),
          ('lowerband', 20.0),
      )
  
      plotlines = dict(percD=dict(_name='%D', ls='--'),
                       percK=dict(_name='%K'))
  
      def _plotlabel(self):
          plabels = [self.p.k_period, self.p.d_period, self.p.rsi_period, self.p.stoch_period]
          plabels += [self.p.movav] * self.p.notdefault('movav')
          return plabels
  
      def _plotinit(self):
          self.plotinfo.plotyhlines = [self.p.upperband, self.p.lowerband]
  
      def __init__(self):
          rsi_hh = Highest(self.p.rsi(period=self.p.rsi_period), period=self.p.stoch_period)
          rsi_ll = Lowest(self.p.rsi(period=self.p.rsi_period), period=self.p.stoch_period)
          knum = self.p.rsi(period=self.p.rsi_period) - rsi_ll
          kden = rsi_hh - rsi_ll
  
          self.k = self.p.movav(100.0 * (knum / kden), period=self.p.k_period)
          self.d = self.p.movav(self.k, period=self.p.d_period)
  
          self.lines.fastk = self.k
          self.lines.fastd = self.d

## Strats

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

        self.ema200 = bt.indicators.EMA(self.datas[0],period=self.params.params['ema_period']) 
        temp = bt.indicators.STOCHRSI(self.datas[0], period=self.params.params['short_period'], fastk_period=3, fastd_period=3, fastd_matype=0)
        self.short_k = (temp.fastk)
        self.short_d = (temp.fastd)
        temp = bt.indicators.STOCHRSI(self.datas[0], period=self.params.params['long_period'], fastk_period=3, fastd_period=3, fastd_matype=0)
        self.long_k = (temp.fastk)
        self.long_d = (temp.fastd)
                
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
        
        # if(self.pos == "long"):
        #   stop_price = order.executed.price * (1.0 - 0.1)
        #   self.sell(exectype=bt.Order.Stop, price=stop_price, size=self.amount)
        # if(self.pos == "short"):
        #   stop_price = order.executed.price * (1.0 + 0.1)
        #   self.buy(exectype=bt.Order.Stop, price=stop_price, size=self.amount)

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
                self.pos ="none"
            if self.short_crossover > 0 and  self.short_k < 20 and self.short_d < 20 and self.pos == 'short':
                self.order = self.buy(size=self.amount)
                self.pos ="none"

class CustomStochRSIStrategy(bt.Strategy):
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

        self.ema = bt.indicators.EMA(self.datas[0],period=self.params.params['ema_period'])

        self.rsi_long = bt.indicators.RSI(self.datas[0],period=self.params.params['long_period'])
 
        self.rsi_short = bt.indicators.RSI(self.datas[0],period=self.params.params['short_period'])


        highest = bt.ind.Highest(self.rsi_long, period=self.params.params['long_period'])
        lowest = bt.ind.Lowest(self.rsi_long, period=self.params.params['long_period'])
        kraw = 100.0 * (self.rsi_long - lowest) / (highest - lowest)
        self.k_long  = bt.ind.SMA(kraw, period=3)

        highest = bt.ind.Highest(self.rsi_long, period=self.params.params['short_period'])
        lowest = bt.ind.Lowest(self.rsi_long, period=self.params.params['short_period'])
        kraw = 100.0 * (self.rsi_long - lowest) / (highest - lowest)
        self.k_short  = bt.ind.SMA(kraw, period=3)

        #self.k_long = bt.indicators.SMA(bt.indicators.Stochastic(self.rsi_long,self.rsi_long,self.rsi_long,period=self.params.params['long_period']),period=3)
        #self.k_short = bt.indicators.SMA(bt.indicators.Stochastic(self.rsi_short,self.rsi_short,self.rsi_short,period=self.params.params['short_period']),period=3)


        self.d_long = bt.indicators.SimpleMovingAverage(self.k_long,period=3)
        self.d_short = bt.indicators.SimpleMovingAverage(self.k_short,period=3)


        self.long_crossover = bt.ind.CrossOver(self.k_long,self.d_long)
        self.short_crossover = bt.ind.CrossOver(self.k_short,self.d_short)


                
        



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

            if self.long_crossover > 0 and self.k_long <20 and self.d_long < 20 and self.datas[0].close[0] > self.ema[0]:
                # Keep track of the created order to avoid a 2nd order
                self.amount = (self.broker.getvalue() * self.params.quantity) / self.dataclose[0]
                self.order = self.buy(size=self.amount)
                self.pos = "long"

            if self.short_crossover < 0 and   self.k_short > 75 and self.d_short > 75 and self.datas[0].close[0] < self.ema[0]:
                # Keep track of the created order to avoid a 2nd order
                self.amount = (self.broker.getvalue() * self.params.quantity) / self.dataclose[0]
                self.order = self.sell(size=self.amount)
                self.pos = "short"
                
        else:
            if self.long_crossover < 0 and  self.k_long > 60 and self.d_long > 60 and self.pos == 'long':
                self.order = self.sell(size=self.amount)
            if self.short_crossover > 0 and  self.k_short < 20 and self.d_short < 20 and self.pos == 'short':
                self.order = self.buy(size=self.amount)


class StochRSIStrategy2(bt.Strategy):

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

        self.ema = bt.indicators.EMA(self.datas[0],period=self.params.params['ema_period'])

        self.rsi_long = bt.indicators.RSI(self.datas[0],period=self.params.params['long_period'])
 
        self.rsi_short = bt.indicators.RSI(self.datas[0],period=self.params.params['short_period'])


        highest = bt.ind.Highest(self.rsi_long, period=self.params.params['long_period'])
        lowest = bt.ind.Lowest(self.rsi_long, period=self.params.params['long_period'])
        kraw = 100.0 * (self.rsi_long - lowest) / (highest - lowest)
        self.k_long  = bt.ind.SMA(kraw, period=3)

        highest = bt.ind.Highest(self.rsi_long, period=self.params.params['short_period'])
        lowest = bt.ind.Lowest(self.rsi_long, period=self.params.params['short_period'])
        kraw = 100.0 * (self.rsi_long - lowest) / (highest - lowest)
        self.k_short  = bt.ind.SMA(kraw, period=3)

        #self.k_long = bt.indicators.SMA(bt.indicators.Stochastic(self.rsi_long,self.rsi_long,self.rsi_long,period=self.params.params['long_period']),period=3)
        #self.k_short = bt.indicators.SMA(bt.indicators.Stochastic(self.rsi_short,self.rsi_short,self.rsi_short,period=self.params.params['short_period']),period=3)


        self.d_long = bt.indicators.SimpleMovingAverage(self.k_long,period=3)
        self.d_short = bt.indicators.SimpleMovingAverage(self.k_short,period=3)


        self.long_crossover = bt.ind.CrossOver(self.k_long,self.d_long)
        self.short_crossover = bt.ind.CrossOver(self.k_short,self.d_short)


                
        



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

            if self.long_crossover > 0 and self.k_long <20 and self.d_long < 20 and self.datas[0].close[0] > self.ema[0]:
                # Keep track of the created order to avoid a 2nd order
                self.amount = (self.broker.getvalue() * self.params.quantity) / self.dataclose[0]
                self.order = self.buy(size=self.amount)
                self.pos = "long"

            if self.short_crossover < 0 and   self.k_short > 75 and self.d_short > 75 and self.datas[0].close[0] < self.ema[0]:
                # Keep track of the created order to avoid a 2nd order
                self.amount = (self.broker.getvalue() * self.params.quantity) / self.dataclose[0]
                self.order = self.sell(size=self.amount)
                self.pos = "short"
                
        else:
            if self.long_crossover < 0 and  self.k_long > 60 and self.d_long > 60 and self.pos == 'long':
                self.order = self.sell(size=self.amount)
            if self.short_crossover > 0 and  self.k_short < 20 and self.d_short < 20 and self.pos == 'short':
                self.order = self.buy(size=self.amount)


class CipherBv2(bt.Strategy):

    params = (
        ('params', dict()),
        ('quantity', None)
    )


    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datahlc3 = (self.dataclose + self.datahigh + self.datalow)/3

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.amount = None

        # df['hlc3'] = (df['Close']+df['High']+df['Low'])/3
        # esa = talib.EMA(df['hlc3'],timeperiod=chlen)
        # de = talib.EMA((df['hlc3']-esa).abs(),chlen)
        # ci = (df['hlc3'] - esa) / (0.015 * de)
        # wt1 = talib.EMA(ci,avg)
        # wt2 = talib.SMA(wt1,malen)
        # prev_wt1 = wt1.shift(1)
        # prev_wt2 = wt2.shift(1)
        # wtCross = (((wt1 <= wt2) & (prev_wt1 >= prev_wt2))
        #             | ((wt1 >= wt2) & (prev_wt1 <= prev_wt2)))
        # wtCrossUp = wt2 - wt1 <= 0
        # wtCrossDown = wt2 - wt1 >= 0
        # wtOversold = wt2 <= 53
        # wtOverbought = wt2 >= -53
        # buySignal = wtCross & wtCrossUp & wtOversold
        # sellSignal = wtCross & wtCrossDown & wtOverbought
        self.ema = bt.indicators.EMA(self.datas[0],period=self.params.params['ema_period'])
        esa = bt.indicators.EMA(self.datahlc3,period=self.params.params['chlen'])
        de = bt.indicators.EMA(abs(self.datahlc3-esa),period=self.params.params['chlen'])
        ci = (self.datahlc3 - esa) / (0.015 * de)
        wt1 = bt.indicators.EMA(ci,period=self.params.params['avg'])
        wt2 = bt.indicators.SimpleMovingAverage(wt1,period=self.params.params['malen'])
        self.wtOversold = wt2 <= 53
        self.wtOverbought = wt2 >= -53
        self.cross = bt.ind.CrossOver(wt1,wt2)

        # short_esa = bt.indicators.EMA(self.datahlc3,period=self.params.params['chlen'])
        # short_de = bt.indicators.EMA(abs(self.datahlc3 - short_esa),period=self.params.params['chlen'])
        # short_ci = (self.datahlc3 - short_esa) / (0.015 * short_de)
        # short_wt1 = bt.indicators.EMA(short_ci,period=self.params.params['avg'])
        # short_wt2 = bt.indicators.SimpleMovingAverage(short_wt1,period=self.params.params['malen'])
        # self.short_wtOversold = short_wt2 <= 53
        # self.short_wtOverbought = short_wt2 >= -53
        # self.short_cross = bt.ind.CrossOver(short_wt1,short_wt2)


                
        



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

            if self.cross > 0 and self.wtOversold and self.datas[0].close[0] > self.ema[0]:
                # Keep track of the created order to avoid a 2nd order
                self.amount = (self.broker.getvalue() * self.params.quantity) / self.dataclose[0]
                self.order = self.buy(size=self.amount)
                self.pos = "long"

            if self.cross < 0 and   self.wtOverbought and self.datas[0].close[0] < self.ema[0]:
                # Keep track of the created order to avoid a 2nd order
                self.amount = (self.broker.getvalue() * self.params.quantity) / self.dataclose[0]
                self.order = self.sell(size=self.amount)
                self.pos = "short"
                
        else:
            if self.cross < 0 and  self.wtOverbought and self.pos == 'long':
                self.order = self.sell(size=self.amount)
            if self.cross > 0 and  self.wtOversold and self.pos == 'short':
                self.order = self.buy(size=self.amount)


import backtrader as bt
class CipherBv2Long(bt.Strategy):

    params = (
        ('params', dict()),
        ('quantity', None)
    )


    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datahlc3 = (self.dataclose + self.datahigh + self.datalow)/3

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.amount = None

        # df['hlc3'] = (df['Close']+df['High']+df['Low'])/3
        # esa = talib.EMA(df['hlc3'],timeperiod=chlen)
        # de = talib.EMA((df['hlc3']-esa).abs(),chlen)
        # ci = (df['hlc3'] - esa) / (0.015 * de)
        # wt1 = talib.EMA(ci,avg)
        # wt2 = talib.SMA(wt1,malen)
        # prev_wt1 = wt1.shift(1)
        # prev_wt2 = wt2.shift(1)
        # wtCross = (((wt1 <= wt2) & (prev_wt1 >= prev_wt2))
        #             | ((wt1 >= wt2) & (prev_wt1 <= prev_wt2)))
        # wtCrossUp = wt2 - wt1 <= 0
        # wtCrossDown = wt2 - wt1 >= 0
        # wtOversold = wt2 <= 53
        # wtOverbought = wt2 >= -53
        # buySignal = wtCross & wtCrossUp & wtOversold
        # sellSignal = wtCross & wtCrossDown & wtOverbought
        self.ema = bt.indicators.EMA(self.datas[0],period=self.params.params['ema_period'])
        esa = bt.indicators.EMA(self.datahlc3,period=self.params.params['chlen'])
        de = bt.indicators.EMA(abs(self.datahlc3-esa),period=self.params.params['chlen'])
        ci = (self.datahlc3 - esa) / (0.015 * de)
        wt1 = bt.indicators.EMA(ci,period=self.params.params['avg'])
        wt2 = bt.indicators.SimpleMovingAverage(wt1,period=self.params.params['malen'])
        self.wtOversold = wt2 <= 53
        self.wtOverbought = wt2 >= -53
        self.cross = bt.ind.CrossOver(wt1,wt2)

        # short_esa = bt.indicators.EMA(self.datahlc3,period=self.params.params['chlen'])
        # short_de = bt.indicators.EMA(abs(self.datahlc3 - short_esa),period=self.params.params['chlen'])
        # short_ci = (self.datahlc3 - short_esa) / (0.015 * short_de)
        # short_wt1 = bt.indicators.EMA(short_ci,period=self.params.params['avg'])
        # short_wt2 = bt.indicators.SimpleMovingAverage(short_wt1,period=self.params.params['malen'])
        # self.short_wtOversold = short_wt2 <= 53
        # self.short_wtOverbought = short_wt2 >= -53
        # self.short_cross = bt.ind.CrossOver(short_wt1,short_wt2)


                
        



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

            if self.cross > 0 and self.wtOversold and self.datas[0].close[0] > self.ema[0]:
                # Keep track of the created order to avoid a 2nd order
                self.amount = (self.broker.getvalue() * self.params.quantity) / self.dataclose[0]
                self.order = self.buy(size=self.amount)
                self.pos = "long"

                
        else:
            if self.cross < 0 and  self.wtOverbought and self.pos == 'long':
                self.order = self.sell(size=self.amount)



class ScalpingStrat1(bt.Strategy):

    params = (
        ('params', dict()),
        ('quantity', None)
    )


    def __init__(self):

        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.amount = None

        self.ema20 = bt.indicators.EMA(self.datas[0],period=20)
        self.ema50 = bt.indicators.EMA(self.datas[0],period=50)
        self.ema100 = bt.indicators.EMA(self.datas[0],period=100)

    

        
                
        



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
        try:

            n=2

            upflagDownFrontier = True
            upflagUpFrontier0 = True
            upflagUpFrontier1 = True
            upflagUpFrontier2 = True
            upflagUpFrontier3 = True
            upflagUpFrontier4 = True

            for i in range(1,n+1):
                if(self.datas[0].low[n+1] and self.datas[0].low[n+2] and self.datas[0].low[n+3] and self.datas[0].low[n+4]):
                    upflagDownFrontier = upflagDownFrontier and (self.datas[0].high[n-i] < self.datas[0].high[n])
                    upflagUpFrontier0 = upflagUpFrontier0 and (self.datas[0].high[n+i] < self.datas[0].high[n])
                    upflagUpFrontier1 = upflagUpFrontier1 and (self.datas[0].high[n+1] <= self.datas[0].high[n] and self.datas[0].high[n+i + 1] < self.datas[0].high[n])
                    upflagUpFrontier2 = upflagUpFrontier2 and (self.datas[0].high[n+1] <= self.datas[0].high[n] and self.datas[0].high[n+2] <= self.datas[0].high[n] and self.datas[0].high[n+i + 2] < self.datas[0].high[n])
                    upflagUpFrontier3 = upflagUpFrontier3 and (self.datas[0].high[n+1] <= self.datas[0].high[n] and self.datas[0].high[n+2] <= self.datas[0].high[n] and self.datas[0].high[n+3] <= self.datas[0].high[n] and self.datas[0].high[n+i + 3] < self.datas[0].high[n])
                    upflagUpFrontier4 = upflagUpFrontier4 and (self.datas[0].high[n+1] <= self.datas[0].high[n] and self.datas[0].high[n+2] <= self.datas[0].high[n] and self.datas[0].high[n+3] <= self.datas[0].high[n] and self.datas[0].high[n+4] <= self.datas[0].high[n] and self.datas[0].high[n+i + 4] < self.datas[0].high[n])
            flagUpFrontier = upflagUpFrontier0 or upflagUpFrontier1 or upflagUpFrontier2 or upflagUpFrontier3 or upflagUpFrontier4

            upFractal = (upflagDownFrontier and flagUpFrontier)

            # downFractal in python

            downflagDownFrontier = True
            downflagUpFrontier0 = True
            downflagUpFrontier1 = True
            downflagUpFrontier2 = True
            downflagUpFrontier3 = True
            downflagUpFrontier4 = True

            for i in range(1,n+1):
                if(self.datas[0].low[n+1] and self.datas[0].low[n+2] and self.datas[0].low[n+3] and self.datas[0].low[n+4]):
                    downflagDownFrontier = downflagDownFrontier and (self.datas[0].low[n-i] > self.datas[0].low[n])
                    downflagUpFrontier0 = downflagUpFrontier0 and (self.datas[0].low[n+i] > self.datas[0].low[n])
                    downflagUpFrontier1 = downflagUpFrontier1 and (self.datas[0].low[n+1] >= self.datas[0].low[n] and self.datas[0].low[n+i + 1] > self.datas[0].low[n])
                    downflagUpFrontier2 = downflagUpFrontier2 and (self.datas[0].low[n+1] >= self.datas[0].low[n] and self.datas[0].low[n+2] >= self.datas[0].low[n] and self.datas[0].low[n+i + 2] > self.datas[0].low[n])
                    downflagUpFrontier3 = downflagUpFrontier3 and (self.datas[0].low[n+1] >= self.datas[0].low[n] and self.datas[0].low[n+2] >= self.datas[0].low[n] and self.datas[0].low[n+3] >= self.datas[0].low[n] and self.datas[0].low[n+i + 3] > self.datas[0].low[n])
                    downflagUpFrontier4 = downflagUpFrontier4 and (self.datas[0].low[n+1] >= self.datas[0].low[n] and self.datas[0].low[n+2] >= self.datas[0].low[n] and self.datas[0].low[n+3] >= self.datas[0].low[n] and self.datas[0].low[n+4] >= self.datas[0].low[n] and self.datas[0].low[n+i + 4] > self.datas[0].low[n])

            flagDownFrontier = downflagUpFrontier0 or downflagUpFrontier1 or downflagUpFrontier2 or downflagUpFrontier3 or downflagUpFrontier4

            downFractal = (downflagDownFrontier and flagDownFrontier)


            if not self.position:

                if self.datas[0].close[0] < self.ema20[0] and self.datas[0].close[0] > self.ema20[0]  and (self.ema20[0] > self.ema50[0] and self.ema50[0] > self.ema100[0]) :
                    self.buy_bracket(
                        limitprice=self.datas[0].close[0] + 1*(self.datas[0].close[0] - self.ema50[0]), price=self.datas[0].close[0], stopprice=self.ema50[0]
                    )
                    self.pos = "long"

                if self.datas[0].close[0] < self.ema50[0] and self.datas[0].close[0] > self.ema100[0]  and (self.ema20[0] > self.ema50[0] and self.ema50[0] > self.ema100[0]) :
                    self.buy_bracket(
                        limitprice=self.datas[0].close[0] + 1*(self.datas[0].close[0] - self.ema100[0]), price=self.datas[0].close[0], stopprice=self.ema100[0]
                    )
                    self.pos = "long"

                if self.datas[0].close[0] > self.ema20[0] and self.datas[0].close[0] < self.ema50[0]  and (self.ema20[0] < self.ema50[0] and self.ema50[0] < self.ema100[0]) :
                    self.sell_bracket(
                        limitprice=self.datas[0].close[0] - 1*(self.ema50[0] - self.datas[0].close[0]), price=self.datas[0].close[0], stopprice=self.ema50[0]
                    )
                    self.pos = "short"

                if self.datas[0].close[0] > self.ema50[0] and self.datas[0].close[0] < self.ema100[0] and (self.ema20[0] < self.ema50[0] and self.ema50[0] < self.ema100[0]) :
                    self.sell_bracket(
                        limitprice=self.datas[0].close[0] - 1*(self.ema100[0] - self.datas[0].close[0]), price=self.datas[0].close[0], stopprice=self.ema100[0]
                    )
                    self.pos = "short"
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
