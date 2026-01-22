// static/js/utils.js

/**
 * Get CSRF Token from cookies
 */
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

/**
 * Reset User Selection UI in the Add Expense modal
 */
function resetUserSelection(userSelectorId, userNames) {
    const $selector = $(userSelectorId);
    $selector.find('.user-item').each(function() {
        const chip = $(this).find('.chip');
        const label = $(this).find('span');
        
        chip.addClass('bg-indigo-600 text-white shadow-md').removeClass('bg-slate-100 text-slate-500');
        label.addClass('text-indigo-600').removeClass('text-slate-400');
    });
    
    // Return all user IDs as selected by default
    return Object.keys(userNames).map(id => parseInt(id));
}
