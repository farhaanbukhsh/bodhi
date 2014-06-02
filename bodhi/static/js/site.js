var cabbage = new Cabbage();

var delay = (function(){
  var timer = 0;
  return function(callback, ms){
    clearTimeout (timer);
    timer = setTimeout(callback, ms);
  };
})();

$(document).ready(function() {
    // Kick it off, but only if we're on the right page.
    var container = $('#examples-container');
    if (container.length > 0) {
        $('#examples-container .lead').html(examples_loading_message);
        load_examples(1);
    }

    $('#text, #notes').keyup(function() {
        delay(function() {
            $("#preview").html("<h3><small>Loading</small></h3>");
            $.ajax({
                url: "/markdown",
                data: $.param({text: $('#text').val()}),
                dataType: 'json',
                success: function(data) {
                    console.log(data)
                    $("#preview").html(data.html);
                },
                error: function(e1, e2, e3) {
                    $("#preview").html("<h3><small>Error loading preview</small></h3>");
                }
            });
        }, 500);
    });

    // Attach bootstrap tooltips to everything.
    $('span').tooltip();

    // Make the rows on the comment form change color on click.
    $('.table td > input').click(function() {
        var td = $(this).parent();
        td.parent().removeClass('danger');
        td.parent().removeClass('success');
        td.parent().addClass(td.attr('data-class'));
    });
});
