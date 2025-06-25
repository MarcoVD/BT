document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('input[name="q"]');
    const resultsContainer = document.getElementById('vacantes-container');
    let timeout;

    searchInput.addEventListener('input', function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            const query = this.value.trim();

            fetch(`/ajax/buscar-vacantes/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    resultsContainer.innerHTML = data.html;
                });
        }, 300);
    });
});