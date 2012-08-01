$(document).ready(function(){
    /*When district is changed*/
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
            '/ajax_portal2/',
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

    /*When facility is changed*/
    $('#facility').change(function(){
        var facilityid = $(this).val();
        if (facilityid == '0' || facilityid == '')
            return;
        $('#xff_table').empty();
        $.get(
            '/ajax_portal2/',
            {xtype:'facility', xid: facilityid},
            function(data){
                var catchment_areas = data;
                htmlstr = "<tr><td>Catchment Areas(Village)</td><td>Village Type</td></tr>";
                for(var i in catchment_areas){
                    name = catchment_areas[i]['name']
                    type = catchment_areas[i]['type']
                    htmlstr += "<tr><td>" + name +"</td><td>" + type + "</td></tr>";
                }
                $('#xff_table').append(htmlstr);
            },
            'json'
        );
    });

});
