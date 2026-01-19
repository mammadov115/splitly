// static/js/script.js
$(document).ready(function() {
    // 0. Dinamik datanı körpüdən (window.RoomieData) alırıq
    const userNames = window.RoomieData.userNames;
    const currentUserId = window.RoomieData.currentUserId;

    // Lokal data saxlanması - Başlanğıcda yalnız özün seçilirsən
    let selectedUsers = Object.keys(userNames).map(id => parseInt(id));

    // 1. Modalı Aç
    $('#btn-open-modal').click(function() {
        $('#modal-expense').removeClass('hidden');
        resetUserSelection(); // Hər dəfə açanda təmiz başlasın
    });

    // 2. Modalı Bağla
    $('#modal-expense').click(function(e) {
        if (e.target === this) { $(this).addClass('hidden'); }
    });

    // 3. İstifadəçi seçimi (Toggle)
    $('.user-item').click(function() {
        const id = parseInt($(this).data('id'));
        const chip = $(this).find('.chip');
        const label = $(this).find('span');

        if (selectedUsers.includes(id)) {
            // Əgər ən azı 1 nəfər qalmalıdırsa, özünü çıxarmağa icazə verməyə bilərsən
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

        // 1. Düyməni dərhal yüklənmə vəziyyətinə gətir
        $submitBtn.prop('disabled', true).addClass('opacity-70 cursor-not-allowed');
        $submitBtn.html('<span>Təsdiq edilir...</span>');

        $.ajax({
            url: '/api/add-expense/', 
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(payload),
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            success: function(response) {
                // Effektin görünməsi üçün kiçik gecikmə (xüsusən localhost-da sürətli olur)
                setTimeout(function() {
                    // Dinamik hesablama
                    const amountNum = parseFloat(amountVal);
                    const perPerson = (amountNum / selectedUsers.length).toFixed(2);
                    
                    let sortedForDisplay = [...selectedUsers].sort((a, b) => {
                        if (a === currentUserId) return -1;
                        if (b === currentUserId) return 1;
                        return 0;
                    });
                    
                    let splitsHtml = '';
                    sortedForDisplay.forEach(id => {
                        const isMe = (id === currentUserId);
                        splitsHtml += `
                            <div class="flex justify-between items-center text-sm">
                                <span class="text-slate-600 flex items-center gap-2">
                                    <span class="${isMe ? 'bg-green-500 shadow-[0_0_5px_rgba(34,197,94,0.5)]' : 'bg-slate-300'} w-2 h-2 rounded-full"></span>
                                    <span class="${isMe ? 'font-bold text-indigo-600' : ''}">${isMe ? 'Sən' : (userNames[id] || 'İstifadəçi')}</span>
                                </span>
                                <span class="font-bold text-slate-700">
                                    <span>${perPerson} ₼</span>
                                    <i class="${isMe ? 'fa-check-circle text-green-500' : 'fa-circle-xmark text-slate-300'} fa-solid ml-1"></i>
                                </span>
                            </div>`;
                    });

                    const newEntryHtml = `
                        <div class="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 mb-4 transition-all animate-in slide-in-from-top duration-500">
                            <div class="flex justify-between items-start mb-4">
                                <div class="flex items-center gap-3">
                                    <div class="w-12 h-12 bg-indigo-100 rounded-2xl flex items-center justify-center text-indigo-600">
                                        <i class="fa-solid fa-receipt"></i>
                                    </div>
                                    <div>
                                        <h3 class="font-bold text-slate-800">${title}</h3>
                                        <p class="text-xs text-slate-400 font-medium">İndi</p>
                                    </div>
                                </div>
                                <div class="text-right">
                                    <span class="text-lg font-bold text-slate-800">${amountNum.toFixed(2)} AZN</span>
                                    <p class="text-[10px] text-indigo-500 font-bold uppercase">Sən ödədin</p>
                                </div>
                            </div>
                            <div class="space-y-3 bg-slate-50 rounded-2xl p-3">
                                ${splitsHtml}
                            </div>
                        </div>`;

                    $('#expenses-list').prepend(newEntryHtml);
                    $('#modal-expense').addClass('hidden');
                    $('#form-add-expense')[0].reset();
                    resetUserSelection();
                    
                    // Düyməni bərpa et
                    $submitBtn.prop('disabled', false).removeClass('opacity-70 cursor-not-allowed');
                    $submitBtn.html(originalBtnHtml);
                }, 600);
            },
            error: function(xhr) {
                // Xəta halında düyməni bərpa et
                $submitBtn.prop('disabled', false).removeClass('opacity-70 cursor-not-allowed');
                $submitBtn.html(originalBtnHtml);
                alert('Xəta: ' + (xhr.responseJSON ? xhr.responseJSON.message : 'Məlumat yadda saxlanılmadı'));
            }
        });
    });

    // Köməkçi Funksiyalar
    function resetUserSelection() {
        // Hamısını seçili etmək istəyirsənsə: selectedUsers = Object.keys(userNames).map(Number);
        // Ancaq özünü seçili etmək istəyirsənsə:
        selectedUsers = Object.keys(userNames).map(id => parseInt(id));
        
        $('.user-item').each(function() {
            const chip = $(this).find('.chip');
            const label = $(this).find('span');
            
            // Hamısını aktiv rəngə boyayırıq
            chip.addClass('bg-indigo-600 text-white shadow-md').removeClass('bg-slate-100 text-slate-500');
            label.addClass('text-indigo-600').removeClass('text-slate-400');
        });
        }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});














// // script.js
// $(document).ready(function() {
//     // Lokal data saxlanması
//     let selectedUsers = [1, 2, 3];
//     const userNames = { 1: 'Sən', 2: 'Elvin', 3: 'Orxan' };

//     // 1. Modalı Aç
//     $('#btn-open-modal').click(function() {
//         $('#modal-expense').removeClass('hidden');
//     });

//     // 2. Modalı Bağla (Kənara klik edəndə)
//     $('#modal-expense').click(function(e) {
//         if (e.target === this) {
//             $(this).addClass('hidden');
//         }
//     });

//     // 3. İstifadəçi seçimi (Toggle)
//     $('.user-item').click(function() {
//         const id = parseInt($(this).data('id'));
//         const chip = $(this).find('.chip');
//         const label = $(this).find('span');

//         if (selectedUsers.includes(id)) {
//             selectedUsers = selectedUsers.filter(u => u !== id);
//             chip.removeClass('bg-indigo-600 text-white shadow-md').addClass('bg-slate-100 text-slate-500');
//             label.removeClass('text-indigo-600').addClass('text-slate-400');
//         } else {
//             selectedUsers.push(id);
//             chip.addClass('bg-indigo-600 text-white shadow-md').removeClass('bg-slate-100 text-slate-500');
//             label.addClass('text-indigo-600').removeClass('text-slate-400');
//         }
//     });

//     // 4. Form Submit - AJAX ilə View-a göndərmək
//     $('#form-add-expense').submit(function(e) {
//         e.preventDefault();

//         // Formdan dataları götürürük
//         const title = $('#newTitle').val();
//         const amountVal = $('#newAmount').val();
//         const amount = parseFloat(amountVal).toFixed(2);
        
//         // Əgər heç kim seçilməyibsə
//         if (selectedUsers.length === 0) {
//             alert('Lütfən ən azı bir nəfər seçin');
//             return;
//         }

//         // View-un gözlədiyi JSON formatında payload yaradırıq
//         const payload = {
//             title: title,
//             amount: amountVal,
//             split_with: selectedUsers // Seçilmiş ID-lər siyahısı
//         };

//         // AJAX Sorğusu
//         $.ajax({
//             url: '/api/add-expense/', // Sənin urls.py-dakı yolun (məs: path('add-expense-ajax/', views.add_expense_ajax, name='add_expense_ajax'))
//             type: 'POST',
//             contentType: 'application/json',
//             data: JSON.stringify(payload),
//             headers: {
//                 'X-CSRFToken': getCookie('csrftoken') // CSRF Token mütləqdir
//             },
//             success: function(response) {
//                 // Serverdən 200 statusu gəldikdə UI-da siyahıya əlavə edirik
//                 const perPerson = (amount / selectedUsers.length).toFixed(2);
//                 let splitsHtml = '';
                
//                 selectedUsers.forEach(id => {
//                     splitsHtml += `
//                         <div class="flex justify-between items-center text-sm">
//                             <span class="text-slate-600 flex items-center gap-2">
//                                 <span class="${id === 1 ? 'bg-green-500' : 'bg-slate-300'} w-2 h-2 rounded-full"></span>
//                                 <span>${userNames[id] || 'İstifadəçi'}</span>
//                             </span>
//                             <span class="font-bold text-slate-700">
//                                 <span>${perPerson} ₼</span>
//                                 <i class="${id === 1 ? 'fa-check-circle text-green-500' : 'fa-circle-xmark text-slate-300'} fa-solid ml-1"></i>
//                             </span>
//                         </div>`;
//                 });

//                 const newEntryHtml = `
//                     <div class="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 mb-4 transition-all animate-in slide-in-from-top duration-500">
//                         <div class="flex justify-between items-start mb-4">
//                             <div class="flex items-center gap-3">
//                                 <div class="w-12 h-12 bg-indigo-100 rounded-2xl flex items-center justify-center text-indigo-600">
//                                     <i class="fa-solid fa-receipt"></i>
//                                 </div>
//                                 <div>
//                                     <h3 class="font-bold text-slate-800">${title}</h3>
//                                     <p class="text-xs text-slate-400 font-medium">İndi</p>
//                                 </div>
//                             </div>
//                             <div class="text-right">
//                                 <span class="text-lg font-bold text-slate-800">${amount} AZN</span>
//                                 <p class="text-[10px] text-indigo-500 font-bold uppercase">Sən ödədin</p>
//                             </div>
//                         </div>
//                         <div class="space-y-3 bg-slate-50 rounded-2xl p-3">
//                             ${splitsHtml}
//                         </div>
//                     </div>`;

//                 // UI Yeniləmələri
//                 $('#expenses-list').prepend(newEntryHtml);
//                 $('#modal-expense').addClass('hidden');
//                 $('#form-add-expense')[0].reset();
                
//                 // Seçimləri sıfırla
//                 resetUserSelection();
//             },
//             error: function(xhr) {
//                 console.error("Xəta:", xhr.responseText);
//                 alert('Xəta baş verdi, məlumat yadda saxlanılmadı.');
//             }
//         });
//     });

//     // Django üçün CSRF Token funksiyası
//     function getCookie(name) {
//         let cookieValue = null;
//         if (document.cookie && document.cookie !== '') {
//             const cookies = document.cookie.split(';');
//             for (let i = 0; i < cookies.length; i++) {
//                 const cookie = cookies[i].trim();
//                 if (cookie.substring(0, name.length + 1) === (name + '=')) {
//                     cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//                     break;
//                 }
//             }
//         }
//         return cookieValue;
//     }

//     // User seçimlərini sıfırlamaq üçün köməkçi funksiya
//     function resetUserSelection() {
//         selectedUsers = [1, 2, 3]; // Default hamı
//         $('.user-item .chip').addClass('bg-indigo-600 text-white shadow-md').removeClass('bg-slate-100 text-slate-500');
//         $('.user-item span').addClass('text-indigo-600').removeClass('text-slate-400');
//     }
// });