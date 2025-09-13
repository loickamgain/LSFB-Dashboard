// =============================================================
// SCRIPT DE STATISTIQUES LSFB
// Visualisations dynamiques (top glosses/sous-titres) et statistiques globales
// =============================================================

document.addEventListener('DOMContentLoaded', () => {

  // =======================
  // FONCTIONS UTILITAIRES
  // =======================

  /**
   * Crée un élément <li> à insérer dans une liste, avec du HTML fourni
   * @param {string} htmlContent - Contenu HTML à afficher dans la liste
   * @returns {HTMLElement} - Élément <li> à insérer dans le DOM
   */
  function createListItem(htmlContent) {
    const li = document.createElement('li');
    li.innerHTML = htmlContent;
    return li;
  }

  /**
   * Affiche un message dans un conteneur lorsqu'aucun résultat n'est trouvé
   * @param {HTMLElement} container - Élément DOM cible
   */
  function displayNoResults(container) {
    container.innerHTML = '<li class="text-red-500">Aucun résultat trouvé</li>';
  }

  /**
   * Affiche un message d'information ou de consigne dans un conteneur donné
   * @param {HTMLElement} container - Élément DOM cible
   * @param {string} message - Texte à afficher
   */
  function displayPromptMessage(container, message) {
    container.innerHTML = `<li class="text-gray-500 italic">${message}</li>`;
  }

  // =======================
  // STATS GÉNÉRALES
  // =======================

  /**
   * Appel API vers /stats/general pour afficher :
   * - total des clips, glosses, signers (CONT et ISOL)
   * - durées moyennes, clips/gloss, gloss/vidéo, phrases/vidéo
   */
  fetch('/stats/general')
    .then(res => res.json())
    .then(data => {
      // Remplissage des champs HTML via leur ID
      document.getElementById('total_clips_cont').textContent = data.total_clips_cont ?? 'N/A';
      document.getElementById('total_clips_isol').textContent = data.total_clips_isol ?? 'N/A';
      document.getElementById('total_glosses_cont').textContent = data.total_glosses_cont ?? 'N/A';
      document.getElementById('total_glosses_isol').textContent = data.total_glosses_isol ?? 'N/A';
      document.getElementById('total_signers_cont').textContent = data.total_signers_cont ?? 'N/A';
      document.getElementById('total_signers_isol').textContent = data.total_signers_isol ?? 'N/A';
      document.getElementById('avg_clip_duration_cont').textContent = data.avg_clip_duration_cont?.toFixed(2) ?? 'N/A';
      document.getElementById('avg_clip_duration_isol').textContent = data.avg_clip_duration_isol?.toFixed(2) ?? 'N/A';
      document.getElementById('avg_clips_per_gloss_cont').textContent = data.avg_clips_per_gloss_cont ?? 'N/A';
      document.getElementById('avg_clips_per_gloss_isol').textContent = data.avg_clips_per_gloss_isol ?? 'N/A';
      document.getElementById('avg_glosses_per_video_cont').textContent = data.avg_glosses_per_video_cont ?? 'N/A';
      document.getElementById('avg_glosses_per_video_isol').textContent = data.avg_glosses_per_video_isol ?? 'N/A';
      document.getElementById('avg_phrases_per_video_cont').textContent = data.avg_phrases_per_video_cont ?? 'N/A';
    })
    .catch(err => console.error('Erreur stats générales:', err));

  // =======================
  // INFOS VIDÉOS
  // =======================

  let videosData = {};  // Stockage local des données pour filtrage client

  /**
   * Récupère les métadonnées des vidéos (instance_id, signer_id, etc.)
   */
  fetch('/stats/videos/info')
    .then(res => res.json())
    .then(data => videosData = data)
    .catch(err => console.error('Erreur infos vidéos:', err));

  /**
   * Gestion du bouton de recherche d’une vidéo via son identifiant
   */
  document.getElementById('searchVideoBtn').addEventListener('click', () => {
    const container = document.getElementById('videos_info');
    const defaultMsg = document.getElementById('videoDefaultMessage');
    if (defaultMsg) defaultMsg.remove();

    const searchTerm = document.getElementById('videoSearch').value.trim().toLowerCase();
    if (!searchTerm) {
      displayPromptMessage(container, 'Tapez un identifiant de vidéo pour lancer la recherche.');
      return;
    }

    // Filtrage partiel par instance_id
    const filtered = {};
    for (const [instanceId, info] of Object.entries(videosData)) {
      if (instanceId.toLowerCase().includes(searchTerm)) {
        filtered[instanceId] = info;
      }
    }

    container.innerHTML = '';
    if (Object.keys(filtered).length === 0) {
      displayNoResults(container);
    } else {
      Object.entries(filtered).forEach(([instanceId, info]) => {
        const html = `
          <strong>Vidéo :</strong> ${instanceId}<br>
          <strong>signer_id :</strong> ${info.signer_id} |
          <strong>session_id :</strong> ${info.session_id} |
          <strong>task_id :</strong> ${info.task_id} |
          <strong>n_frames :</strong> ${info.n_frames} |
          <strong>n_signs :</strong> ${info.n_signs}
        `;
        container.appendChild(createListItem(html));
      });
    }
  });

  // =======================
  // FRÉQUENCE DES GLOSSES
  // =======================

  let glossFrequencyData = {};

  /**
   * Appel à /stats/glosses/frequency
   * Permet une recherche dynamique par terme dans les glosses
   */
  fetch('/stats/glosses/frequency')
    .then(res => res.json())
    .then(data => glossFrequencyData = data)
    .catch(err => console.error('Erreur fréquence des glosses:', err));

  document.getElementById('searchGlossBtn').addEventListener('click', () => {
    const container = document.getElementById('gloss_frequency');
    const defaultMsg = document.getElementById('glossDefaultMessage');
    if (defaultMsg) defaultMsg.remove();

    const searchTerm = document.getElementById('glossSearch').value.trim().toLowerCase();
    if (!searchTerm) {
      displayPromptMessage(container, 'Tapez un terme pour lancer la recherche.');
      return;
    }

    const filtered = {};
    for (const [gloss, freq] of Object.entries(glossFrequencyData)) {
      if (gloss.toLowerCase().includes(searchTerm)) {
        filtered[gloss] = freq;
      }
    }

    container.innerHTML = '';
    if (Object.keys(filtered).length === 0) {
      displayNoResults(container);
    } else {
      Object.entries(filtered).forEach(([gloss, freq]) => {
        container.appendChild(createListItem(`${gloss}: ${freq}`));
      });
    }
  });

  // =======================
  // VARIABILITÉ SIGNERS
  // =======================

  let signersVariabilityData = {};

  /**
   * Appel API vers /stats/signers/variability
   * Retourne le nombre de glosses uniques par signer
   */
  fetch('/stats/signers/variability')
    .then(res => res.json())
    .then(data => signersVariabilityData = data)
    .catch(err => console.error('Erreur variabilité des signers:', err));

  document.getElementById('searchSignerBtn').addEventListener('click', () => {
    const container = document.getElementById('signers_variability');
    const defaultMsg = document.getElementById('signersDefaultMessage');
    if (defaultMsg) defaultMsg.remove();

    const searchTerm = document.getElementById('signerSearch').value.trim();
    if (!searchTerm) {
      displayPromptMessage(container, 'Tapez un identifiant signer pour lancer la recherche.');
      return;
    }

    const filtered = Object.entries(signersVariabilityData)
      .filter(([signer]) => signer === searchTerm);

    container.innerHTML = '';
    if (filtered.length === 0) {
      displayNoResults(container);
    } else {
      filtered.forEach(([signer, count]) => {
        container.appendChild(createListItem(`Signer ${signer} : ${count} glosses uniques`));
      });
    }
  });

  // =======================
  // DISTRIBUTION DES POSES
  // =======================

  fetch('/stats/poses/distribution')
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById('poses_distribution');
      if (Object.keys(data).length === 0) {
        displayNoResults(container);
      } else {
        Object.entries(data).forEach(([part, count]) => {
          container.appendChild(createListItem(`${part}: ${count}`));
        });
      }
    })
    .catch(err => console.error('Erreur distribution des poses:', err));

  // =======================
  // HISTOGRAMME GLOSSES DYNAMIQUE
  // =======================

  function fetchGlossHistogram(top = 10) {
    console.assert(top >= 5 && top <= 20, "`top` doit être compris entre 5 et 20");
    fetch(`/stats/visualizations/histogram?top=${top}`)
      .then(res => res.json())
      .then(data => {
        const glosses = Object.keys(data);
        const frequencies = Object.values(data);
        const ctx = document.getElementById('topGlossesCanvas').getContext('2d');
        if (window.topGlossesChart) window.topGlossesChart.destroy();
        window.topGlossesChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: glosses,
            datasets: [{
              label: 'Occurrences',
              data: frequencies,
              backgroundColor: 'rgba(54, 162, 235, 0.6)',
              borderColor: 'rgba(54, 162, 235, 1)',
              borderWidth: 1
            }]
          },
          options: {
            plugins: {
              title: { display: true, text: `Top ${top} glosses les plus fréquents` }
            },
            scales: {
              y: { beginAtZero: true },
              x: { title: { display: true, text: 'Glosses' } }
            }
          }
        });
      });
  }

  // =======================
  // HISTOGRAMME SOUS-TITRES DYNAMIQUE
  // =======================

  function fetchSubtitlesHistogram(top = 10) {
    console.assert(top >= 5 && top <= 20, "`top` doit être compris entre 5 et 20");
    fetch(`/stats/visualizations/top_subtitles?top=${top}`)
      .then(res => res.json())
      .then(data => {
        const subtitles = Object.keys(data);
        const frequencies = Object.values(data);
        const ctx = document.getElementById('topSubtitlesCanvas').getContext('2d');
        if (window.topSubtitlesChart) window.topSubtitlesChart.destroy();
        window.topSubtitlesChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: subtitles,
            datasets: [{
              label: 'Occurrences',
              data: frequencies,
              backgroundColor: 'rgba(255, 99, 132, 0.6)',
              borderColor: 'rgba(255, 99, 132, 1)',
              borderWidth: 1
            }]
          },
          options: {
            plugins: {
              title: { display: true, text: `Top ${top} sous-titres les plus utilisés` }
            },
            scales: {
              y: { beginAtZero: true },
              x: { title: { display: true, text: 'Sous-titres' } }
            }
          }
        });
      });
  }

  // =======================
  // INPUT DYNAMIQUE POUR TOP N
  // =======================

  function setupTopInput(id, callback) {
    const input = document.getElementById(id);
    input.addEventListener('change', () => {
      let top = parseInt(input.value);
      if (isNaN(top)) top = 10;
      top = Math.max(5, Math.min(20, top)); // Limite entre 5 et 20
      callback(top);
    });
  }

  // Initialisation des histogrammes
  fetchGlossHistogram(10);
  fetchSubtitlesHistogram(10);
  setupTopInput('topGlossesSelect', fetchGlossHistogram);
  setupTopInput('topSubtitlesSelect', fetchSubtitlesHistogram);
});
