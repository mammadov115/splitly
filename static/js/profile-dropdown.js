$(document).ready(function() {
    const $profileBtn = $('#profile-btn');
    const $dropdownMenu = $('#dropdown-menu');

    // Düyməyə klikləyəndə aç/bağla
    $profileBtn.on('click', function(e) {
        e.stopPropagation(); // Klik hadisəsinin yuxarı sızmasının qarşısını alırıq
        $dropdownMenu.toggleClass('hidden');
    });

    // Səhifənin istənilən yerinə basanda dropdown-u bağla
    $(document).on('click', function(e) {
        if (!$(e.target).closest('#profile-dropdown-container').length) {
            $dropdownMenu.addClass('hidden');
        }
    });
});