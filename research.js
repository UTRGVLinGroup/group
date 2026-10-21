// Store viewer instances to avoid re-initializing 
const viewers = {};

function openModal(id) {
    const modal = document.getElementById(id);
    modal.style.display = "block";
    document.body.classList.add('no-scroll');

    // Wait for the browser to render the 'display: block' change
    requestAnimationFrame(() => {
        const containers = modal.querySelectorAll('.mol-container');

        containers.forEach(container => {
            const containerId = container.id;
            
            // Initialize if not already created
            if (!viewers[containerId]) {
                const cid = container.getAttribute('data-cid');
                if (!cid) return;

                viewers[containerId] = $3Dmol.createViewer(container, {
                    backgroundColor: 'white'
                });

                $3Dmol.download("cid:" + cid, viewers[containerId], {}, function() {
                    viewers[containerId].setStyle({}, {stick: {radius: 0.2, colorscheme: 'Jmol'}});
                    viewers[containerId].zoomTo();
                    viewers[containerId].render();
                });
            } else {
                // Resize if it already exists
                viewers[containerId].resize();
                viewers[containerId].render();
            }
        });
    });
}

function closeModal(id) {
    document.getElementById(id).style.display = "none";
    document.body.classList.remove('no-scroll');
}

window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = "none";
        document.body.classList.remove('no-scroll');
    }
};