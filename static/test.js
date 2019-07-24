console.log('hi');

$(document).ready(function() {

    $('form').on('submit', function(event) {

        $.ajax({
            data : {
                user_id: $('#user_id').val(),
                rss_url: $('#rss_url').val(),
                daily_amount: $('#daily_amount').val(),
            },
            type: 'POST',
            url: '/process',
        })
        .done(function(data){
            if (data.error){
                $('#errorAlert').text(data.error).show();
                $('#successAlert').hide();
            } else {
                $('#successAlert').text(data.rss_url).show();

                $('#errorAlert').hide();
            }
        });
        event.preventDefault();
    });

});