/* common.js for app */

function confirmRecordDelete(){
	return confirm("Are you sure you want to delete this record?");
}

function updateImage(imageSource,imageID) {
	$(imageID).attr("src",imageSource);
}

function editFromList(editFormURL) {
	setModal('dialog',true);
	$('#modal-form-contain').show();
	$('#modal-form').show();
	$('#modal-form').load(editFormURL,function(data){modalFormSuccess(data);})
	}

function modalFormSuccess(data){
	// return true if the update was successful
	// also return true if the update failed for a reason
	// other than a validation error
	var result = true;
	if (data.toLowerCase() == "success"){
		result = true;
	}
	else if (data.substr(0,9).toLowerCase() == 'failure: '){
		cancelModalForm();
		// display an error message
		alert(data.substr(9)) 
		result = true;
	} else { result = false; }
	if(result == true){ cancelModalForm(); }
	return result;
}


function submitModalForm(formID, postingURL, successTarget, successURL){
	$("#modal-form").load(postingURL,formToJson(formID),function(data){
		if (modalFormSuccess(data)){
			$("#"+successTarget).load(successURL);
		} else {
			// there were errors, so the form will redisplay
		}
	}
	,"html");
}

function formToJson(formID){
	var raw = $("#"+formID).serializeArray();
	var obj = {};
	jQuery.each( raw, function( i, field ) { 
		if (obj[field.name] !== undefined) {
			if (!obj[field.name].push) {
				obj[field.name] = [obj[field.name]];
			}
			obj[field.name].push(field.value || '');
		} else {
			obj[field.name] = field.value || '';
		}
		
	});
	return obj;
}

function deleteFromList(deleteActionURL, successTarget){
	if (confirmRecordDelete()) {
		$.get(deleteActionURL, function(data){
		if(data == "success"){
			$("#"+successTarget).text('').hide();
		} else {
			alert(data)
		}
	})
	}
}

function cancelModalForm(){
	setModal("dialog",false);
	$("#modal-form").text("")
	$("#modal-form, #modal-form-contain").hide();
}

// Paint the screen with a div to simulate a modal dialog
function setModal(objectID,modalState) {
	var objectID = "#"+objectID;
	var docHeight = $(document).height()+"px";
	var docWidth = $(document).width()+"px";
	$(objectID).css("position","absolute").css("top","0").css("left","0");
	if(modalState) {
		// display the div
		$(objectID).css("height",docHeight).css("width",docWidth).show();
	}
	else {
		//hide the div
		docHeight = "1px";
		docWidth = "1px";
		$(objectID).css("height",docHeight).css("width",docWidth).hide();
	}
}

function getDateString(d) {
	// format the LOCAL time string into the ISO formatted string that the db expects
    var d = d || new Date();
    //var n = d.toISOString(); // toISOString always returns UTC time, not ISO formatted local time
	var dateString = (d.getFullYear() + "-");
	dateString += ("0" + (d.getMonth()+1)).substr(-2)+"-"
	dateString += ("0" + d.getDate()).substr(-2)
    return dateString;
	//$("#eventDate").val(dateString);
}
