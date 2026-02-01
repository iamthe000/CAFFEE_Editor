document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggle-lang');
    const body = document.body;

    toggleBtn.addEventListener('click', () => {
        if (body.classList.contains('lang-en')) {
            body.classList.remove('lang-en');
            body.classList.add('lang-ja');
            toggleBtn.textContent = 'English';
        } else {
            body.classList.remove('lang-ja');
            body.classList.add('lang-en');
            toggleBtn.textContent = '日本語';
        }
    });
});
