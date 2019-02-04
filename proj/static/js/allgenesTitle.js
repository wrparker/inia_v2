var oldTitle = document.getElementById('agTitle').value;
var blurNow = false;
// always update title unless hit cancel
var updateTitle = true;
var blurFromFunction = true;

//$("#maincontent").css("max-width", $("#maincontent").width());

function agTitleKey(e)
{
    var keynum;
    if(window.event) // IE
    {
        keynum = e.keyCode;
    }
    else if(e.which) // Netscape/Firefox/Opera
    {
        keynum = e.which;
    }
    
    if (keynum == 27) //esc
    {
        blurNow = true;
        updateTitle = false;
        $('#agTitle').blur();
        titleBlur();
    }
    
    return true;

}


function titleFocus()
{
    $("#agTitle").addClass("white");
    $("#agTitle").addClass("border");
    $("#agTitleInfo").hide();
    $("#agTitle").animate({width:'600px'});
    $("#agTitleBG").animate({width:'600px', opacity:'100'});
    $('#agTitleSubmit').fadeIn();
    $('#agTitleCancel').fadeIn();
    
}

function titleBlur()
{
    // timeout is needed for blur otherwise it's triggered before onclick
    if (blurNow || (!$('#agTitle').is(":focus") && !$('#agTitleSubmit').is(":focus") && !$('#agTitleCancel').is(":focus")))
    {
        blurNow = false;
        if (!updateTitle)
        {
            $('#agTitle').attr('value', oldTitle);
        }
        else
        {
            var newTitle = $('#agTitle').attr("value");
            newTitle = newTitle.replace(/</g,"");
            newTitle = newTitle.replace(/>/g,"");
            if ($('#agTitle').attr("value") != newTitle)
            {
                alert("Sorry, < and > are not allowed in your title and have been removed.");
            }
            $('#agTitle').attr("value", newTitle);
            $('#title').attr("value", newTitle);
            var re = new RegExp(oldTitle);
            document.title = document.title.replace(re, newTitle);
            if (oldTitle != newTitle)
            {
                oldTitle = newTitle;
                newTitle = newTitle.replace(/\+/g, "%2B");
                newTitle = newTitle.replace(/ /g,"+");
                var networkIDArray = /id=(p?\d+)/i.exec(document.location.href);
                var networkID = networkIDArray[1];
                $('#agTitle').load("http://inia.icmb.utexas.edu/analysis/updateTitle?id=" + networkID + "&title=" + newTitle);
            }            
        }
        updateTitle = true;
        setTimeout(function(){
            $("#agTitleInfo").hide();
            $("#agTitle").animate({width:'100%'}, function(){$("#agTitle").removeClass("white");});
            //$("#agTitleBG").animate({width:'100%', opacity:'0'});
            $("#agTitle").removeClass("border");
            $('#agTitleSubmit').fadeOut();
            $('#agTitleCancel').fadeOut();
        }, 1);
    }
    
}

$('#agTitle').hover(function(){titleHover()}, function(){titleHoverOut()});
$('#agTitleInfo').hover(function(){titleInfoHover()}, function(){titleInfoHoverOut()});

function titleHover()
{
    if (!$('#agTitle').is(":focus") && !$('#agTitleSubmit').is(":focus") && !$('#agTitleCancel').is(":focus"))
    {
        $('#agTitleInfo').show();
    }
}

function titleInfoHover()
{
    if (!$('#agTitle').is(":focus") && !$('#agTitleSubmit').is(":focus") && !$('#agTitleCancel').is(":focus"))
    {
        $('#agTitleInfo').show();
        $("#agTitle").addClass("white");
    }
}

function titleHoverOut()
{
    //if (!$('#agTitle').is(":hover") && !$('#agTitleInfo').is(":hover"))
    //{
        $('#agTitleInfo').hide();
    //}
}

function titleInfoHoverOut()
{
    $('#agTitleInfo').hide();
    $("#agTitle").removeClass("white");
}

function agTitleFormSubmit()
{
    blurNow = true;
    updateTitle = true;
    $('#agTitle').blur();
    titleBlur();
    
    return false;
}