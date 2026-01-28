// static/js/balance-actions.js

$(document).ready(function() {
    $('#form-pay-debt').submit(function(e) {
        e.preventDefault();

        const userId = $('#payToUser').val();
        const amount = $('#payAmount').val();
        
        if (!userId) {
            alert('Lütfən bir istifadəçi seçin');
            return;
        }

        if (!amount || amount <= 0) {
            alert('Lütfən düzgün məbləğ daxil edin');
            return;
        }

        const payload = {
            title: "Borcun qaytarılması 💸",
            amount: amount,
            split_with: [parseInt(userId)],
            is_payment: true
        };

        const $submitBtn = $('#btn-submit-payment');
        const originalBtnHtml = $submitBtn.html();

        $submitBtn.prop('disabled', true).addClass('opacity-70 cursor-not-allowed');
        $submitBtn.html('<span>Gözləyin...</span>');

        $.ajax({
            url: '/api/add-expense/', 
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(payload),
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            success: function(response) {
                // Səhifəni yeniləyirik ki, balanslar tam düzgün görünsün
                window.location.reload();
            },
            error: function(xhr) {
                $submitBtn.prop('disabled', false).removeClass('opacity-70 cursor-not-allowed');
                $submitBtn.html(originalBtnHtml);
                alert('Xəta: ' + (xhr.responseJSON ? xhr.responseJSON.message : 'Ödəniş qeydə alınmadı'));
            }
        });
    });
});
