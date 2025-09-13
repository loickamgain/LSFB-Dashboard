import os
from collections import defaultdict

def find_duplicates(directories):
    """Trouver les doublons dans une liste de dossiers en prenant en compte les extensions"""
    file_paths = defaultdict(list)

    # Parcourir tous les fichiers dans les dossiers fournis
    for directory in directories:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                
                # Enregistrer les fichiers avec leur nom complet et leur chemin
                file_paths[file].append(file_path)
    
    # Vérifier les doublons
    duplicates_info = defaultdict(list)
    for file_name, paths in file_paths.items():
        if len(paths) > 1:  # Si plusieurs fichiers ont le même nom et extension
            duplicates_info[file_name] = paths
    
    return duplicates_info

# Liste des cinq dossiers à analyser
directories = [
    r"E:\lsfb dataset\cont\videos",
    #r"E:\lsfb dataset\cont\poses\face",
    #r"E:\lsfb dataset\cont\poses\left_hand",
    #r"E:\lsfb dataset\cont\poses\pose",
    #r"E:\lsfb dataset\cont\poses\right_hand"
]

# Trouver les doublons
duplicates = find_duplicates(directories)

if duplicates:
    print("Doublons trouvés :")
    for file_name, file_paths in duplicates.items():
        print(f"\nDoublon : {file_name}")
        for file_path in file_paths:
            print(f"  - Dossier: {os.path.dirname(file_path)} | Fichier: {file_path}")
else:
    print("Aucun doublon trouvé.")
