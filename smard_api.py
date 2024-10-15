import sys
sys.setrecursionlimit(1500)

from datetime import datetime
import datetime as DT
from deutschland import smard
from pprint import pprint
from deutschland.smard.api import default_api
from deutschland.smard.api.default_api import DefaultApi

from deutschland.smard.apis import *
from deutschland.smard.models import *
import pandas as pd
import numpy as np

def get_start_times():
    with smard.ApiClient() as api_client:
        # Create an instance of the API class
        api_instance = default_api.DefaultApi(api_client)
        filter = 1223 
        try:
            api_response = api_instance.filter_region_index_resolution_json_get(filter, )
            return([datetime.fromtimestamp(int(i/1000)) for i in api_response['timestamps']]) 
        except smard.ApiException as e:
            print("Exception when calling DefaultApi->filter_region_index_resolution_json_get: %s\n" % e)
            return(np.nan)

def convert_timestamp(serie):
    data_time = [datetime.fromtimestamp(int(serie[i][0]/1000)) for i in range(len(serie))]
    values = [serie[i][1] for i in range(len(serie))]
    return(pd.Series(values,index=data_time))

def get_timeseries_yearly(configuration,year,data_code,region):
    weekly_start_time = get_start_times()
    resolution = 'hour' 
    dates = [date for date in weekly_start_time if date >= (datetime(year, 1, 1, 0) - DT.timedelta(days=7)) and (date <= datetime(year,12,31,0) + DT.timedelta(days=7))]
    time_series = []
    _filter = data_code 
    filter_copy = data_code 
    region_copy = region 
    for date in dates: 
        with smard.ApiClient(configuration) as api_client:
            # Create an instance of the API class
            api_instance = default_api.DefaultApi(api_client)
            timestamp = int(datetime.timestamp(date)*1000) 
            try:
                api_response = api_instance.filter_region_filter_copy_region_copy_resolution_timestamp_json_get(filter=_filter,filter_copy=filter_copy,region=region,region_copy=region_copy,resolution=resolution,timestamp=timestamp)
                serie = api_response['series']
                time_series.append(convert_timestamp(serie))
            except smard.ApiException as e:
                print("Exception when calling DefaultApi->filter_region_filter_copy_region_copy_resolution_timestamp_json_get: %s\n" % e)
    time_series = pd.concat(time_series)
    index_list = [i for i in time_series.index if i.year==year]
    return(time_series[index_list])
                
def Smard_Data(year,region):
    configuration = smard.Configuration(host = "https://www.smard.de/app/chart_data")
    data_code_dict = {4066: 'Stromerzeugung: Biomasse',
                      1226: 'Stromerzeugung: Wasserkraft',
                      1225: 'Stromerzeugung: WindOffshore', 
                      4067: 'Stromerzeugung: WindOnshore',
                      4068: 'Stromerzeugung: Photovoltaik',
                      1228: 'Stromerzeugung: SonstigeErneuerbare',
                      1224: 'Stromerzeugung: Kernenergie', 
                      1223: 'Stromerzeugung: Braunkohle',  
                      4069: 'Stromerzeugung: Steinkohle',  
                      4071: 'Stromerzeugung: Erdgas',  
                      4070: 'Stromerzeugung: Pumpspeicher',
                      1227: 'Stromerzeugung: SonstigeKonventionelle', 
                      410: 'Stromverbrauch: Gesamt(Netzlast)',
                      4359: 'Stromverbrauch: Residuallast',
                      4387: 'Stromverbrauch: Pumpspeicher'}
    region_dict = {'DE': 'Deutschland',
                   'AT': 'Österreich',
                   'LU': 'Luxemburg',
                   'DE-LU': 'Marktgebiet: DE/LU',
                   'DE-AT-LU': 'Marktgebiet: DE/AT/LU',
                   '50Hertz': 'Regelzone (DE): 50Hertz',
                   'Amprion': 'Regelzone (DE): Amprion',
                   'TenneT': 'Regelzone (DE): TenneT',
                   'TransnetBW': 'Regelzone (DE): TransnetBW',
                   'APG': 'Regelzone (AT): APG',
                   'Creos': 'Regelzone (LU): Creos'}
    
    energy_sources = [v[len('Stromerzeugung: '):] for v in data_code_dict.values() if v.find('Stromerzeugung')>-1]
    gen_time_series = dict()
    generation = pd.DataFrame(index=pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31 23:00:00', freq='h')) 
    for energietraeger in energy_sources:
        print(energietraeger)
        data_code = [k for k,v in data_code_dict.items() if v.find(energietraeger)>-1][0]
        serie = get_timeseries_yearly(configuration,year,data_code,region).reset_index()
        generation[energietraeger] = list(serie.drop(serie.index[serie.duplicated()][-2:],axis=0)[0])
    generation['Wind'] = generation['WindOffshore'] + generation['WindOnshore']
    generation = generation.drop(['WindOffshore', 'WindOnshore'],axis=1)
    
    data_code = 410 # 'Stromverbrauch: Gesamt(Netzlast)'
    serie = get_timeseries_yearly(configuration,year,data_code,region).reset_index()
    consumption = pd.Series(index=pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31 23:00:00', freq='h'), 
                            data=list(serie.drop(serie.index[serie.duplicated()][-2:],axis=0)[0]))
    return(energy_sources,generation,consumption)

