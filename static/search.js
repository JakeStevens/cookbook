document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const recipeList = document.getElementById('recipe-list');
    let recipes = [];

    // Load search index
    fetch('search.json')
        .then(response => response.json())
        .then(data => {
            recipes = data;
        });

    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        
        // Filter recipes
        const filtered = recipes.filter(recipe => 
            recipe.title.toLowerCase().includes(term)
        );

        // Render results
        recipeList.innerHTML = '';
        filtered.forEach(recipe => {
            const li = document.createElement('li');
            li.className = 'recipe-card';

            const a = document.createElement('a');
            a.href = `recipe/${recipe.id}.html`;

            const h3 = document.createElement('h3');
            h3.textContent = recipe.title;

            const span = document.createElement('span');
            span.className = 'meta';
            span.textContent = recipe.total_time || '';

            a.appendChild(h3);
            a.appendChild(span);
            li.appendChild(a);
            recipeList.appendChild(li);
        });
    });
});
