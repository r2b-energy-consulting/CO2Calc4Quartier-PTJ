import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def plot_AEF_MEF(year,region,method,AEF_hourly,AEF,MEF_hourly,MEF,first_hour=0,last_hour=8760,linewidth=1,save_fig=False,path='..',comment=''):
    b, e = first_hour, last_hour
    plt.figure(figsize=(20,5)) 
    MEF_hourly[b:e].plot(grid=True, label='MEF (stündlich)', color='darkturquoise',linewidth=max(linewidth-1,1))
    AEF_hourly[b:e].plot(grid=True, label='AEF (stündlich)', color='teal',linewidth=linewidth)

    plt.hlines(y=MEF/8760, xmin = MEF_hourly[b:e].index[0] , xmax = MEF_hourly[b:e].index[-1], linewidth=3, color='red', label='MEF (jährlich)')
    plt.hlines(y=AEF/8760, xmin = AEF_hourly[b:e].index[0] , xmax = AEF_hourly[b:e].index[-1], linewidth=3, color='darkred', label='AEF (jährlich)')

    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.legend(loc=1)
    plt.xlabel('Stunden im Jahr')
    plt.ylabel('CO2 Emissionen [TonCO2/MWh]')
    plt.yticks(np.arange(0, max(MEF_hourly.values)*1.1, step=0.1))

    plt.title(f'Grenzkraftwerks-Emissionen/Strommix-Emissionen - Region {region} - Jahr {year} - {method}')

    if save_fig: 
        plt.savefig(f'{path}/AEFMEF_{region}_{year}_{method}{comment}.png', dpi=300, facecolor='white', bbox_inches='tight')
    return(plt)
   
def plot_AEF_MEF_sorted(year,region,method,AEF_hourly,AEF,MEF_hourly,MEF,spezifische_emission,convensional_table,save_fig=False,path='..'):    
    plt.figure(figsize=(20,5))    
    plt.plot(pd.Series(MEF_hourly.sort_values(ascending=False).values), linewidth=3, color='darkturquoise', label=f'MEF (stündlich)')
    
    i = 0
    for k in [k for k in sorted(spezifische_emission, key=spezifische_emission.get, reverse=True) if spezifische_emission[k]>0]:
        vert_space = 0.07 if k in ['Braunkohle_KWK', 'Erdgas_KWK'] and method in ['IEA-Methode', 'Finnische Methode'] else 0.03
        if convensional_table.loc[k,'Grenzkraftwerk #Stunden'] >= 200: 
            plt.text(i+50+max(0,int(convensional_table.loc[k,'Grenzkraftwerk #Stunden']/2)-300), spezifische_emission[k]+vert_space, k, fontsize='large', color='black')
        i += convensional_table.loc[k,'Grenzkraftwerk #Stunden']
    plt.text(i+50, 0.03, 'Andere', fontsize='large', color='black')
    
    pd.Series(AEF_hourly.sort_values(ascending=False).values).plot(label='AEF (stündlich)', color='teal',linewidth=3)

    plt.hlines(y=MEF/8760, xmin=0, xmax=8760, color='red',label='MEF (jährlich)',linewidth=3)
    plt.hlines(y=AEF/8760, xmin=0, xmax=8760, color='darkred',label='AEF (jährlich)',linewidth=3)

    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.legend(loc=1)
    plt.title(f'Grenzkraftwerks-Emissionen/Strommix-Emissionen - Sortiert - Region {region} - Jahr {year} - {method}')
    plt.xlabel('Stunden im Jahr')
    plt.xticks(np.arange(0, 8800, step=500))
    plt.ylabel('CO2 Emissionen [TonCO2/MWh]')
    plt.yticks(np.arange(0, max(MEF_hourly.values)*1.1, step=0.2))
    plt.grid(True)

    if save_fig:
        plt.savefig(f'{path}/Grenzkraftwerke_sortiert_{region}_{year}_{method}.png', dpi=300, facecolor='white',bbox_inches='tight')
    return(plt)

def plot_MEF_sorted_allMethods(year,region,methods,AEF_hourly,AEF,MEF_hourly,MEF,spezifische_emission,convensional_table,save_fig=False,path='..'):   
    colors = {'Stromgutschrift': '#006851', 'Referenz': '#8FB845', 'Finnische Methode': '#00B7A1', 'IEA-Methode': '#25FFE4', 'Wärmegutschrift': '#9B3C27'}
    plt.figure(figsize=(20,5))    
    for m in colors.keys():
        plt.plot(pd.Series(MEF_hourly[m].sort_values(ascending=False).values), linewidth=3, label=f'MEF (stündlich) {m}', color=colors[m])
    
    m = 'Stromgutschrift'
    plt.plot(pd.Series(MEF_hourly[m].sort_values(ascending=False).values), linewidth=3, color=colors[m])
    i = 0
    for k in [k for k in sorted(spezifische_emission[m], key=spezifische_emission[m].get, reverse=True) if spezifische_emission[m][k]>0]:
        if convensional_table.loc[k,'Grenzkraftwerk #Stunden'] >= 200: 
            plt.text(i+50+max(0,int(convensional_table.loc[k,'Grenzkraftwerk #Stunden']/2)-300), spezifische_emission[m][k]+0.03, k, fontsize='large', color='black')
        i += convensional_table.loc[k,'Grenzkraftwerk #Stunden']
    plt.text(i+50, 0.03, 'Andere', fontsize='large', color='black')

    
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.legend(loc=1)
    plt.title(f'Grenzkraftwerks-Emissionen (sortiert) für alle Methoden - Region {region} - Jahr {year}')
    plt.xlabel('Stunden im Jahr')
    plt.xticks(np.arange(0, 8800, step=500))
    plt.ylabel('CO2 Emissionen [TonCO2/MWh]')
    plt.yticks(np.arange(0, max(max(MEF_hourly[m].values) for m in methods+['Referenz']),  step=0.2))
    plt.grid(True)
    
    if save_fig:
        plt.savefig(f'{path}/Grenzkraftwerke_sortiert_{region}_{year}.png', dpi=300, facecolor='white',bbox_inches='tight')
    return(plt)

