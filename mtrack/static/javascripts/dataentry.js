$(document).ready(function(){
    /*Look at django-selectable*/
    /*When district is changed*/
    $('#district').change(function(){
        var districtid = $(this).val();
        if (districtid == '0')
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
        if (facilityid == '0')
            return;
        $('#reporter').find('option').remove().end();
        $('#reporter').append("<option value='0' selected='selected'>Select Reporter</option>");
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

    /*Some initial stuff*/
    // $('#ffields').hide();

    /*When XForm is changed*/
    $('#xform').change(function(){
        var xformid = $(this).val();
        if (xformid == '0'){
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
                        htmlstr += "<tr><td>" + name +"</td><td><input type='file' name='"+ command +"' id='" + field_id + "' class='itext'/></td></tr>";
                    }else{
                        htmlstr += "<tr><td>" + name +"</td><td><input type='text' name='"+ command +"' id='" + field_id + "' class='itext'/></td></tr>";
                    }
                }
                $('#xff_table').append(htmlstr);
                /* Add Submit buttons*/
            },
            'json'
        );
    });
    /*More stuff*/
});
