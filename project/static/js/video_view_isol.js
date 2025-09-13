document.getElementById("plot-btn").addEventListener("click", function() {
    alert("Affichage du squelette 3D en cours...");
    fetch("/generate_skeleton", { method: "POST" })
        .then(response => response.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
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