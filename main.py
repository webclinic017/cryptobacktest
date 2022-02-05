import backtest 
import os
from strats import StochRSIStrategy
import itertools
from tqdm import tqdm
import threading


commission_val = 0.04 
portofolio = 10000.0 
stake_val = 1
quantity = 0.10 

start = '2021-8-01'
end = '2022-01-31'
strategies = [{
    "name":"StochRSI",
    "value":StochRSIStrategy,
    "params":{
        "short_period":[13,14,15,20,21,22],
        "long_period":[13,14,15,20,21,22],
        "ema_period":range(50,200,50),
    }
}]
plot = False

#global results
results = []

def run_backtest(strategy,data):
    datapath = './data/' + data
    pair = data[:-4].split("-")[0]
    start_year = data[:-4].split("-")[1]
    end_year = data[:-4].split("-")[2]
    timeframe = data[:-4].split("-")[3]

    print(f"Running backtest for {pair} {start_year}-{end_year} {timeframe}")
    for combination in tqdm(itertools.product(*strategy["params"].values())):
        paramCounnter = {}
        for index, param in enumerate(strategy["params"]):
            paramCounnter[param] = combination[index]
        end_val, totalwin, totalloss, pnl_net, sqn, sharpe, drawdown = backtest.runbacktest(
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

def write_results(results):
    results = sorted(results, key=lambda k: k['sqn'], reverse=True)


    #wite results to csv file
    import csv
    with open('results.csv', 'w') as csvfile:
        fieldnames = ['pair', 'start_year', 'end_year', 'timeframe', 'strategy', 'params', 'totalwin', 'totalloss', 'pnl_net', 'sqn', 'end_val', 'sharpe', 'drawdown']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results[:20]:
            writer.writerow(result)
        csvfile.close()

threads = []
for strategy in strategies:
    for data in os.listdir('./data'):
        #run the backtest in a new thread 
        #t = threading.Thread(target=run_backtest, args=(strategy,data))
        #threads.append(t)
        #t.start()
        try:
            run_backtest(strategy,data)
        except Exception as e:
            print(e)
            continue
    #for t in threads:
    #    t.join()

write_results(results)
    
        

#print top 10 results based on highest sqn 

            