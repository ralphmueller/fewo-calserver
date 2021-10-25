/*
* @author: Ralph Mueller
* @date: 25.10.2021
*
* datepicker settings
*
* requires:
*
*   - jquery (js)
*   - jquery-ui (css)
*   - jquery-ui (js)
*   - jquery-ui.i18 (js)
*
*/

$( function() {
	$.datepicker.setDefaults( $.datepicker.regional[ "de" ] );
	$( "#abreise" ).datepicker( "option", "dateFormat", "dd.mm.yy" );
	$( "#abreise" ).datepicker( "option", "dateFormat", "dd.mm.yy" );
    $('#anreise').datepicker({
    onSelect: function(dateText, inst) {
		console.log(dateText);
      $("input[name='abreise']").val(dateText);
    }
	});
  } );