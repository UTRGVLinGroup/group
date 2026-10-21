document.addEventListener('DOMContentLoaded', async () => {
    const pubList = document.getElementById('publications-list');
    const searchInput = document.getElementById('pubSearch');
    const filterBtns = document.querySelectorAll('.filter-btn');
    
    let allData = [];

    try {
        // Fetch both files
        const [pubRes, manRes] = await Promise.all([
            fetch('publications.json').catch(() => ({ json: () => [] })),
            fetch('manuscripts.json').catch(() => ({ json: () => [] }))
        ]);

        const published = await pubRes.json();
        const manuscripts = await manRes.json();

        // Merge and SORT by year (Newest first)
        allData = [...published, ...manuscripts].sort((a, b) => {
            const yearA = parseInt(a.year) || 0;
            const yearB = parseInt(b.year) || 0;
            return yearB - yearA; // High year to Low year
        });

        renderPublications(allData);
    } catch (err) {
        pubList.innerHTML = `<p>Error loading publications. Ensure publications.json exists.</p>`;
        console.error(err);
    }

    function renderPublications(data) {
        if (data.length === 0) {
            pubList.innerHTML = `<p>No matches found.</p>`;
            return;
        }

        pubList.innerHTML = data.map(pub => `
            <div class="pub-card">
                <div class="pub-year-badge">${pub.year}</div>
                <h3>${pub.title}</h3>
                <p class="authors">${pub.authors}</p>
                <p class="journal-info"><em>${pub.journal}</em></p>
                <div class="pub-actions">
                    <a href="${pub.link}" target="_blank" class="btn view-link">View Paper</a>
                    <button class="btn cite-btn" onclick="handleCite(this, \`${pub.citation}\`)">Cite Paper</button>
                </div>
            </div>
        `).join('');
    }

    // Search logic
    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const filtered = allData.filter(p => 
            p.title.toLowerCase().includes(term) || 
            p.authors.toLowerCase().includes(term) ||
            p.year.toString().includes(term)
        );
        renderPublications(filtered);
    });

    // Filter logic
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelector('.filter-btn.active').classList.remove('active');
            btn.classList.add('active');
            const filter = btn.dataset.filter;
            const filtered = filter === 'all' ? allData : allData.filter(p => p.type === filter);
            renderPublications(filtered);
        });
    });
});

function handleCite(btn, citationText) {
    navigator.clipboard.writeText(citationText).then(() => {
        const originalText = btn.innerHTML;
        btn.innerHTML = "✓ Copied";
        btn.classList.add('success');
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.classList.remove('success');
        }, 2000);
    });
}