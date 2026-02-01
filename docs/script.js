document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggle-lang');
    const body = document.body;
    const html = document.documentElement;
    const metaDescription = document.querySelector('meta[name="description"]');
    const ogDescription = document.querySelector('meta[property="og:description"]');
    const twitterDescription = document.querySelector('meta[name="twitter:description"]');

    const descriptions = {
        en: "CAFFEE Editor: A lightweight, modern, and extensible terminal text editor for Python.",
        ja: "ターミナルで動作する、軽量でモダンなPython製テキストエディタ。"
    };

    toggleBtn.addEventListener('click', () => {
        if (body.classList.contains('lang-en')) {
            body.classList.remove('lang-en');
            body.classList.add('lang-ja');
            toggleBtn.textContent = 'English';
            html.lang = 'ja';
            if (metaDescription) metaDescription.content = descriptions.ja;
            if (ogDescription) ogDescription.content = descriptions.ja;
            if (twitterDescription) twitterDescription.content = descriptions.ja;
        } else {
            body.classList.remove('lang-ja');
            body.classList.add('lang-en');
            toggleBtn.textContent = '日本語';
            html.lang = 'en';
            if (metaDescription) metaDescription.content = descriptions.en;
            if (ogDescription) ogDescription.content = descriptions.en;
            if (twitterDescription) twitterDescription.content = descriptions.en;
        }
    });
});
