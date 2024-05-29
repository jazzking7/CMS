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
    // Hide the form  when clicking outside of it
    $(document).on('click', function(event) {
        if (!$(event.target).closest('#addFieldForm, #addfield').length) {
            $('#addFieldForm').hide();
        }
    });

    // Prevent form  click from hiding it
    $('#addFieldForm').on('click', function(event) {
        event.stopPropagation(); // Prevent the click from propagating to the document
    });
})