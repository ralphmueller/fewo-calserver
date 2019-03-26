function getBuchungenForBesucher(t, h3Text, stat){
	
	Rx.Observable.fromPromise(fetch('/rest/buchungen/besucher/' + t + '?status=' + stat).then(res => res.json()))
	.subscribe(data => {
		var results = $("#besucher-" + stat);
		results.empty();
		if (data.length > 0) {			// show rechnungen
			results
				.show()
				.append($('<h3>').text(h3Text))
            	.append ($.map(data, function (v) {return $('<p>').html(
  			  		`<span class="badge badge-dark">${v.id}</span>  ${v.apartment.name} ${new Date(v.anreise).toLocaleDateString()}-${new Date(v.abreise).toLocaleDateString()} ${v.miete} ${v.kurtaxe} ${v.summe}` 
  			  	);
  		  	}))
		}
	});
}

function getBesucherDetails(t) {
	Rx.Observable.fromPromise(fetch('/rest/besucher/' + t).then(res => res.json()))
	.subscribe(data => {
		var results = $("#besucher-details");
		results.show();		
		results
			.empty()
			.append($('<h3>').text('Besucher Details'))
			.append($('<div class="d-flex flex-column bd-highlight mb-3">')
				.html($('<div id="1" class="d-inline p-2 bg-light border">').html(`<span class="badge badge-dark">${data.id}</span> ${data.anrede} ${data.name}, ${data.vorname}`))
				.append($('<div id="2" class="d-inline p-2 bg-light border">').text(`${data.strasse}, ${data.stadt}, ${data.land}-${data.plz}`))
				.append($('<div id="2" class="d-inline p-2 bg-light border">').text(`${data.email}, ${data.tel}`))
			)
	});
	
	getBuchungenForBesucher(t, 'Rechnungen', 'abgerechnet');
	getBuchungenForBesucher(t, 'Buchungen', 'gebucht');
	getBuchungenForBesucher(t, 'Storno', 'storno');
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
		  .append('<tr><th>ID</th><th>Name</th><th>Vorname</th><th>Strasse</th></tr>')
          .append ($.map(data, function (v) {return $(`<tr id=${v.id} onclick=getBesucherDetails(${v.id})>`).html(
			  	`<td>${v.id}</td>` +
			    `<td>${v.name}</td>`+
			    `<td>${v.vorname}</td>` +
			    `<td>${v.strasse}, ${v.stadt}</td>` 
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