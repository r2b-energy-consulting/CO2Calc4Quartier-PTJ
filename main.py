import pandas as pd
import numpy as np

from config import *
from smard_api import Smard_Data
from load_data import *
from plots import *

# Laden der Stromerzeugungs- und Stromverbrauchsdaten über Smard-Api für alle Jahre
energy_sources_all, generations_all, consumption_all = dict(), dict(), dict()
for year in years:
    print('\nReading generation and consumption data from Smard for year', year)
    energy_sources_all[year], generations_all[year], consumption_all[year] = Smard_Data(year,region)

## Rechnung AEF, MEF für alle Jahre
for year in years:
    print(f'\n*************** Year {year} ***************')
    print('Reading technical parameters and inputs')
    energy_sources, generations, consumption = energy_sources_all[year].copy(), generations_all[year].copy(), consumption_all[year].copy()    
    tech_params = all_tech_parameters[all_tech_parameters.TIME_PERIOD==year].drop('TIME_PERIOD',axis=1).set_index('siec')

    input_data = all_input_data[year]
    input_data['Wirkungsgrad[MWhel/MWhth]_el'] = tech_params['Eff_el']
    input_data['Wirkungsgrad[MWhel/MWhth]_el'] = input_data['Wirkungsgrad[MWhel/MWhth]_el'].fillna(1)
    
    # Skalierungsfaktor der Stromerzeugung 
    skalieungsfaktor = {**{e: (tech_params.loc[e,'NEP']*1000)/generations[e].sum() for e in tech_params.index.drop_duplicates()}, 
                        **{e: 1 for e in generations.columns if e not in tech_params.index }}
    # KWK-Anteil der konventionellen Kraftwerke
    chp_portion = {**{e: (tech_params.loc[e,'Anteil_KWK']) for e in tech_params.index.drop_duplicates()}, 
                  **{e: 0 for e in generations.columns if e not in tech_params.index }}
               
    consumption_scale = sum(generations[e].sum()*skalieungsfaktor[e] for e in generations.columns)/generations.sum().sum()  
    
    input_data['Skalierungsfaktor'] = pd.Series(skalieungsfaktor)
    input_data['Skalierungsfaktor'] = input_data['Skalierungsfaktor'].fillna(0)
    
    input_data['Verfügbare_Leistung[MW]'] = input_data['Installierte_Leistung[MW]'] * input_data['Skalierungsfaktor'] * input_data['Verfügbarkeit'] 
    input_data.loc['Import','Verfügbare_Leistung[MW]'] = 10e6
    
    for c in generations.columns:
        generations[c] *= skalieungsfaktor[c] 
    consumption *= consumption_scale
    residualload = consumption - (generations['Wind'] + generations['Photovoltaik'])
    
    EMF_primärenergy = input_data['Emissionsfaktor[TCO2/MWhth]'].to_dict()
    EMF_primärenergy['Wärme'] = 0.285 
    EMF_primärenergy['Strom'] = 0.645
       
    emissionfactor = input_data['Emissionsfaktor[TCO2/MWhth]'].to_dict()
    efficiency = input_data['Wirkungsgrad[MWhel/MWhth]_el'].to_dict()
    efficiency_el_kwk = tech_params['Eff_el_kwk'].fillna(0).to_dict()
    efficiency_th_kwk = tech_params['Eff_th_kwk'].fillna(0).to_dict()
    
    methods = ['Wärmegutschrift', 'IEA-Methode', 'Finnische Methode', 'Stromgutschrift']
    allokation_facktors = {'Wärmegutschrift': {f: 0 for f in convensional}, 
                          'IEA-Methode': tech_params.loc[convensional,'Allokationsfaktor_IEA'].to_dict(), 
                          'Finnische Methode': tech_params.loc[convensional,'Allokationsfaktor_Finnisch'].to_dict(), 
                          'Stromgutschrift': {f: 1 for f in convensional}}
    
    ## Strommixemissionsfaktoren
    AEF_hourly[year], AEF[year] = dict(), dict()
    print(f'\nCalculating average emission factor: AEF for {year}: ')
        
    AEF_hourly[year]['IEA-Methode'] = sum(generations[f]*tech_params.loc[f,'Anteil_NichtKWK']*EMF_primärenergy[f]/tech_params.loc[f,'Eff_el'] + 
                                          generations[f]*tech_params.loc[f,'Anteil_KWK']*EMF_primärenergy[f]*allokation_facktors['IEA-Methode'][f]/tech_params.loc[f,'Eff_el_kwk'] for f in convensional)/generations.sum(axis=1)
    
    AEF_hourly[year]['Finnische Methode'] = sum(generations[f]*tech_params.loc[f,'Anteil_NichtKWK']*EMF_primärenergy[f]/tech_params.loc[f,'Eff_el'] + 
                                                generations[f]*tech_params.loc[f,'Anteil_KWK']*EMF_primärenergy[f]*allokation_facktors['Finnische Methode'][f]/tech_params.loc[f,'Eff_el_kwk'] for f in convensional)/generations.sum(axis=1)
            
    AEF_hourly[year]['Wärmegutschrift'] = sum(generations[f]*tech_params.loc[f,'Anteil_NichtKWK']*EMF_primärenergy[f]/tech_params.loc[f,'Eff_el'] + 
                                              generations[f]*tech_params.loc[f,'Anteil_KWK']*(EMF_primärenergy[f]-EMF_primärenergy['Wärme']*tech_params.loc[f,'Eff_th_kwk'])/tech_params.loc[f,'Eff_el_kwk'] for f in convensional)/generations.sum(axis=1)
    
    AEF_hourly[year]['Stromgutschrift'] = sum(generations[f]*tech_params.loc[f,'Anteil_NichtKWK']*EMF_primärenergy[f]/tech_params.loc[f,'Eff_el'] + 
                                              generations[f]*tech_params.loc[f,'Anteil_KWK']*EMF_primärenergy['Strom'] for f in convensional)/generations.sum(axis=1)
        
    AEF_hourly[year]['Referenz'] = sum(generations[f]*emissionfactor[f]/tech_params.loc[f,'Eff_el'] for f in convensional)/generations.sum(axis=1)
    
    for k in AEF_hourly[year].keys(): 
        AEF[year][k] = sum(AEF_hourly[year][k])
        print(f'***** Methode {k}: \t {round(AEF[year][k],3)} [TCO2/MWh]')
        
    print('\nBuilding marginal power plant table')
    ## Grenzkraftwerkemissionsfaktoren

    chp_portion['Import'] = 0
    
    data_table = input_data.copy()
    data_table['Wirkungsgrad[MWhel/MWhth]_kwk'] = np.nan
    data_table['Verfügbare_Leistung[MW]'] = data_table['Verfügbare_Leistung[MW]'] * (1-pd.Series(chp_portion))
    data_table['Gesamtkosten[Euto/MWhel]'] = (data_table['Brennstoffpreis[MWhel/MWhth]'] + data_table['Emissionsfaktor[TCO2/MWhth]']*co2_price[year])/data_table['Wirkungsgrad[MWhel/MWhth]_el'] + data_table['Variable_Kosten[Euro/MWhel]']
    data_table['Gesamtkosten[Euto/MWhel]-Wärmegutschrift'] = data_table['Gesamtkosten[Euto/MWhel]']
    
    # Wärmegutschrift
    df = input_data.copy().loc[['Erdgas','Steinkohle','Braunkohle','Biomasse','SonstigeKonventionelle']]
    df['Wirkungsgrad[MWhel/MWhth]_el'] = np.nan
    df['Wirkungsgrad[MWhel/MWhth]_kwk'] = tech_params['Eff_el_kwk'] 
    df['Verfügbare_Leistung[MW]'] = df['Verfügbare_Leistung[MW]'] * pd.Series(chp_portion)
    df = df.rename({i: f'{i}_KWK' for i in df.index},axis=0)
    df['Gesamtkosten[Euto/MWhel]'] = (df['Brennstoffpreis[MWhel/MWhth]'] + df['Emissionsfaktor[TCO2/MWhth]']*co2_price[year])/df['Wirkungsgrad[MWhel/MWhth]_kwk'] + df['Variable_Kosten[Euro/MWhel]']
    df['Gesamtkosten[Euto/MWhel]-Wärmegutschrift'] = df['Gesamtkosten[Euto/MWhel]'] - (df.loc['Erdgas_KWK', 'Brennstoffpreis[MWhel/MWhth]'] + df.loc['Erdgas_KWK','Emissionsfaktor[TCO2/MWhth]']*co2_price[year])/tech_params.loc['Erdgas','Eff_th_ref']

    data_table = pd.concat([data_table.rename({i: f'{i}_KOND' for i in ['Erdgas','Steinkohle','Braunkohle','Biomasse','SonstigeKonventionelle']},axis=0),df],ignore_index=False)
    data_table = data_table.sort_values(['Gesamtkosten[Euto/MWhel]-Wärmegutschrift'])
   
    residual_last_energiy_source = [e for e in data_table.index if e.find('Wind') == -1 and e.find('Photo') == -1]
    marginal_table = data_table[data_table.index.isin(residual_last_energiy_source)].sort_values(['Gesamtkosten[Euto/MWhel]-Wärmegutschrift'])
    marginal_table['Kumulierter Betrag[MW]'] = marginal_table['Verfügbare_Leistung[MW]'].cumsum()
    cols = ['Emissionsfaktor[TCO2/MWhth]',
            'Wirkungsgrad[MWhel/MWhth]_el',
            'Wirkungsgrad[MWhel/MWhth]_kwk',
            'Brennstoffpreis[MWhel/MWhth]',
            'Variable_Kosten[Euro/MWhel]',
            'Gesamtkosten[Euto/MWhel]',
            'Gesamtkosten[Euto/MWhel]-Wärmegutschrift',
            'Installierte_Leistung[MW]',
            'Verfügbare_Leistung[MW]',
            'Kumulierter Betrag[MW]']
    marginal_table = marginal_table[cols]
    
    print('Finding marginal power plant for each hour')
    grenzkraftwerk = {}
    for h in residualload.index:
        try: 
            grenzkraftwerk[h] = marginal_table[marginal_table['Kumulierter Betrag[MW]'] >= residualload[h]].index[0]
        except: 
            grenzkraftwerk[h] = 'Import'
            
    marginal_pp_sorted = {k: len([v for v in grenzkraftwerk.values() if v == k]) for k in marginal_table.index}
    marginal_pp_sorted['Import'] = max(0,8760-sum(list(marginal_pp_sorted.values())))
    marginal_table['Grenzkraftwerk #Stunden'] = pd.Series(marginal_pp_sorted)
    
    # Anzahl der Grenkraftwerke je nach Technologie
    if save_marginal_tables:
        marginal_table[['Grenzkraftwerk #Stunden']].to_excel(f'{outputs_folder}/grenzkraftwerke_{region}_{year}.xlsx')
            
    print(f'\nCalculating marginal emission factor: MEF for {year}: ')
    efficiency_dict = (marginal_table['Wirkungsgrad[MWhel/MWhth]_el'].fillna(0) + marginal_table['Wirkungsgrad[MWhel/MWhth]_kwk'].fillna(0)).to_dict()
    efficiency_dict_referenz = efficiency_dict.copy()
    for k in ['Erdgas','Steinkohle','Braunkohle','Biomasse']: 
        efficiency_dict_referenz[f'{k}_KWK'] = efficiency_dict_referenz[f'{k}_KOND']
    
    #### Stündliche MEF
    MEF_hourly[year], MEF[year] = dict(), dict()
    emissionfactor_Import = dict()
    
    specific_emission = dict()
    for m in methods: 
        allokations_facktor_voll = {**{f'{k}_KWK': allokation_facktors[m][k] for k in ['Braunkohle', 'Steinkohle', 'Erdgas', 'SonstigeKonventionelle']}, 
                                    **{k: 1 for k in marginal_pp_sorted.keys() if k.find('KWK') == -1 or k.find('Biomasse')>-1}}
        emissionfactor_Import[m] = AEF_hourly[year][m]
        mef_hourly = pd.Series(data=None, index=residualload.index,dtype='float')
        if m in ['IEA-Methode', 'Finnische Methode']: 
            specific_emission[m] = {k: marginal_table['Emissionsfaktor[TCO2/MWhth]'].to_dict()[k]*allokations_facktor_voll[k]/efficiency_dict[k] for k in pd.Series(grenzkraftwerk.values()).drop_duplicates()}
        if m in ['Wärmegutschrift']: 
            specific_emission[m] = {**{f'{k}_KWK': (marginal_table['Emissionsfaktor[TCO2/MWhth]'].to_dict()[f'{k}_KWK']-EMF_primärenergy['Wärme']*tech_params.loc[k,'Eff_th_kwk'])/efficiency_dict[f'{k}_KWK'] for k in ['Braunkohle', 'Steinkohle', 'Erdgas', 'SonstigeKonventionelle']},
                                       **{k: marginal_table['Emissionsfaktor[TCO2/MWhth]'].to_dict()[k]*allokations_facktor_voll[k]/efficiency_dict[k] for k in marginal_pp_sorted.keys() if k.find('KWK') == -1 or k.find('Biomasse')>-1}}
        if m in [ 'Stromgutschrift']: 
            specific_emission[m] = {**{f'{k}_KWK': EMF_primärenergy['Strom'] for k in ['Braunkohle', 'Steinkohle', 'Erdgas', 'SonstigeKonventionelle']},
                                       **{k: marginal_table['Emissionsfaktor[TCO2/MWhth]'].to_dict()[k]*allokations_facktor_voll[k]/efficiency_dict[k] for k in marginal_pp_sorted.keys() if k.find('KWK') == -1 or k.find('Biomasse')>-1}}
        for h in consumption.index: 
            if grenzkraftwerk[h] == 'Import': 
                mef_hourly[h] = emissionfactor_Import[m][h]
            else:
                mef_hourly[h] = specific_emission[m][grenzkraftwerk[h]] 
        
        ### Jährliche MEF
        MEF_hourly[year][m] = mef_hourly
        MEF[year][m] = sum(MEF_hourly[year][m])
        print(f'***** Methode {m}: \t {round(MEF[year][m],3)} [TCO2/MWh]')
    
    emissionfactor_Import['Referenz'] = AEF_hourly[year]['Referenz']
    mef_hourly = pd.Series(data=None, index=residualload.index,dtype='float')
    specific_emission['Referenz'] = {k: marginal_table['Emissionsfaktor[TCO2/MWhth]'].to_dict()[k]/efficiency_dict_referenz[k] for k in pd.Series(grenzkraftwerk.values()).drop_duplicates()}
    for h in consumption.index: 
        if grenzkraftwerk[h] == 'Import': 
            mef_hourly[h] = emissionfactor_Import['Referenz'][h]
        else:
            mef_hourly[h] = specific_emission['Referenz'][grenzkraftwerk[h]]
    
    ### Jährliche MEF Refernz
    MEF_hourly[year]['Referenz'] = mef_hourly
    MEF[year]['Referenz'] = sum(MEF_hourly[year]['Referenz'])
    print(f'***** Methode Referenz: \t {round(MEF[year]["Referenz"],3)} [TCO2/MWh]')
    
    ## Abbildungen
    for m in methods+['Referenz']:
        Plot = plot_AEF_MEF(year,region,m,AEF_hourly[year][m],AEF[year][m],MEF_hourly[year][m],MEF[year][m], 
                            first_hour=0,last_hour=8760,linewidth=2,
                            save_fig=True,path=plots_folder)
        Plot.close()
    
    for m in methods+['Referenz']:
        Plot_sorted = plot_AEF_MEF_sorted(year,region,m,AEF_hourly[year][m],AEF[year][m],MEF_hourly[year][m],MEF[year][m],
                                          specific_emission[m],marginal_table,save_fig=save_plots,path=plots_folder)
        Plot_sorted.close()
    
    Plot_sorted = plot_MEF_sorted_allMethods(year,region,methods+['Referenz'],AEF_hourly[year],AEF[year],MEF_hourly[year],MEF[year],
                                              specific_emission,marginal_table,save_fig=save_plots,path=plots_folder)
    Plot_sorted.close()
                 
    # Alle stündlichen Emissionsfaktoren 
    if save_ef_tables:
        writer = pd.ExcelWriter(f'{outputs_folder}/AEF_MEF_stündlich_{region}_{year}.xlsx', engine='xlsxwriter')
        emissionfactors_table = pd.DataFrame(index=AEF_hourly[year]['Referenz'].index)
        for m in methods+['Referenz']:    
            emissionfactors_table[m] = AEF_hourly[year][m]
        emissionfactors_table.reset_index().to_excel(writer,sheet_name='AEF',header=True,index=False)    
        emissionfactors_table = pd.DataFrame(index=MEF_hourly[year]['Referenz'].index)
        for m in methods+['Referenz']:    
            emissionfactors_table[m] = MEF_hourly[year][m]
        emissionfactors_table.reset_index().to_excel(writer,sheet_name='MEF',header=True,index=False)    
        writer.close()
           
# Zusammenfassung aller Jahre
serie_AEF = pd.DataFrame.from_dict(AEF, orient='columns').unstack()
serie_MEF = pd.DataFrame.from_dict(MEF, orient='columns').unstack()

df = pd.DataFrame() 
df['AEF'] = serie_AEF
df['MEF'] = serie_MEF
df = df/8760

# jährliche Emissionsfaktoren
if save_ef_tables:
    df.to_excel(f'{outputs_folder}/AEFMEF_jährlich_{region}.xlsx',header=True,index=True)


    
    


