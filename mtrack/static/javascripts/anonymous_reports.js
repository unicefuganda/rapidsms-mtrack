function deleteAnonymousReport(elem, pk, name) {
    if (confirm('Are you sure you want to remove ' + name + '?')) {
        $(elem).parents('tr').remove();
        $.post('../anonymousreports/' + pk + '/delete/', function(data) {});
    }
}

function editAnonymousReport(elem, pk) {
    overlay_loading_panel($(elem).parents('tr'));
	$(elem).parents('tr').load('../anonymousreports/'+pk+'/edit/','',function(){
	    $('#div_panel_loading').hide();
	});
}

function submitForm(link, action, resultDiv) {
    form = $(link).parents("form");
    form_data = form.serializeArray();
    resultDiv.load(action, form_data);
    disablePopup();
    return false;
}

function deleteConnection(elem,link,name) {
    if (confirm('Are you sure you want to remove ' + name + '?')) {
        $(elem).parents('p').remove();
        $.post(link, function(data) {});
    }
}
function edit_elem(elem){
	$('#contactArea').html("");
	$('#popup_heading').html('Edit Anonymous Report')
	$.get(
		'../anonymousreports/'+elem.id+'/edit/',
		{},
		function(data){
			$('#contactArea').html(data);
		}
	);
	centerPopup();
    loadPopup();
}
function detail_elem(elem){
	$('#contactArea').html("");
	id = elem.id.split('_')[1];
	$('#popup_heading').html('Anonymous Report Details');
	$.get(
		'../anonymousreports/'+id+'/detail/',
		{},
		function(data){
			$('#contactArea').html(data);
		}
	);
	centerPopup();
    loadPopup();
}
$(document).ready(function() {
	//Accordion based messaging history list
    if($('#accordion').length > 0) {
    	$(function() {
    		$( "#accordion" ).accordion({ autoHeight: false, collapsible: true });
    	});
    }
	$(function() {
        $('.replyForm').hide();
	});
});