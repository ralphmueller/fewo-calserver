


function getBesucherDetails(t) {
	window.location.href = '/besucher/update/' + t;
	return (t)
  }


(function (global, $, Rx) {
	
	var rest_besucher_get = '/rest/besucher_by_name/'; // with attribute name fragement, returns a list of users
	$("#besucher-details").hide();		// hide details 
	$("#besucher-abgerechnet").hide();
	$("#besucher-gebucht").hide();
	$("#besucher-storno").hide();

  // Besucher
  function getBesucher (term) {
	// will see what we need here $("#buchung-form").hide();		// hide input form
    return $.ajax({
      url: '/rest/besucher_by_name/' + term,
      dataType: 'json',
    }).promise();
  }

  function main() {
	  
    var $input = $('#textInput'),
        $results = $('#results');
		
	var $date = $('#date');
	
	var currentTime = Rx.Observable.timer(0,1000).map(function(e) {return new Date()});
	
	currentTime.subscribe(
		function(data) {
			$date 
				.empty()
				.append(data)
		}
	);

    // Get all distinct key up events from the input and only fire if long enough and distinct
    var keyup = Rx.Observable.fromEvent($input, 'keyup')
      .map(function (e) {
        return e.target.value; // Project the text from the input
      })
      .filter(function (text) {
        return text.length > 2; // Only if the text is longer than 2 characters
      })
      .debounce(750 /* Pause for 750ms */ )
      .distinctUntilChanged(); // Only if the value has changed

    var searcher = keyup.flatMapLatest(getBesucher);

    searcher.subscribe(
      function (data) {
        $results
          .empty()
		  .append('<tr><th>Anrede</th><th>Name</th><th>Vorname</th><th>Email</th><th>Adresse</th></tr>')
          .append ($.map(data, function (v) {return $(`<tr id=${v.id} onclick=getBesucherDetails(${v.id})>`).html(
			  	`<td>${v.anrede}</td>` +
			    `<td>${v.name}</td>`+
			    `<td>${v.vorname}</td>` +
				`<td>${v.email}</td>` +
			    `<td>${v.strasse}, ${v.plz} - ${v.stadt}</td>` 
			  );
		  }))
      },
      function (error) {
		console.log('Error: ', error);
        $results
          .empty()
          .append($('<li>'))
          .text('Error:' + error);
      });
  }
  
  $(main);
  
}(window, jQuery, Rx));