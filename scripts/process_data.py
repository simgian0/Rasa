import pandas as pd

# Carica il dataset
df = pd.read_csv('/home/arthas0130/Rasa/Dataset DnD/over_one_mil_chars.csv')

# Elimina i duplicati e visualizza le classi uniche
unique_classes = df['class_starting'].dropna().unique().tolist()

print(unique_classes)