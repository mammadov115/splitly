// static/js/expense-add.js

$(document).ready(function() {
    const userNames = window.RoomieData.userNames;
    const currentUserId = window.RoomieData.currentUserId;
    let selectedUsers = Object.keys(userNames).map(id => parseInt(id));

    // 1. Open Modal
    $('#btn-open-modal').click(function() {
        $('#modal-expense').removeClass('hidden');
        selectedUsers = resetUserSelection('#user-selector', userNames);
    });

    // 2. Close Modal
    $('#modal-expense').click(function(e) {
        if (e.target === this) { $(this).addClass('hidden'); }
    });

    // 3. User Selection (Toggle)
    $(document).on('click', '.user-item', function() {
        const id = parseInt($(this).data('id'));
        const chip = $(this).find('.chip');
        const label = $(this).find('span');

        if (selectedUsers.includes(id)) {
            selectedUsers = selectedUsers.filter(u => u !== id);
            chip.removeClass('bg-indigo-600 text-white shadow-md').addClass('bg-slate-100 text-slate-500');
            label.removeClass('text-indigo-600').addClass('text-slate-400');
        } else {
            selectedUsers.push(id);
            chip.addClass('bg-indigo-600 text-white shadow-md').removeClass('bg-slate-100 text-slate-500');
            label.addClass('text-indigo-600').removeClass('text-slate-400');
        }
    });

    // 4. Form Submit
    $('#form-add-expense').submit(function(e) {
        e.preventDefault();

        const title = $('#newTitle').val();
        const amountVal = $('#newAmount').val();
        
        if (selectedUsers.length === 0) {
            alert('Lütfən ən azı bir nəfər seçin');
            return;
        }

        const payload = {
            title: title,
            amount: amountVal,
            split_with: selectedUsers
        };

        const $submitBtn = $('#btn-submit-expense');
        const originalBtnHtml = $submitBtn.html();

        $submitBtn.prop('disabled', true).addClass('opacity-70 cursor-not-allowed');
        $submitBtn.html('<span>Təsdiq edilir...</span>');

        $.ajax({
            url: '/api/add-expense/', 
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(payload),
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            success: function(response) {
                setTimeout(function() {
                    const amountNum = parseFloat(amountVal);
                    const perPerson = (amountNum / selectedUsers.length).toFixed(2);
                    
                    // Save for WhatsApp Share
                    localStorage.setItem('recentExpense', JSON.stringify({
                        title: title,
                        total: amountNum.toFixed(2),
                        count: selectedUsers.length,
                        perPerson: perPerson
                    }));

                    // Show success modal (Share Modal)
                    $('#modal-expense').addClass('hidden');
                    $('#modal-share-success').removeClass('hidden');
                    setTimeout(() => {
                        $('#share-modal-content').removeClass('scale-95 opacity-0').addClass('scale-100 opacity-100');
                    }, 10);

                    $('#form-add-expense')[0].reset();
                    selectedUsers = resetUserSelection('#user-selector', userNames);
                    
                    $submitBtn.prop('disabled', false).removeClass('opacity-70 cursor-not-allowed');
                    $submitBtn.html(originalBtnHtml);
                }, 600);
            },
            error: function(xhr) {
                $submitBtn.prop('disabled', false).removeClass('opacity-70 cursor-not-allowed');
                $submitBtn.html(originalBtnHtml);
                alert('Xəta: ' + (xhr.responseJSON ? xhr.responseJSON.message : 'Məlumat yadda saxlanılmadı'));
            }
        });
    });
});
