import os
import pandas as pd

def remove_extension(filename):
    """Retirer l'extension du fichier."""
    return os.path.splitext(filename)[0]

def compare_directories(dir1, dir2, subfolders):
    """Comparer les fichiers dans dir1 et dir2 en ignorant les extensions et indiquer où chaque fichier est présent."""
    file_status = []

    for subfolder in subfolders:
        subdir1 = os.path.join(dir1, subfolder)
        subdir2 = os.path.join(dir2, subfolder)

        files_in_subdir1 = {remove_extension(f) for f in os.listdir(subdir1) if os.path.isfile(os.path.join(subdir1, f))} if os.path.exists(subdir1) else set()
        files_in_subdir2 = {remove_extension(f) for f in os.listdir(subdir2) if os.path.isfile(os.path.join(subdir2, f))} if os.path.exists(subdir2) else set()

        all_files = files_in_subdir1.union(files_in_subdir2)

        for file in all_files:
            status_poses = "Présent" if file in files_in_subdir1 else "Absent"
            status_videos = "Présent" if file in files_in_subdir2 else "Absent"
            file_status.append({'Sous-dossier': subfolder, 'Fichier': file, 'Présent dans poses': status_poses, 'Présent dans videos': status_videos})

    return file_status

# Utiliser des chaînes brutes pour éviter les séquences d'échappement
dir1 = r"E:\lsfb dataset\cont\poses"
dir2 = r"E:\lsfb dataset\cont\videos"
subfolders = ['face', 'pose', 'left_hand', 'right_hand']

# Appel de la fonction pour comparer les dossiers
file_status = compare_directories(dir1, dir2, subfolders)

# Créer un DataFrame à partir des statuts des fichiers
df = pd.DataFrame(file_status)

# Enregistrer le DataFrame dans un fichier Excel
output_file = r"D:\Etudes\Bachelier Informatique Unamur\Bloc 3\Projet\lsfb_projet\statuts_fichiers.xlsx"
df.to_excel(output_file, index=False, engine='openpyxl')

print(f"Les statuts des fichiers ont été enregistrés dans {output_file}")
