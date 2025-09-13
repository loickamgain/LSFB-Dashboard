import pandas as pd

file_path = r"E:\lsfb dataset\cont\instances.csv"

# Charger les données du fichier CSV
df = pd.read_csv(file_path, sep='\t')

# Afficher les colonnes du DataFrame
print(df.columns)
