import pandas as pd

# Caricare il dataset
file_path = '/home/arthas0130/Rasa/Dataset DnD/dnd_monsters.csv'
monsters_df = pd.read_csv(file_path)

# Eliminare le righe che hanno valori nulli nelle colonne specificate
columns_to_check = ['url', 'str', 'dex', 'con', 'int', 'wis', 'cha']
filtered_monsters_df = monsters_df.dropna(subset=columns_to_check)

# Salvare il nuovo dataset filtrato in un file separato (se necessario)
output_path = '/home/arthas0130/Rasa/actions/Dataset/dnd_monsters_filtered.csv'
filtered_monsters_df.to_csv(output_path, index=False)

# Mostrare una preview del dataset filtrato
filtered_monsters_df.head()
