function get_current_conversion(){
    $.ajax({url: "get_conversion/", success: function(response){
        response = $.parseJSON(response);
        conversion_content = '<p>Актуальная конверсия</p><p>' + response * 100 + '%</p>';
        $('#conversion').html(conversion_content);
    }});
};
$(document).ready(function(){get_current_conversion();});
$(document).ready(function(){
    $("#renew").click(function(){get_current_conversion();});
});