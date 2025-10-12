const form = document.getElementById('shortenForm');
const submitBtn = document.getElementById('submitBtn');
const result = document.getElementById('result');
const error = document.getElementById('error');
const shortUrlInput = document.getElementById('shortUrl');
const copyBtn = document.getElementById('copyBtn');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const url = document.getElementById('url').value;
    
    // Esconder resultados anteriores
    result.classList.remove('show');
    error.classList.remove('show');
    
    // Mostrar loading
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="loading"></span>';
    
    try {
        const response = await fetch('/shorten', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });
        
        if (!response.ok) {
            throw new Error('Erro ao encurtar URL');
        }
        
        const data = await response.json();
        
        // Mostrar resultado
        shortUrlInput.value = data.short_url;
        document.getElementById('clicks').textContent = data.clicks;
        document.getElementById('shortCode').textContent = data.short_code;
        result.classList.add('show');
        
    } catch (err) {
        error.textContent = '❌ ' + err.message;
        error.classList.add('show');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Encurtar URL';
    }
});

// Copiar URL
copyBtn.addEventListener('click', async () => {
    try {
        await navigator.clipboard.writeText(shortUrlInput.value);
        copyBtn.textContent = '✓ Copiado!';
        copyBtn.classList.add('copied');
        
        setTimeout(() => {
            copyBtn.textContent = 'Copiar';
            copyBtn.classList.remove('copied');
        }, 2000);
    } catch (err) {
        alert('Erro ao copiar');
    }
});