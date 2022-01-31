/*
* 
* JS functions to support with booking related forms
* @author: Ralph Mueller
* @date: 25.10.2021
*
*/

    

function getBuchungDetails(id) {
	/* 
	  re-route to actions available for 
	  this particular booking

	  author: ralph
	  date: 23.11.2021
	*/
	window.location.href = '/buchung/update_check/' + id;
	return (1)
}

function checkAvailability() {
	/* 
	  check availability of selected apartment and 
	  - confirm or
	  - negate with list of available apartments

	  author: ralph
	  date: 23.11.2021
	*/
	const anreiseElement = document.querySelector('#anreise');
	const abreiseElement = document.querySelector('#abreise');
	const apartmentElement = document.querySelector('#apartment_id');
	const availabilityElement = document.querySelector('#availability_id');
	const url = '/rest/apartment/available/' 
	  + apartmentElement.value 
	  + '?anreise=' + anreiseElement.value 
	  + '&abreise=' + abreiseElement.value;
	$.getJSON(url, function(result){
	  if (result.avail == true) {
		availabilityElement.innerHTML = 'Apartment verfügbar';
	  } else {
		availabilityElement.innerHTML = 'Apartment nicht verfügbar. Freie Apartments: ' + result.apartments; 
	  }
	});
	return false;
}
