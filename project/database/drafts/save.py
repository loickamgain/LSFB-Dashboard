async def insert_videos_cont(session: AsyncSession, cont_folder_path: str):
    video_folder = os.path.join(cont_folder_path, 'videos')
    assert os.path.exists(video_folder), f"Le dossier 'videos' n'existe pas : {video_folder}"
    
    instance_csv_path = os.path.join(cont_folder_path, 'instances.csv')
    assert os.path.exists(instance_csv_path), f"Le fichier 'instance.csv' n'existe pas : {instance_csv_path}"
    
    instances_df = pd.read_csv(instance_csv_path, delimiter='\t')  
    instances_data = instances_df.to_dict(orient='records')

    for video_file in os.listdir(video_folder):
        if video_file.endswith('.mp4'):
            video_name = os.path.splitext(video_file)[0]
            print(f"Vidéo cherchée : {video_name}")
            print(f"Instances disponibles : {[item['id'] for item in instances_data]}")
            instance = next((item for item in instances_data if item.get('id') == video_name), None)
            assert instance is not None, f"Instance non trouvée pour la vidéo : {video_name}"
            video_path = os.path.join(video_folder, video_file)
            video = ContVideo(id=video_name, path=video_path)
            session.add(video)

    await session.commit()
