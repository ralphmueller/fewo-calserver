/*
* @author: Ralph Mueller
* @date: 20.03.2018
*
* generalized chart drawing functions
*
*/

// return a TD, number formatted in €
function td_number(number) {
	var s = '<td class="text-right">';
	s += number.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });
	s += '</td>';
	return (s)
}

// return a TH, label text centered
function th_label(label) {
	return ('<th class="text-center">' + label + '</th>' );
}

// return a TD label (starting label for a row)
function td_label(label, url) {
	return ('<td><a href="' + url + label + '">' + label + '</a></td>' );
}

// build the entire table and return it
function build_table(data) {
	var s = '<tbody><tr>';
	// top row
	s += th_label('');
	for (i = 0; i < data.labels.length; i++) {
		s += th_label(data.labels[i]);
	}
	s += '</tr>';
	
	for (i = 0; i < data.datasets.length; i++) {
		s += '<tr>'; 
		s += td_label(data.dataset_labels[i], data.single_apt_url);
		for (j = 0; j < data.datasets[i].length; j++) {
			s += td_number(data.datasets[i][j]);
		}
	s += '</tr></tbody>';
	}
	return (s);
}

// output table and diagram as bar chart
function chart_func_1(data){
	
	// display table
	
	s = build_table(data);
	$('#data-table').html(s);
	
	// draws a bar chart from n datasets
	var ctx = document.getElementById('data-chart').getContext('2d');

	rgba = ["rgba(153,255,51,0.4)", "rgba(153,255,51,2.0)", "rgba(255,153,51,0.4)", "rgba(255,153,51,2.0)", "rgba(153,51,255,0.4)", "rgba(153,51,255,2.0)"]

	var datasets = []
	for (i = 0; i < data.datasets.length; i++) {
		datasets[i] = [];
		datasets[i].label = data.dataset_labels[i];
		datasets[i].data = data.datasets[i];
		datasets[i].cubicInterpolationMode = 'default';
		datasets[i].backgroundColor = rgba[i];
	}

	var myChart = new Chart(ctx, {
		type: 'bar',
		data: {
		labels: data.labels,
		datasets: datasets
	}
	});
}