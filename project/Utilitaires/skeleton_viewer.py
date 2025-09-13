import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import tkinter as tk
from tkinter import filedialog
from matplotlib.widgets import Slider, Button

def charger_fichier(message):
    """Ouvre une boîte de dialogue pour sélectionner un fichier .npy et le charge."""
    root = tk.Tk()
    root.withdraw()
    chemin = filedialog.askopenfilename(title=message, filetypes=[("Fichiers Numpy", "*.npy")])
    if not chemin:
        raise FileNotFoundError("Aucun fichier sélectionné pour " + message)
    return np.load(chemin)

# --- Chargement des données ---
print("Sélection du fichier pour left_hand...")
left_hand_all = charger_fichier("Sélectionner le fichier npy pour left_hand")
print("Sélection du fichier pour right_hand...")
right_hand_all = charger_fichier("Sélectionner le fichier npy pour right_hand")
print("Sélection du fichier pour pose...")
pose_all = charger_fichier("Sélectionner le fichier npy pour pose")
print("Sélection du fichier pour face...")
face_all = charger_fichier("Sélectionner le fichier npy pour face")

# --- Connexions (exemple MediaPipe) ---
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

# --- Paramètres d'animation ---
num_frames = min(left_hand_all.shape[0],
                 right_hand_all.shape[0],
                 pose_all.shape[0],
                 face_all.shape[0])
initial_interval = 40  # en ms (~25 fps)

# Variable globale pour la frame courante
current_frame = 0

# --- Choix du style Matplotlib ---
plt.style.use('seaborn-v0_8-darkgrid')

# --- Création de la figure et de l'axe principal ---
fig, ax = plt.subplots(figsize=(8, 6))
fig.subplots_adjust(bottom=0.3)
fig.patch.set_facecolor('#2c2c2c')
ax.set_facecolor('#2c2c2c')
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)

def frame_generator():
    """Générateur infini qui retourne current_frame et l'incrémente."""
    global current_frame
    while True:
        yield current_frame
        current_frame = (current_frame + 1) % num_frames

def update(frame):
    """Met à jour l'affichage pour la frame donnée."""
    global current_frame
    current_frame = frame
    ax.clear()
    # Refixer limites et fond après clear()
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_facecolor('#2c2c2c')
    
    # Extraction des données de la frame courante
    left_hand = left_hand_all[frame]   # (21, 3)
    right_hand = right_hand_all[frame]  # (21, 3)
    pose = pose_all[frame]              # (33, 3)
    face = face_all[frame]              # (478, 3)
    
    # Coordonnées X et Y (affichage 2D)
    x_pose, y_pose = pose[:, 0], pose[:, 1]
    x_lh, y_lh = left_hand[:, 0], left_hand[:, 1]
    x_rh, y_rh = right_hand[:, 0], right_hand[:, 1]
    x_face, y_face = face[:, 0], face[:, 1]
    
    # --- Tracé de la pose (corps) avec liaisons épaissies ---
    ax.scatter(x_pose, y_pose, c='green', s=20, label='Pose')
    for (i, j) in pose_connections:
        if i < pose.shape[0] and j < pose.shape[0]:
            ax.plot([x_pose[i], x_pose[j]], [y_pose[i], y_pose[j]],
                    color='green', linewidth=2)  # Épaisseur augmentée pour le corps
    
    # --- Tracé des mains avec points réduits ---
    ax.scatter(x_lh, y_lh, c='red', s=10, label='Main Gauche')  # taille réduite
    for (i, j) in hand_connections:
        ax.plot([x_lh[i], x_lh[j]], [y_lh[i], y_lh[j]],
                color='red', linewidth=2)
    
    ax.scatter(x_rh, y_rh, c='blue', s=10, label='Main Droite')  # taille réduite
    for (i, j) in hand_connections:
        ax.plot([x_rh[i], x_rh[j]], [y_rh[i], y_rh[j]],
                color='blue', linewidth=2)
    
    # --- Tracé du visage ---
    ax.scatter(x_face, y_face, c='orange', s=5, alpha=0.6, label='Visage')
    
    # --- Arêtes reliant la pose aux mains ---
    if pose.shape[0] > 15 and left_hand.shape[0] > 0:
        ax.plot([pose[15, 0], left_hand[0, 0]], [pose[15, 1], left_hand[0, 1]],
                color='magenta', linewidth=2, label='Relais gauche')
    if pose.shape[0] > 16 and right_hand.shape[0] > 0:
        ax.plot([pose[16, 0], right_hand[0, 0]], [pose[16, 1], right_hand[0, 1]],
                color='cyan', linewidth=2, label='Relais droite')
    
    # Mise en forme générale
    ax.set_title(f"Squelette 2D - Frame {frame}/{num_frames-1}", color='white')
    ax.set_xlabel("X", color='white')
    ax.set_ylabel("Y", color='white')
    ax.invert_yaxis()
    ax.axis('equal')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_color('white')
    ax.grid(True, color='white', alpha=0.2)
    
    # Mise à jour du slider de frame sans déclencher sa callback
    frame_slider.eventson = False
    frame_slider.set_val(frame)
    frame_slider.eventson = True
    
    if frame == 0:
        ax.legend(facecolor='#444444', edgecolor='white')

# --- Animation auto avec cache_frame_data désactivé ---
ani = animation.FuncAnimation(fig, update, frames=frame_generator,
                              interval=initial_interval, repeat=True,
                              cache_frame_data=False)

# --- Slider de vitesse (contrôle l'intervalle en ms) ---
ax_speed = fig.add_axes([0.15, 0.10, 0.70, 0.03], facecolor='#555555')
speed_slider = Slider(ax_speed, 'Vitesse (ms)', 10, 1000, valinit=initial_interval, valstep=10)
def update_speed(val):
    ani.event_source.interval = speed_slider.val
speed_slider.on_changed(update_speed)
# Texte informatif placé à droite
ax_speed.text(1.05, 0.5, "Contrôle de la vitesse", transform=ax_speed.transAxes,
              color='white', fontsize=9, verticalalignment='center', horizontalalignment='left')

# --- Slider de frame (navigation dans les frames) ---
ax_frame = fig.add_axes([0.15, 0.05, 0.70, 0.03], facecolor='#555555')
frame_slider = Slider(ax_frame, 'Frame', 0, num_frames-1, valinit=0, valstep=1)
def update_frame(val):
    global current_frame
    new_frame = int(frame_slider.val)
    current_frame = new_frame
    update(new_frame)  # Met à jour immédiatement l'affichage
    # L'animation continue à partir de new_frame
frame_slider.on_changed(update_frame)
# Texte informatif placé à droite
ax_frame.text(1.05, 0.5, "Navigation dans les frames", transform=ax_frame.transAxes,
              color='white', fontsize=9, verticalalignment='center', horizontalalignment='left')

# --- Bouton Pause/Resume (ne modifie que l'animation auto) ---
ax_button = fig.add_axes([0.02, 0.10, 0.1, 0.04])
pause_button = Button(ax_button, 'Pause', color='gray', hovercolor='red')
is_paused = False
def toggle_pause(event):
    global is_paused
    if is_paused:
        ani.event_source.start()
        pause_button.label.set_text('Pause')
        is_paused = False
    else:
        ani.event_source.stop()
        pause_button.label.set_text('Resume')
        is_paused = True
pause_button.on_clicked(toggle_pause)

plt.show()
