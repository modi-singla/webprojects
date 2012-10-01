function onloadfns()
{
	$('#refresh').click(refresh_list);
	$('#searchbox').keyup(refresh_list);
	refresh_list();
	startPoll();
}

function user_ping()
{
	ping_url = '/ping?id=' + $(this).attr('id');
	$.ajax({url:ping_url, success: function(result){
		if(result)
		{
			
		}
	}});
}

function handle_json_response(result)
{
	if(result['type'] == 'user_list')
	{
		$('#online_list').html('');
		var list = result['user_list'];
		for(i=0;i<list.length;i++)
		{
			var li = "";
			li = li + '<li class=\"opponent\" id=\"' + list[i]['id'] + '\">';
			var img;
			switch(list[i]['state'])
			{
			case 0:
				img = 'available';
				break;
			case 1:
				img = 'idle';
				break;
			default:
				img = 'busy';
			}
			li = li + '<img width="10px" width="10px" src=\"static/' + img + '.jpg\"\>';
			li = li + '<div class=\"user_name\">' + list[i]['name'] + '</div></li>';
			$('#online_list').append(li)
		}
		$('.opponent').click(user_ping);
	}
}

ContinuePoll = 0;
function poll()
{
	if(ContinuePoll)
	{
		setTimeout("poll()", 10000);
		var poll_url = '/pull';
		if($('#searchbox').hasClass('watermark')){}
		else
		{
			poll_url = poll_url + '?search=' + $('#searchbox').val();
		}
		$.ajax({url: poll_url, dataType: 'json', success: handle_json_response});
	}
	
}

function startPoll()
{
	ContinuePoll = 1;
	poll();
}

function StopPoll()
{
	ContinuePoll = 0;
}

function refresh_list()
{
	//alert('a');
	var poll_url = '/buddy_list';
	if($('#searchbox').hasClass('watermark')){}
	else
	{
		poll_url = poll_url + '?search=' + $('#searchbox').val();
	}
	$.ajax({url: poll_url, dataType: 'json', success: handle_json_response});
};

function drawCalender()
{
	monthnames = new Array("January","Februrary","March","April","May","June","July","August","September","October","November","Decemeber");
	
	/*
	Not used for now but can be used to add custom links to special dates
	var linkcount=0;
	function addlink(month, day, href) {
		var entry = new Array(3);
		entry[0] = month;
		entry[1] = day;
		entry[2] = href;
		this[linkcount++] = entry;
	}
	Array.prototype.addlink = addlink;
	linkdays = new Array();
	linkdays.addlink(9,17,"http://google.com");
	linkdays.addlink(1,5,"http://www.facebook.com/aman.singla32");
	linkdays.addlink(1,26,"http://en.wikipedia.org/wiki/Republic_Day_(India)");
	linkdays.addlink(8,15,"http://en.wikipedia.org/wiki/Independence_Day_(India)");
	linkdays.addlink(12,25,"http://en.wikipedia.org/wiki/Christmas_day");
	linkdays.addlink(1,1,"http://en.wikipedia.org/wiki/New_Year%27s_Day");
	*/
	
	monthdays = new Array(12);
	monthdays[0]=31;monthdays[1]=28;monthdays[2]=31;monthdays[3]=30;monthdays[4]=31;monthdays[5]=30;monthdays[6]=31;monthdays[7]=31;monthdays[8]=30;monthdays[9]=31;monthdays[10]=30;monthdays[11]=31;todayDate=new Date();
	thisday=todayDate.getDay();
	thismonth=todayDate.getMonth();
	thisdate=todayDate.getDate();
	thisyear=todayDate.getYear();
	thisyear = thisyear % 100;
	thisyear = ((thisyear < 50) ? (2000 + thisyear) : (1900 + thisyear));
	if (((thisyear % 4 == 0) && !(thisyear % 100 == 0))	||(thisyear % 400 == 0)) monthdays[1]++;
	startspaces=thisdate;
	while (startspaces > 7) startspaces-=7;
	startspaces = thisday - startspaces + 1;
	if (startspaces < 0) startspaces+=7;
	document.write("<table class=\"transparent\" border=2>");
	document.write("<tr><td colspan=7><center><strong>" + monthnames[thismonth] + " " + thisyear + "</strong></center></font></td></tr>");
	document.write("<tr>");
	document.write("<td align=center>Su</td>");
	document.write("<td align=center>M</td>");
	document.write("<td align=center>Tu</td>");
	document.write("<td align=center>W</td>");
	document.write("<td align=center>Th</td>");
	document.write("<td align=center>F</td>");
	document.write("<td align=center>Sa</td>"); 
	document.write("</tr>");
	document.write("<tr>");
	for (s=0;s<startspaces;s++) {
		document.write("<td> </td>");
	}
	count=1;
	while (count <= monthdays[thismonth]) {
		for (b = startspaces;b<7;b++) {
			linktrue=false;
			document.write("<td>");
			document.write("<a style=\"color:black;\" href=\"http://www.google.com/search?btnI=745&q=" + count + " " + monthnames[thismonth] + "\">");
			linktrue=true;
			if (count==thisdate) {
				document.write("<div class=\"redhighlight\"><strong>");
			}
			if (count <= monthdays[thismonth]) {
				document.write(count);
			}
			else {
				document.write(" ");
			}
			if (count==thisdate) {
				document.write("</strong></div>");
			}
			if (linktrue)
				document.write("</a>");
			document.write("</td>");
			count++;
		}
		document.write("</tr>");
		document.write("<tr>");
		startspaces=0;
	}
	document.write("</table></p>");
}

clockID = 0;
function UpdateClock() 
{
   if(clockID) 
   {
      clearTimeout(clockID);
      clockID  = 0;
   }
   var tDate = new Date();
	var hours = tDate.getHours();
	var min = tDate.getMinutes();
	var sec = tDate.getSeconds();
	if (hours   < 10) {hours   = "0"+hours;}
    if (min < 10) {min = "0"+min;}
    if (sec < 10) {sec = "0"+sec;}
   document.getElementById("theClock").innerHTML = "" + hours + ":" + min + ":" + sec;
   clockID = setTimeout("UpdateClock()", 1000);
}

function StartClock() 
{
   clockID = setTimeout("UpdateClock()", 500);
}

function KillClock() 
{
   if(clockID) 
   {
      clearTimeout(clockID);
      clockID  = 0;
   }
}