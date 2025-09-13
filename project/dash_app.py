import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import numpy as np
import plotly.graph_objs as go
import json

# Initialisation de l'application Dash
app = dash.Dash(__name__)

# Connexions des parties du corps (par exemple, MediaPipe)
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

# Layout de l'application Dash
app.layout = html.Div([
    dcc.Store(id='video_paths', data={}),  # Stocker les chemins des fichiers .npy
    dcc.Graph(id='skeleton-graph'),
    html.Button('Pause', id='pause-button', n_clicks=0),
    dcc.Interval(id='interval-component', interval=40, n_intervals=0),
])

# Fonction pour charger un fichier .npy donné par son chemin
def charger_fichier(chemin):
    """Charge un fichier .npy à partir d'un chemin donné."""
    if not chemin:
        raise FileNotFoundError(f"Aucun fichier trouvé pour le chemin spécifié : {chemin}")
    return np.load(chemin)

# Écouteur pour recevoir les données envoyées par postMessage (du frontend)
@app.callback(
    Output('video_paths', 'data'),
    Input('interval-component', 'n_intervals'),
    [dash.dependencies.State('video_paths', 'data')]
)
def update_video_paths(n_intervals, current_data):
    # Recevoir les chemins des poses envoyés via postMessage
    return current_data  # Enregistre ou utilise les données ici

# Mise à jour de l'animation avec les fichiers .npy
@app.callback(
    Output('skeleton-graph', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('pause-button', 'n_clicks'),
    [dash.dependencies.State('video_paths', 'data')]
)
def update_graph(n_intervals, n_clicks, video_paths):
    if not video_paths:
        return go.Figure()  # Retourne une figure vide si aucun chemin n'est disponible

    # Récupération des chemins des fichiers .npy pour chaque partie du corps
    left_hand_paths = video_paths.get('left_hand', [])
    right_hand_paths = video_paths.get('right_hand', [])
    pose_paths = video_paths.get('pose', [])
    face_paths = video_paths.get('face', [])

    # Charger les fichiers .npy
    left_hand_all = [charger_fichier(path) for path in left_hand_paths]
    right_hand_all = [charger_fichier(path) for path in right_hand_paths]
    pose_all = [charger_fichier(path) for path in pose_paths]
    face_all = [charger_fichier(path) for path in face_paths]

    # Paramètres d'animation et création de la figure
    current_frame = 0  # Frame courante par défaut
    num_frames = min(len(left_hand_all), len(right_hand_all), len(pose_all), len(face_all))

    # Extraction des données pour l'affichage
    left_hand = left_hand_all[current_frame]
    right_hand = right_hand_all[current_frame]
    pose = pose_all[current_frame]
    face = face_all[current_frame]

    # Coordonnées X et Y pour l'affichage 2D
    x_pose, y_pose = pose[:, 0], pose[:, 1]
    x_lh, y_lh = left_hand[:, 0], left_hand[:, 1]
    x_rh, y_rh = right_hand[:, 0], right_hand[:, 1]
    x_face, y_face = face[:, 0], face[:, 1]

    # Tracé des lignes du squelette (par exemple, bras, tête, etc.)
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

    figure = {
        'data': [
            go.Scatter(x=x_pose, y=y_pose, mode='markers', marker=dict(color='green', size=10), name='Pose'),
            go.Scatter(x=x_lh, y=y_lh, mode='markers', marker=dict(color='red', size=6), name='Main Gauche'),
            go.Scatter(x=x_rh, y=y_rh, mode='markers', marker=dict(color='blue', size=6), name='Main Droite'),
            go.Scatter(x=x_face, y=y_face, mode='markers', marker=dict(color='orange', size=3), name='Visage')
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

    return figure

if __name__ == "__main__":
    app.run(debug=True)
