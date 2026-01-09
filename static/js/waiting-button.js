$(document).on('click', '.settle-btn', function(e) {
    e.preventDefault();
    let btn = $(this);
    let splitId = btn.data('id');
    
    // Düyməni dərhal "Loading" vəziyyətinə gətiririk (Reactive hissə)
    btn.prop('disabled', true).html('<i class="fa-solid fa-spinner fa-spin"></i> İşlənir...');

    $.ajax({
        url: `/settle-request/${splitId}/`, // URL-i urls.py-da təyin etdiyin kimi yaz
        method: 'POST',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}' // Django CSRF qoruması
        },
        success: function(response) {
            if (response.status === 'success') {
                // UI-da düyməni "Təsdiq gözlənilir" statusuna çeviririk
                btn.removeClass('bg-indigo-600 text-white settle-btn')
                   .addClass('bg-amber-100 text-amber-600 border border-amber-200')
                   .html('<i class="fa-solid fa-hourglass-half animate-pulse"></i> Təsdiq gözlənilir...');
            }
        },
        error: function() {
            alert('Xəta baş verdi!');
            btn.prop('disabled', false).html('<i class="fa-solid fa-wallet"></i> İndi Ödə');
        }
    });
});