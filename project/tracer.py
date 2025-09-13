import numpy as np
import dash
from dash import dcc, html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import json

# Fonction pour charger un fichier .npy via un chemin d'accès
def charger_fichier(chemin):
    """Charge un fichier .npy donné par son chemin d'accès."""
    if not chemin:
        raise FileNotFoundError("Aucun fichier trouvé pour le chemin spécifié.")
    return np.load(chemin)

# Connexions (exemple MediaPipe)
pose_connections = [
    (11, 12), (11, 13), (13, 15),
    (12, 14), (14, 16), (11, 23),
    (12, 24), (23, 24)
]
hand_connections = [
    (0, 1), (1, 2), (2, 3), (3, 4),    
    (0, 5), (5, 6), (6, 7), (7, 8),    
    (0, 9), (9, 10), (10, 11), (11, 12),  
    (0, 13), (13, 14), (14, 15), (15, 16), 
    (0, 17), (17, 18), (18, 19), (19, 20)
]

# Paramètres d'animation
current_frame = 0  # La frame actuelle
animation_paused = False  # Variable pour suivre l'état de la pause

# Initialisation de l'application Dash
app = dash.Dash(__name__)

# Layout de l'application Dash
app.layout = html.Div([
    # Graphique pour afficher l'animation (squelette)
    dcc.Graph(id='skeleton-graph'),

    # Bouton Pause/Resume
    html.Button('Pause', id='pause-button', n_clicks=0),

    # Interval pour animer les frames
    dcc.Interval(
        id='interval-component',
        interval=40,  # Interval en ms (toutes les 40 ms)
        n_intervals=0
    ),
    
    # Stockage des chemins des fichiers .npy
    dcc.Store(id='video_paths', data='')  # Ce champ sera rempli dynamiquement par FastAPI
])

# Fonction de mise à jour du graphique avec les fichiers .npy transmis
@app.callback(
    Output('skeleton-graph', 'figure'),
    [Input('interval-component', 'n_intervals'), Input('pause-button', 'n_clicks')],
    [dash.dependencies.State('video_paths', 'data')]  # Récupérer les fichiers .npy à partir de l'état
)
def update_graph(n_intervals, n_clicks, video_paths):
    global current_frame
    poses_paths = json.loads(video_paths)  # Charger les chemins des fichiers .npy

    # Chargement des fichiers .npy pour chaque partie du corps (utilisation des chemins transmis)
    left_hand_all = charger_fichier(poses_paths[0])  # Assumer le premier fichier est pour la main gauche
    right_hand_all = charger_fichier(poses_paths[1])  # Main droite
    pose_all = charger_fichier(poses_paths[2])  # Pose générale
    face_all = charger_fichier(poses_paths[3])  # Visage

    # Paramètres d'animation
    num_frames = min(left_hand_all.shape[0],
                     right_hand_all.shape[0],
                     pose_all.shape[0],
                     face_all.shape[0])
    current_frame = (current_frame + 1) % num_frames

    # Extraction des données de la frame courante
    left_hand = left_hand_all[current_frame]   # (21, 3)
    right_hand = right_hand_all[current_frame]  # (21, 3)
    pose = pose_all[current_frame]              # (33, 3)
    face = face_all[current_frame]              # (478, 3)

    # Coordonnées X et Y pour l'affichage 2D
    x_pose, y_pose = pose[:, 0], pose[:, 1]
    x_lh, y_lh = left_hand[:, 0], left_hand[:, 1]
    x_rh, y_rh = right_hand[:, 0], right_hand[:, 1]
    x_face, y_face = face[:, 0], face[:, 1]

    # Correction de l'inversion du sens du squelette
    y_pose = -y_pose
    y_lh = -y_lh
    y_rh = -y_rh
    y_face = -y_face

    # Tracé des éléments (pose, mains, visage)
    pose_lines = [
        go.Scatter(x=[x_pose[i], x_pose[j]], y=[y_pose[i], y_pose[j]], mode='lines', line=dict(color='green', width=2))
        for (i, j) in pose_connections if i < pose.shape[0] and j < pose.shape[0]
    ]

    hand_lines_left = [
        go.Scatter(x=[x_lh[i], x_lh[j]], y=[y_lh[i], y_lh[j]], mode='lines', line=dict(color='red', width=2))
        for (i, j) in hand_connections
    ]

    hand_lines_right = [
        go.Scatter(x=[x_rh[i], x_rh[j]], y=[y_rh[i], y_rh[j]], mode='lines', line=dict(color='blue', width=2))
        for (i, j) in hand_connections
    ]

    # Réduction de la taille des cercles des articulations des mains
    hand_marker_size = 4  # Taille réduite des points des articulations des mains

    # Construction de la figure avec les éléments tracés
    figure = {
        'data': [
            go.Scatter(x=x_pose, y=y_pose, mode='markers', marker=dict(color='green', size=10), name='Pose'),
            go.Scatter(x=x_lh, y=y_lh, mode='markers', marker=dict(color='red', size=hand_marker_size), name='Main Gauche'),
            go.Scatter(x=x_rh, y=y_rh, mode='markers', marker=dict(color='blue', size=hand_marker_size), name='Main Droite'),
            go.Scatter(x=x_face, y=y_face, mode='markers', marker=dict(color='orange', size=3, opacity=0.6), name='Visage')
        ] + pose_lines + hand_lines_left + hand_lines_right,
        'layout': go.Layout(
            title=f"Squelette 2D - Frame {current_frame}/{num_frames-1}",
            xaxis=dict(title="X"),
            yaxis=dict(title="Y", scaleanchor="x"),
            hovermode='closest',
            showlegend=True,
            height=600
        )
    }

    return figure  # Retourner la figure
