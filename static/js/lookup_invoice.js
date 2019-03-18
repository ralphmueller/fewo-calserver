var date_options = { year: 'numeric', month: 'numeric', day: 'numeric' };

// set up recalc hooks for miete and summe

function calcDays(str_anreise, str_abreise) {
	var anreise = new Date(str_anreise);
	var abreise = new Date(str_abreise);
	var timeDiff = Math.abs(abreise.getTime() - anreise.getTime());
	return(Math.ceil(timeDiff / (1000 * 3600 * 24)));
}

function recalcMiete(){
	// calculate days and multiply with price per night, don't forget rebate!
	
}

function recalcKurtaxe(){
	// calculate kurtaxe for number of days; make sure that kurtaxe is current!
}

function getRechnung(t) {
	$("#buchung-form").show();		// show input form
  	var k = $(t).attr("id");
	var rx = Rx.Observable.fromPromise(fetch('/rest/buchung/' + k).then(res => res.json()))
	.subscribe(data => {
		console.log(data);
		$("#id-and-name").text(`Ändern Rechnung ${data.id}: ${data.besucher.name}, ${data.besucher.vorname}`);
		$("#buchung-vorname").val(data.besucher.vorname);
		$("#buchung-anreise").val(data.anreise);
		$("#buchung-abreise").val(data.abreise);
		$("#buchung-naechte").val(calcDays(data.anreise, data.abreise));
		$("#buchung-preis-nacht").val(data.preis_nacht);
		$("#buchung-miete").val(data.miete);
		$("#buchung-summe").val(data.summe);
		$("#buchung-kurtaxe").val(data.kurtaxe);
		$("#buchung-kurtaxe-voll").val(data.kurtaxe_vz);
		$("#buchung-kurtaxe-halb").val(data.kurtaxe_hz);
		$("#buchung-kurtaxe-kinder").val(data.kurtaxe_kinder);
		$("#buchung-kurtaxe-nz").val(data.kurtaxe_nz);
		$("#buchung-voraus").val(data.vorauszahlung);
		$("#buchung-restbetrag").val((data.summe - data.vorauszahlung).toFixed(2));
		$("#change-header").text(`Ändern ${data.id}: ${data.besucher.name}, ${data.besucher.vorname}`);
		// install event handlers
		['#buchung-anreise', '#buchung-abreise', '#buchung-preis-nacht', '#buchung-kurtaxe-voll', '#buchung-kurtaxe-halb', 
			'#buchung-kurtaxe-kinder', '#buchung-kurtaxe-nz', '#buchung-voraus']
			.forEach(function(e){
				$(e).focusout(function(){
					console.log('feuer: ', e);
						});
			});
	});
  }

(function (global, $, Rx) {
	
	var rest_besucher_get = '/rest/besucher/'; 	
	$("#buchung-form").hide();		// hide input form
  
  // Rechnungsliste
  function getRechnungen (term) {
	$("#buchung-form").hide();		// hide input form
    return $.ajax({
      url: '/rest/rechnung/' + term,
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

    var searcher = keyup.flatMapLatest(getRechnungen);

    searcher.subscribe(
      function (data) {
        $results
          .empty()
		  .append('<tr><th>ID</th><th>Name</th><th>Vorname</th><th>Anreise</th><th>Abreise</th><th>Summe</th></tr>')
          .append ($.map(data, function (v) {return $(`<tr id=${v.id} onclick="getRechnung(this)">`).html(
			  	`<td class="text-right">${v.id}</td><td>${v.besucher.name}</td><td>${v.besucher.vorname}</td>` +
			  	`<td class="text-right">${new Date(v.anreise).toLocaleString('de-DE',date_options)}</td>` + 
			    `<td class="text-right">${new Date(v.abreise).toLocaleString('de-DE',date_options)}</td>` +
			  	`<td class="text-right">${v.summe} €</td>` 
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