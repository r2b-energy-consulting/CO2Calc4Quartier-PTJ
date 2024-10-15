import pandas as pd
import numpy as np

from config import *

all_tech_parameters = pd.read_excel(f'{inputs_folder}/technische_parameter.xlsx') # alle vorberechneten technischen Parameter
co2_price = pd.read_excel(f'{inputs_folder}/technische_annahmen.xlsx', sheet_name='CO2_Prices',index_col=[0]).to_dict()['CO2_Price']

all_input_data = dict()
for year in years: 
    df = pd.read_excel(f'{inputs_folder}/technische_annahmen.xlsx', sheet_name=str(year), index_col=[0]).drop('Wirkungsgrad[MWhel/MWhth]',axis=1) # alle Kosten und Emissionsintensitäten
    df.loc['Wind'] = df.loc['WindOffshore'] + df.loc['WindOnshore']
    df = df.drop(['WindOffshore','WindOnshore'],axis=0)
    all_input_data[year] = df
    
