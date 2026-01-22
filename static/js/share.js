// static/js/share.js

$(document).ready(function() {
    // --- WHATSAPP SHARE LOGIC ---
    $('#btn-whatsapp-share').click(function() {
        const data = JSON.parse(localStorage.getItem('recentExpense'));
        if (!data) return;

        const message = 
            `*Yeni xərc əlavə edildi!* 💸\n\n` +
            `🛒 *Məhsul:* ${data.title}\n` +
            `💰 *Cəmi:* ${data.total} ₼\n` +
            `👥 *Hərəyə:* ${data.perPerson} ₼\n\n` +
            `Xərcin detallarına bax:\n\n` +
            `https://xercler.pythonanywhere.com/`;

        const waUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(message)}`;
        window.open(waUrl, '_blank');
        location.reload(); 
    });

    $('#btn-skip-share').click(function() {
        location.reload();
    });
});
