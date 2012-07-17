$(document).ready(function(){
    /*Build array with required fields*/
    var mandatory_fields = ['muac_red', 'death', 'fastbreath', 'diarrhea',
                            'muac_green', 'fever', 'muac_yellow', 'bi_od'
        ]
    /*When district is changed*/
    $('#rdate').datepicker({dateFormat: 'yy-mm-dd'});
    $('#fsubmit').hide();
    $('#district').change(function(){
        var districtid = $(this).val();
        if (districtid == '0' || districtid == "")
            return;
        // $('#facility').find('option').remove().end();
        $('#facility').empty();
        $('#reporter').find('option').remove().end();
        $('#facility').append("<option value='0' selected='selected'>Select Facility</option>");
        $('#reporter').append("<option value='0' selected='selected'>Select Reporter</option>");
        $.get(
            '/ajax_portal/',
            {xtype:'district', xid: districtid},
            function(data){
                var health_centers = data;
                for(var i in health_centers){
                    val = health_centers[i]["id"];
                    txt = health_centers[i]["name"] + " " +health_centers[i]["type__slug"].toUpperCase();
                    $('#facility').append(
                        $(document.createElement("option")).attr("value",val).text(txt)
                    );
                }
            },
            'json'
        );
    });
    // $('#district').trigger('change');

    /*When facility is changed*/
    $('#facility').change(function(){
        var facilityid = $(this).val();
        if (facilityid == '0' || facilityid == '')
            return;
        $('#reporter').find('option').remove().end();
        $('#reporter').append("<option value='' selected='selected'>Select Reporter</option>");
        $.get(
            '/ajax_portal/',
            {xtype:'facility', xid: facilityid},
            function(data){
                var healthproviders = data;
                for(var i in healthproviders){
                    val = healthproviders[i]['id']
                    txt = healthproviders[i]['name'] + " (" + healthproviders[i]['connection__identity']+")"
                    $('#reporter').append(
                            $(document.createElement("option")).attr("value",val).text(txt)
                    );
                }
            },
            'json'
        );
    });

    /*When Report Type is changed*/
    $('#rtype').change(function(){
        var typeid = $(this).val();
        if (typeid == '0' || typeid == '')
            return;

        $('#xform').find('option').remove().end();
        $('#xform').append("<option value='0' selected='selected'>Select Report</option>");
        $.get('/ajax_portal/',
            {'xtype':'report',xid:typeid},
            function(data){
                var xforms = data;
                for (var i in xforms) {
                    val = xforms[i]['id'];
                    txt = xforms[i]['name'] + "("+xforms[i]['keyword'] + ")";
                    $('#xform').append($(document.createElement("option")).attr("value",val).text(txt))
                }
            },
            'json'
        );

    });

    /*Some initial stuff*/
    // $('#ffields').hide();

    /*When XForm is changed*/
    $('#xform').change(function(){
        var xformid = $(this).val();
        if (xformid == '0'){
            $('#fsubmit').hide();
            $('#xff_table').empty();
            return;
        }
        $.get('/ajax_portal/',
            {xtype:'xform', xid: xformid},
            function(data){
                /*Now time to generate dynamic inputs*/
                $('#xff_table').empty();
                htmlstr = "";
                var xformfields = data;
                for(var i in xformfields){
                    name = xformfields[i]['name'];
                    command = xformfields[i]['command'];
                    field_type = xformfields[i]['field_type'];
                    field_id = 'id_'+command;
                    if (field_type == 'binary'){
                        label_str = "<label for='" + field_id +"'>"+name.charAt(0).toUpperCase() +name.slice(1) + ":</label>";
                        htmlstr += "<tr><td>" + label_str +"</td><td><input type='file' name='"+
                        command +"' id='" + field_id + "' class='itext" + validation_class +"'/></td></tr>";
                    }else{
                        if ($.inArray(command,mandatory_fields) > -1){
                            validation_class = ' required'
                        } else {
                            validation_class = ''
                        }
                        label_str = "<label for='" + field_id + "'>"+name.charAt(0).toUpperCase() +name.slice(1) + ":</label>";
                        htmlstr += "<tr><td>" + label_str +"</td><td><input type='text' name='"+
                        command +"' id='" + field_id + "' class='itext" + validation_class + "'/></td></tr>";
                    }
                }
                $('#xff_table').append(htmlstr);
                /* Add Submit buttons*/
                $('#fsubmit').show();
            },
            'json'
        );
    });
    /*More stuff*/
    /*Validation*/
    $('#dataForm').validate({messages:{reporter: "Reporter is required", rdate:"date is required"}});
});
