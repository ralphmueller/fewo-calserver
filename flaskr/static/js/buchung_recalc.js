// 
// Set date of abreise field to 3 days ahead of anreise field
// calculate and update nights of stay, net price (excl. kurtaxe)
// 

// data entered or provided in hidden fields

window.onload = function() {
	const anreise = document.querySelector('#anreise');
	const abreise = document.querySelector('#abreise');
    const preis_nacht = document.querySelector('#preis_nacht');
    const rabatt = document.querySelector('#rabatt');
    const zusatzkosten = document.querySelector('#zusatzkosten');
    const kurtaxe_vz = document.querySelector('#kurtaxe_vz');
    const ktsatz_hz = document.querySelector('#ktsatz_hz');
    const ktsatz_vz = document.querySelector('#ktsatz_vz');
    const vorauszahlung = document.querySelector('#vorauszahlung');
    // calculated 
    const naechte = document.querySelector('#nächte');
    const miete = document.querySelector('#miete');
    const kurtaxe = document.querySelector('#kurtaxe');
    const summe = document.querySelector('#summe');
    const restbetrag = document.querySelector('#restbetrag');

	// setting all the event listeners

    abreise.addEventListener('change', (event) => {
		naechte.innerHTML = datediff();
		recalc();
	  });
  
	  anreise.addEventListener('change', (event) => {
		let d1 = new Date(event.target.value);
		d1.setDate(d1.getDate() + 3);
		abreise.value = d1.toISOString().substring(0,10);
		naechte.innerHTML = datediff();
		recalc();
	  });	

    preis_nacht.addEventListener('change', (event) => {
      recalc();
    });

    zusatzkosten.addEventListener('change', (event) => {
      recalc();
    });

    rabatt.addEventListener('change', (event) => {
      recalc();
    });

    vorauszahlung.addEventListener('change', (event) => {
      recalc();
    });

    kurtaxe_vz.addEventListener('change', (event) => {
      recalc();
    });

    kurtaxe_hz.addEventListener('change', (event) => {
      recalc();
    });

	function datediff(){
		let d1 = new Date(anreise.value);
		let d2 = new Date(abreise.value);
		return(Math.floor((d2 - d1) / (1000*60*60*24)));
	  }
  
	function recalc() {
		// 
		// shall be triggered by
		//  - # nights
		//  - preis_nacht
		//  - zusatzkosten
		//  - rabatt
		//
		let nights = datediff(abreise.value, anreise.value);
		let miete_value = parseFloat(preis_nacht.value) * nights * (1 - parseFloat(rabatt.value)/100) + parseFloat(zusatzkosten.value);
		miete.innerHTML = miete_value.toLocaleString('de-DE', { 
		  style: 'currency', 
		  currency: 'EUR', 
		  minimumFractionDigits: 2 
		});
  
		let kurtaxe_value = nights * (parseFloat(kurtaxe_vz.value) * parseFloat(ktsatz_vz.value) + parseFloat(kurtaxe_hz.value) * parseFloat(ktsatz_hz.value));
		kurtaxe.innerHTML = kurtaxe_value.toLocaleString('de-DE', {
		  style: 'currency', 
		  currency: 'EUR', 
		  minimumFractionDigits: 2 
		});
  
		let summe_value = miete_value + kurtaxe_value;
		summe.innerHTML = summe_value.toLocaleString('de-DE', {
		  style: 'currency', 
		  currency: 'EUR', 
		  minimumFractionDigits: 2 
		});     
		
		let restbetrag_value = summe_value - parseFloat(vorauszahlung.value);
		restbetrag.innerHTML = restbetrag_value.toLocaleString('de-DE', {
		  style: 'currency', 
		  currency: 'EUR', 
		  minimumFractionDigits: 2 
		});  
	}
}