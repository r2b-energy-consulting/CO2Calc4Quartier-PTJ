import os

# Einstellungen
years = [2019,2020,2021,2022] 
path = os.getcwd()
inputs_folder = 'Eingangsdaten'
plots_folder = 'Ausgangsabbildungen'
outputs_folder = 'Ausgangstabellen'

if not os.path.exists(plots_folder):
    os.makedirs(plots_folder)
if not os.path.exists(outputs_folder):
    os.makedirs(outputs_folder)
    
region = 'DE-LU' 
save_plots = True # wenn die Abbildungen gespeichert werden müssen
save_ef_tables = True # wenn die Emissionsfaktortabellen gespeichert werden müssen
save_marginal_tables = True # wenn die Grenzkraftwerkinformationen gespeichert werden müssen

# Vordefiniren der Variablen
AEF_hourly, AEF = dict(), dict()
MEF_hourly, MEF = dict(), dict()

convensional = ['Braunkohle', 'Steinkohle', 'Erdgas', 'SonstigeKonventionelle'] # konventionelle Energieträger
