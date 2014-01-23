$(document).ready(function(){
    $('#fsubmit').hide();
    /*When Poll is changed*/
    $('#poll').change(function(){
        var poll_id = $(this).val();
        if (poll_id == '0'){
            $('#fsubmit').hide();
            $('#xff_table').empty();
            return;
        }
        $.get('/poll_info/',
            {xtype:'poll', xid: poll_id},
            function(data){
                /*Now time to generate dynamic inputs*/
                $('#xff_table').empty();
                htmlstr = "";
                var poll_info = data[0];
                htmlstr += "<tr><td>Name</td><td style='font-size:120%;'>" + poll_info['name'] + "</td></tr>";
                htmlstr += "<tr><td>Star Date</td><td>" + poll_info['start_date'] + "</td></tr>";
                htmlstr += "<tr><td>End Date</td><td>" + poll_info['end_date'] + "</td></tr>";
                htmlstr += "<tr><td>Question</td><td>" + poll_info['question'] + "</td></tr>";
                htmlstr += "<tr><td>Default Response.</td><td>" + poll_info['default_response'] + "</td></tr>";
                htmlstr += "<tr><td>Responses</td><td style='font-size:120%;'>" + poll_info['responses__count'] + "</td></tr>";
                htmlstr += "<tr><td></td><td><a href='../../polls/" + poll_info['id']+ "/view/'>Edit Poll</a></td></tr>";

                $('#xff_table').append(htmlstr);
                /* Add Submit buttons*/
                $('#fsubmit').show();
            },
            'json'
        );
    });
    $('#pollForm').validate({messages:{poll: "Poll is required"}});
});
