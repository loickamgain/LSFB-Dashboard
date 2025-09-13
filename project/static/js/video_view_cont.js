// Exécute ce script une fois que le DOM HTML est complètement chargé
document.addEventListener("DOMContentLoaded", function () {

    // =======================
    //  INITIALISATION DES VARIABLES
    // =======================
  
    /**
     * Liste des segments à lire (format : [{start, end}, ...])
     * Injectée depuis le backend Flask via Jinja2
     */
    const segments = JSON.parse('{{ segments_list | safe }}');
  
    /**
     * Segment initial à jouer automatiquement (optionnel)
     * Injecté également par Flask
     */
    const firstSegment = JSON.parse('{{ first_segment | safe }}');
  
    const video = document.getElementById("myVideo"); // élément vidéo HTML
    const segmentsList = document.getElementById("segmentsList"); // conteneur <ul> de la liste des segments
  
    let currentSegmentIndex = 0; // index actuel du segment joué
    let showSegments = true;     // indicateur si on joue en mode segment ou complet
  
    // =======================
    //  LECTURE D'UN SEGMENT
    // =======================
  
    /**
     * Joue un segment vidéo donné par son index dans la liste `segments`
     * @param {number} index - Index du segment à lire
     */
    function playSegment(index) {
      if (segments.length === 0) return;
  
      currentSegmentIndex = index;
      const { start, end } = segments[index]; // extrait les temps en ms
  
      video.currentTime = start / 1000; // convertit ms → s
      video.play();
  
      /**
       * Arrête la vidéo à la fin du segment
       * Utilise un listener temporaire retiré dès que le segment se termine
       */
      video.addEventListener("timeupdate", function onTimeUpdate() {
        if (video.currentTime >= end / 1000) {
          video.pause();
          video.removeEventListener("timeupdate", onTimeUpdate);
        }
      });
    }
  
    // =======================
    //  LECTURE INITIALE
    // =======================
  
    // Si `firstSegment` est défini, on lance automatiquement le 1er segment
    if (firstSegment) {
      playSegment(0);
    }
  
    // =======================
    //  CONTRÔLES DE NAVIGATION
    // =======================
  
    // Bouton "Suivant" → Joue le segment suivant
    document.getElementById("btnNext").addEventListener("click", function () {
      if (currentSegmentIndex < segments.length - 1) {
        playSegment(currentSegmentIndex + 1);
      }
    });
  
    // Bouton "Précédent" → Joue le segment précédent
    document.getElementById("btnPrev").addEventListener("click", function () {
      if (currentSegmentIndex > 0) {
        playSegment(currentSegmentIndex - 1);
      }
    });
  
    // Bouton "Lecture complète" → Joue toute la vidéo sans découpage
    document.getElementById("btnFull").addEventListener("click", function () {
      video.currentTime = 0;
      video.play();
      showSegments = false;
    });
  
    // Bouton "Revenir aux segments" → Joue depuis le premier segment
    document.getElementById("btnSegments").addEventListener("click", function () {
      if (segments.length > 0) {
        playSegment(0);
      }
    });
  
    // =======================
    //  LISTE CLIQUABLE DES SEGMENTS
    // =======================
  
    /**
     * Affiche dynamiquement chaque segment dans une <ul>
     * Chaque élément est cliquable pour jouer le segment correspondant
     */
    segments.forEach((seg, index) => {
      const li = document.createElement("li");
      li.textContent = `Segment ${index + 1} : ${seg.start / 1000}s - ${seg.end / 1000}s`;
      li.addEventListener("click", () => playSegment(index));
      segmentsList.appendChild(li);
    });
  
    // =======================
    //  AFFICHAGE DU SQUELETTE 3D
    // =======================
  
    /**
     * Envoie une requête POST à /generate_skeleton
     * Reçoit une image du squelette en réponse et l'affiche sous la vidéo
     */
    document.getElementById("plot-btn").addEventListener("click", function () {
      alert("Affichage du squelette 3D en cours...");
  
      fetch("/generate_skeleton", { method: "POST" })
        .then(response => response.blob()) // On récupère un blob image (PNG ou autre)
        .then(blob => {
          const url = URL.createObjectURL(blob); // Crée une URL temporaire pour l’image
          const img = document.createElement("img");
          img.src = url;
          img.alt = "Squelette 3D";
          img.style.width = "100%";
          img.style.marginTop = "10px";
  
          const container = document.getElementById("skeleton-container");
          container.appendChild(img);
        })
        .catch(error => console.error("Erreur lors de la récupération du squelette :", error));
    });
  });
  