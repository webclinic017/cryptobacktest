import os
import itertools
from tqdm import tqdm
from strats import StochRSIStrategy, CipherBv2, CipherBv2Long, CustomStochRSIStrategy, ScalpingStrat1
from backtest import runbacktest
import sys


commission_val = 0.04 
portofolio = 100
stake_val = 1
quantity = 0.5

start = '2022-08-17'
end = '2022-09-17'
strategies = [
    #           {
    #  "name":"StochRSIStrategy",
    #  "value":CustomStochRSIStrategy,
    #  "params":{
    #      "short_period":[13,14,15,20,21,22],
    #      "long_period":[13,14,15,20,21,22],
    #      "ema_period":range(50,200,50),
    #  }
    # }
    {
        "name":"ScalpingStrat1",
        "value":ScalpingStrat1,
        "params":{
            "ema":[20]
        }
    }
    # {
    #     "name":"CipherBv2",
    #     "value":CipherBv2,
    #     "params":{
    #         "ema_period":range(50,200,50),
    #         "chlen":range(9,21,2),
    #         "avg":range(9,21,2),
    #         "malen":[3,4]
    #     }
    # },
    # {
    #     "name":"CipherBv2Long",
    #     "value":CipherBv2Long,
    #     "params":{
    #         "ema_period":range(50,200,50),
    #         "chlen":range(9,21,2),
    #         "avg":range(9,21,2),
    #         "malen":[3,4]
    #     }
    # }
 ]
plot = False

results = []

def run_backtest(strategy,data):
    datapath = './data/' + data
    pair = data[:-4].split("-")[0]
    start_year = data[:-4].split("-")[1]
    end_year = data[:-4].split("-")[2]
    timeframe = data[:-4].split("-")[3]

    print(f"Running backtest for {pair} {start_year}-{end_year} {timeframe}")
    print(itertools.product(*strategy["params"].values()))
    for combination in tqdm(itertools.product(*strategy["params"].values())):
        try:
            paramCounnter = {}
            for index, param in enumerate(strategy["params"]):
                paramCounnter[param] = combination[index]
            end_val, totalwin, totalloss, pnl_net, sqn, sharpe, drawdown = runbacktest(
                datapath, start, end, 
                paramCounnter, strategy['value'], commission_val, 
                portofolio, stake_val, quantity, plot)
            results.append({
                "pair":pair,
                "start_year":start_year,
                "end_year":end_year,
                "timeframe":timeframe,
                "strategy":strategy["name"],
                "params":paramCounnter,
                "totalwin":totalwin,
                "totalloss":totalloss,
                "pnl_net":pnl_net,
                "sqn":sqn,
                "end_val":end_val,
                "sharpe":sharpe,
                "drawdown":drawdown
            })
            write_results(results)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

def write_results(results):
    results = sorted(results, key=lambda k: k['sqn'], reverse=True)
    import csv
    with open('results.csv', 'w') as csvfile:
        fieldnames = ['pair', 'start_year', 'end_year', 'timeframe', 'strategy', 'params', 'totalwin', 'totalloss', 'pnl_net', 'sqn', 'end_val', 'sharpe', 'drawdown']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results[:50]:
            writer.writerow(result)
        csvfile.close()

threads = []
for strategy in strategies:
    for data in os.listdir('./data'):
        try:
            run_backtest(strategy,data)
        except Exception as e:
            print(e)
            continue