// static/js/expense-actions.js

$(document).ready(function() {
    let activeExpenseId = null;
    let pressTimer = null;

    // --- LONG PRESS HANDLER ---
    $(document).on('pointerdown', '.expense-card', function(e) {
        // Only trigger on left click or touch
        if (e.pointerType === 'mouse' && e.button !== 0) return;
        
        const $card = $(this);
        
        // If we are in edit mode, don't trigger long press
        if ($card.find('.edit-mode').is(':visible')) return;

        activeExpenseId = $card.data('expense-id');
        
        // Visual feedback
        $card.addClass('scale-[0.96] brightness-95');
        
        pressTimer = setTimeout(() => {
            // Haptic effect
            if (window.navigator.vibrate) {
                window.navigator.vibrate(50);
            }

            // Open Bottom Sheet
            $('#bottom-sheet-actions').removeClass('hidden');
            setTimeout(() => {
                $('#bottom-sheet-content').removeClass('translate-y-full').addClass('translate-y-0');
            }, 10);
            
            // Clean up visual feedback
            $card.removeClass('scale-[0.96] brightness-95');
        }, 600);
    });

    $(document).on('pointerup pointerleave', '.expense-card', function() {
        clearTimeout(pressTimer);
        $(this).removeClass('scale-[0.96] brightness-95');
    });

    $(document).on('contextmenu', '.expense-card', function(e) {
        e.preventDefault();
    });

    // --- BOTTOM SHEET ACTIONS ---
    function closeBottomSheet() {
        $('#bottom-sheet-content').removeClass('translate-y-0').addClass('translate-y-full');
        setTimeout(() => {
            $('#bottom-sheet-actions').addClass('hidden');
        }, 300);
    }

    $('#bottom-sheet-actions').click(function(e) {
        if (e.target === this) closeBottomSheet();
    });

    // --- DELETE LOGIC ---
    $('#bs-btn-delete').click(function() {
        if (!activeExpenseId) return;
        closeBottomSheet();
        setTimeout(() => {
            $('#modal-delete-confirm').removeClass('hidden');
        }, 350);
    });

    $('#btn-cancel-delete').click(function() {
        $('#modal-delete-confirm').addClass('hidden');
    });

    $('#btn-confirm-delete').click(function() {
        const idToDelete = activeExpenseId;
        if (!idToDelete) return;
        
        const $btn = $(this);
        $btn.prop('disabled', true).addClass('opacity-70 font-medium');
        $btn.text('Silinir...');

        $.ajax({
            url: `/api/delete-expense/${idToDelete}/`,
            type: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            success: function() {
                $(`.expense-card[data-expense-id="${idToDelete}"]`).fadeOut(300, function() {
                    $(this).remove();
                });
                $('#modal-delete-confirm').addClass('hidden');
            },
            error: function() {
                alert('Xəta baş verdi. Xərc silinmədi.');
            },
            complete: function() {
                $btn.prop('disabled', false).removeClass('opacity-70 font-medium');
                $btn.text('Bəli, sil');
                activeExpenseId = null;
            }
        });
    });

    // --- INLINE EDIT LOGIC ---
    $('#bs-btn-edit').click(function() {
        if (!activeExpenseId) return;
        closeBottomSheet();
        
        const $card = $(`.expense-card[data-expense-id="${activeExpenseId}"]`);
        $card.find('.display-mode').addClass('hidden');
        $card.find('.edit-mode').removeClass('hidden');

        const currentSplitIds = $card.find('.splits-container [data-user-id]').map(function() {
            return $(this).data('user-id');
        }).get();

        $card.find('.edit-user-item').each(function() {
            const uid = parseInt($(this).data('id'));
            const $item = $(this);
            const $chip = $item.find('.chip');
            const $name = $item.find('span');
            
            if (currentSplitIds.includes(uid)) {
                $(this).addClass('active-user');
                $chip.addClass('bg-indigo-600 text-white shadow-md').removeClass('bg-slate-100 text-slate-400');
                $name.addClass('text-indigo-600').removeClass('text-slate-400');
            } else {
                $(this).removeClass('active-user');
                $chip.removeClass('bg-indigo-600 text-white shadow-md').addClass('bg-slate-100 text-slate-400');
                $name.removeClass('text-indigo-600').addClass('text-slate-400');
            }
        });
    });

    $(document).on('click', '.edit-user-item', function(e) {
        e.stopPropagation();
        const $item = $(this);
        const $chip = $item.find('.chip');
        const $name = $item.find('span');
        
        $item.toggleClass('active-user');
        
        if ($item.hasClass('active-user')) {
            $chip.addClass('bg-indigo-600 text-white shadow-md').removeClass('bg-slate-100 text-slate-400');
            $name.addClass('text-indigo-600').removeClass('text-slate-400');
        } else {
            $chip.removeClass('bg-indigo-600 text-white shadow-md').addClass('bg-slate-100 text-slate-400');
            $name.removeClass('text-indigo-600').addClass('text-slate-400');
        }
    });

    $(document).on('click', '.btn-cancel-edit', function(e) {
        e.stopPropagation();
        const $card = $(this).closest('.expense-card');
        $card.find('.edit-mode').addClass('hidden');
        $card.find('.display-mode').removeClass('hidden');
    });

    $(document).on('click', '.btn-save-edit', function(e) {
        e.stopPropagation();
        const $card = $(this).closest('.expense-card');
        const expenseId = $card.data('expense-id');
        
        const newTitle = $card.find('.edit-title').val();
        const newAmount = $card.find('.edit-amount').val();
        const selectedIds = $card.find('.edit-user-item.active-user').map(function() {
            return $(this).data('id');
        }).get();

        if (selectedIds.length === 0) {
            alert('Lütfən ən azı bir nəfər seçin');
            return;
        }

        const $btn = $(this);
        $btn.prop('disabled', true).text('Gözləyin...');

        $.ajax({
            url: `/api/update-expense/${expenseId}/`,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                title: newTitle,
                amount: newAmount,
                split_with: selectedIds
            }),
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            success: function() {
                location.reload(); 
            },
            error: function() {
                alert('Xəta baş verdi');
                $btn.prop('disabled', false).text('Yadda saxla');
            }
        });
    });
});
