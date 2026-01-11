$(document).ready(function() {
    // Həm təsdiq, həm ləğv düyməsi üçün tək funksiya
    $('.approve-btn, .reject-btn').on('click', function() {
        
        const btn = $(this);
        const splitId = btn.data('id');
        const actionType = btn.data('action');
        const container = $(`#action-buttons-${splitId}`);

        // Düymələri müvəqqəti söndürürük (double-click olmasın)
        container.find('button').prop('disabled', true).opacity = 0.5;

        $.ajax({
            url: `/api/approve-split/${splitId}/`,
            type: 'POST',
            data: {
                'action': actionType,
                'csrfmiddlewaretoken': '{{ csrf_token }}' // Və ya getCookie('csrftoken')
            },
            success: function(response) {
                if (response.status === 'success') {
                    // Düymələri silib yerinə status yazırıq
                    let statusHtml = '';
                    if (actionType === 'approve') {
                        statusHtml = `<div class="w-full text-center py-3 bg-green-50 text-green-600 rounded-2xl font-bold animate-pulse">
                                        <i class="fa-solid fa-check-circle mr-2"></i> Təsdiqləndi
                                      </div>`;
                    } else {
                        statusHtml = `<div class="w-full text-center py-3 bg-red-50 text-red-600 rounded-2xl font-bold">
                                        <i class="fa-solid fa-circle-xmark mr-2"></i> İmtina edildi
                                      </div>`;
                    }
                    
                    container.html(statusHtml);

                    // 2 saniyə sonra kartı tamamilə itirmək istəsən:
                    // setTimeout(() => {
                    //     $(`#split-container-${splitId}`).fadeOut(500);
                    // }, 2000);
                }
            },
            error: function(xhr) {
                alert("Xəta baş verdi: " + xhr.responseJSON.message);
                container.find('button').prop('disabled', false).opacity = 1;
            }
        });
    });
});