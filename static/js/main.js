$('#addfield').off('click').on('click',function(event){
    var x = event.pageX;
    var y = event.pageY;

    $('#addFieldForm').css({
        'top': y + 'px',
        'left': x + 'px',
        'display': 'block'
    });
    
    event.stopPropagation(); 
});

$(document).ready(function(){
    // Hide the form container when clicking outside of it
    $(document).on('click', function(event) {
        if (!$(event.target).closest('#addFieldForm, #addfield').length) {
            $('#addFieldForm').hide();
        }
    });

    // Prevent form container click from hiding it
    $('#addFieldForm').on('click', function(event) {
        event.stopPropagation(); // Prevent the click from propagating to the document
    });


    // ================================ sidebar control ================================

    const sidebar = document.getElementById('sidebar');
    const menuIcon = document.getElementById('menu-icon');
    const mainContent = document.getElementById('main-content-wrapper');
    const closeBtn = document.getElementById('close-btn');

    window.onload = () => {
        
        const sidebarOpen = localStorage.getItem('sidebarOpen') === 'true';
        if (sidebarOpen) {
            sidebar.classList.remove('-translate-x-full');
            sidebar.classList.add('translate-x-0');
            mainContent.classList.add('ml-48');
            mainContent.classList.remove('ml-0');
            menuIcon.classList.add('hidden');
        } else {
            sidebar.classList.add('-translate-x-full');
            sidebar.classList.remove('translate-x-0');
            mainContent.classList.remove('ml-48');
            mainContent.classList.add('ml-0');
            menuIcon.classList.remove('hidden');
        }
    
    };

    // open sidebar
    if (!menuIcon.hasEventListener) {
        menuIcon.addEventListener('click', function () {
            sidebar.classList.toggle('-translate-x-full');
            sidebar.classList.toggle('translate-x-0');
            mainContent.classList.add('ml-48');
            mainContent.classList.remove('ml-0');    
            menuIcon.classList.add('hidden');
            localStorage.setItem('sidebarOpen', 'true');
        });
        menuIcon.hasEventListener = true; // Custom property to check if listener is added
    }

    // close sidebar
    closeBtn.addEventListener('click', function() {               
        sidebar.classList.add('-translate-x-full');
        sidebar.classList.remove('translate-x-0');
        mainContent.classList.remove('ml-48');
        mainContent.classList.add('ml-0');
        menuIcon.classList.remove('hidden');
        localStorage.setItem('sidebarOpen', 'false');
    });

    // logout hide sidebar
    document.getElementById('logout_button').addEventListener('click', function() {
        localStorage.setItem('sidebarOpen', 'false');
    });
    

})