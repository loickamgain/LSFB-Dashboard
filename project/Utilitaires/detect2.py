import os
import pandas as pd

def remove_extension(filename):
    """Retirer l'extension du fichier."""
    return os.path.splitext(filename)[0]

def compare_directories(dir1, dir2, subfolders):
    """Comparer les fichiers dans dir1 et dir2 en ignorant les extensions et lister les vidéos sans pose."""
    missing_files = []

    for subfolder in subfolders:
        subdir1 = os.path.join(dir1, subfolder)
        subdir2 = os.path.join(dir2, subfolder)

        # Récupérer les fichiers sans extension dans poses
        files_in_subdir1 = {remove_extension(f) for f in os.listdir(subdir1) if os.path.isfile(os.path.join(subdir1, f))} if os.path.exists(subdir1) else set()

        # Récupérer les fichiers sans extension dans videos
        files_in_subdir2 = {remove_extension(f) for f in os.listdir(subdir2) if os.path.isfile(os.path.join(subdir2, f))} if os.path.exists(subdir2) else set()

        # Identifier les vidéos sans pose
        missing_in_subdir2 = files_in_subdir2 - files_in_subdir1

        for file in missing_in_subdir2:
            missing_files.append({'Sous-dossier': subfolder, 'Fichier vidéo sans pose': file})

    return missing_files

# Utiliser des chaînes brutes pour éviter les séquences d'échappement
dir1 = r"E:\lsfb dataset\cont\poses"
dir2 = r"E:\lsfb dataset\cont\videos"
subfolders = ['face', 'pose', 'left_hand', 'right_hand']

# Appel de la fonction pour comparer les dossiers
missing_files = compare_directories(dir1, dir2, subfolders)

# Créer un DataFrame à partir des fichiers manquants
df = pd.DataFrame(missing_files)

# Enregistrer le DataFrame dans un fichier Excel
output_file = r"D:\Etudes\Bachelier Informatique Unamur\Bloc 3\Projet\lsfb_projet\videos_sans_pose.xlsx"
df.to_excel(output_file, index=False, engine='openpyxl')

print(f"Les vidéos sans pose ont été enregistrées dans {output_file}")
