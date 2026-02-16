document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const recipeList = document.getElementById('recipe-list');
    let recipes = [];

    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            const context = this;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    }

    // Load search index
    fetch('search.json')
        .then(response => response.json())
        .then(data => {
            recipes = data;
        });

    searchInput.addEventListener('input', debounce((e) => {
        const term = e.target.value.toLowerCase();
        
        // Filter recipes
        const filtered = recipes.filter(recipe => 
            recipe.title.toLowerCase().includes(term)
        );

        // Render results
        recipeList.innerHTML = filtered.map(recipe => `
            <li class="recipe-card">
                <a href="recipe/${recipe.id}.html">
                    <h3>${recipe.title}</h3>
                    <span class="meta">${recipe.total_time || ''}</span>
                </a>
            </li>
        `).join('');
    }, 300));
});
