// clear all checkboxes in brain regions
function clearBrains() {
	$('.brainCheck').attr('checked', false);
	clearColor();
}

// clear all datasets
function clearDatasets() {
	$('.datasetCheck').attr('checked', false);
	clearColor();
}

// check/uncheck datasets when checking/unchecking brain region
function selectPubsInRegion(region) {
	if ($('#'+region).attr('checked'))
	{
		// select all datasets containing a class matching the region of interest
		flashGreen('.'+region);
		$('.'+region).attr('checked', true);
	}
	else
	{
		flashRed('.'+region);
		$('.'+region).attr('checked', false);
		// get all datasets in that region, then set each to false
		// also if we are unchecking a region whose parent publication is selected, we need to uncheck the parent
		
		// get all datasets that belong to that region
		datasets = $('.'+region);
		datasets.each( function(i) {
			// get all the classes, which includes each dataset's parent
			classes = $(this).attr('class');
			// extract the publication, which is form pub:{htmlid}
			var match = classes.match(/\spub:(\w+)\s/i);
			// uncheck the publication
			if ($('#'+match[1]).attr('checked'))
			{
				$('#'+match[1]).attr('checked', false);
				flashRed('#'+match[1]+'Label');
			}	
		} );
	}
}

// remove all colors
function clearColor() {
	$('.datasetCheckLabel').removeClass('thankyou');
	$('.datasetCheckLabel').removeClass('thankyoublue');
	$('.datasetCheckLabel').removeClass('warning');
	$('.brainCheckLabel').removeClass('thankyou');
	$('.brainCheckLabel').removeClass('thankyoublue');
	$('.brainCheckLabel').removeClass('warning');
}

// remove all the brain regions for a given dataset
function clearBrainRegion (region, dataset) {
	var regions = region.split(/\s+/g);
	for (var i in regions)
	{
		if ($('#'+regions[i]).attr('checked') == true && $('#'+dataset).attr('checked') == false)
		{
			$('#'+regions[i]).attr('checked', false);
			flashRed('#'+regions[i]+"Label");
		}
		
	}
}

// uncheck all datasets in a publication
function clearPub (htmlid)
{
	$('#'+htmlid).attr('checked', false);
}

// select datasets belonging to a publication
function selectPubDatasets (htmlid)
{
	if ($('#'+htmlid).attr('checked'))
	{
		$('.'+htmlid).attr('checked', true);
	}
	else
	{
		$('.'+htmlid).attr('checked', false);
	}
}

function flashGreen(idClass)
{
	$(idClass).addClass('thankyoublue');
	setTimeout(function(){$(idClass).removeClass('thankyoublue');}, 1750);
}

function flashRed(idClass)
{
	$(idClass).addClass('warning');
	setTimeout(function(){$(idClass).removeClass('warning');}, 1750);
}