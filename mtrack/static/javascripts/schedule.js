$(document).ready(function(){
    $('#location2').hide();
    $('#grp2').hide();
    $('#xform2').hide();
    $('#dinter').hide();
    $('#row-args').hide();
    // $('#row-handlers').hide();
    $('#sdate').datepicker({dateFormat: 'yy-mm-dd'});
    $('#edate').datepicker({dateFormat: 'yy-mm-dd'});

    $('#loc_type').change(function(){
        if ($(this).val() == 'list'){
            $('#location').hide();
            $('#location2').show();
        }else{
            $('#location2').hide();
            $('#location').show();
        }
    });
    $('#gtype').change(function(){
        if ($(this).val() == 'list'){
            $('#grp').hide();
            $('#grp2').show();
        }else{
            $('#grp2').hide();
            $('#grp').show();
        }
    });

    $('#xformtype').change(function(){
        if ($(this).val() == 'list'){
            $('#xform').hide();
            $('#xform2').show();
        }else{
            $('#xform2').hide();
            $('#xform').show();
        }
    });
    $('#msg').keyup(function(){
        var obj = $('#msg');
        var cc = $('#ccount');
        var x = obj.val();
        var l = obj.val().length;
        cc.val(l);
        if(x.length >= 160){
            var y = obj.val().substring(0,160);
            obj.val(y);
            cc.val(160);
        }
    });
    $('#interval').change(function(){
        if($(this).val() == 'week'){
            $('#dinter').show();
        }else{
            $('#dinter').hide();
        }
    });

    $('#setup').change(function(){
        if ($(this).val() == 'temp'){
            $('#row-handlers').show();
            $('#row-args').show();
        }else{
            $('#row-handlers').hide();
            $('#row-args').hide();
            $('#handler').val("");
        }
    });

    /* Some Validation stuff follows */
    $.validator.addMethod("enddate_greater_startdate", function(value, element){
        edate = $('#edate').val()
        if (edate != '')
            return $('#edate').val() > $('#sdate').val()
        else
            return true
    }, "* End date should be greater than Start date");

    $('#schedform').validate({
        rules: {
                   msg: {
                            required: true
                        },
                   edate: {
                              required: false,
                              enddate_greater_startdate: true
                          },
                   grp2: {
                             required: function(){return $('#gtype').val() == 'list';}
                         },
                  location2: {
                                required: function(){return $('#loc_type').val() == 'list';}
                             },
                  xform2: {
                                required: function(){return $('#xformtype').val() == 'list';}
                          },
                 xform: {
                                required: function(){return $('#xformtype').val() == 'particular';}
                        }
               },
        messages: {
                      msg: "Message is required",
                  }
    });
});
