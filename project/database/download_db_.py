from lsfb_dataset import Downloader

# Télécharger le dataset 'cont'
downloader_cont = Downloader(dataset='cont', destination="D:\Projet LSFB\dataset\cont", include_videos=True)
downloader_cont.download()

# Télécharger le dataset 'isol'
downloader_isol = Downloader(dataset='isol', destination="D:\Projet LSFB\dataset\isol", include_videos=True)
downloader_isol.download()
