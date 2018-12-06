
var current_power = "" 
var current_page_num = 1
var keywordquery = ""
var power_list = []

/* accepts power name by exact title match or error */
function getPowerView(power_name){
	current_power = power_name
	var power_data
	var xmlhttp = new XMLHttpRequest();
	xmlhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			power_data = this.responseText;
			console.log("retrieved data for " + power_name);
			//console.log(power_data)
			document.getElementById("power-view").innerHTML = power_data;
		}
	};
	xmlhttp.open("GET", `search?div=pow&power=${power_name}`, true);
	xmlhttp.send();
	getLoadingScreen();
	document.getElementById("power-view").innerHTML =  "<h2>Loading...</h2>";   // Blank page
}

function searchFor(query){
	keywordquery = query;
	current_page_num = 1;
	getSearchResultsList(query);
}


function getSearchResultsList(query){
	keywordquery=query
	current_page_num = 1
	var xmlhttp = new XMLHttpRequest();
	xmlhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			power_list = JSON.parse(this.responseText);
			console.log("retrieved page " + current_page_num);
			var res_title = `Results for "${keywordquery}"`
			if (power_list.length == 0){
				res_title = `No Results for "${keywordquery}"`
			}
			document.getElementById("power-list-title").innerText = res_title;
			popPowerList()
		}
	};
	xmlhttp.open("GET", `search?div=res&format=json&query=${keywordquery}`, true);
	xmlhttp.send();
	power_list = [];
}


function getCategory(cat_name){
	var xmlhttp = new XMLHttpRequest();
	xmlhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			cat = JSON.parse(this.responseText);
			subcats = cat['sub_cat'];  /* Do something with this?? */
			powers = cat['members'];
			power_list = combineLists(subcats, powers);
			console.log("cat data for " + cat_name);
			document.getElementById("power-list-title").innerText = `Members of ${getCategoryName(cat_name)}`
			popPowerList()
		}
	};
	xmlhttp.open("GET", `category/${cat_name}`, true);
	xmlhttp.send();
	power_list = [];
}


function getLinkButton(power_link){
	var cat_link = getCategoryName(power_link);
	if (cat_link != null){
		return `<button class="cat-button" id="${power_link}" onclick="getCategory(this.id)"><span>${cat_link}</span></button>`
	}
	else
		return `<button class="pow-button" id="${power_link}" onclick="getPowerView(this.id)"><span>${power_link}</span></button>`
}


function combineLists(subcats, powers){
	list = [];
	s = subcats.length;
	p = powers.length;
	for (var i = 0; i < s+p; i++){
		if (i < s){
			list[i] = subcats[i];
		}
		else{
			list[i] = powers[i-s];
		}
	}
	return list;
}

function popPowerList(){
	var pow_buttons = ""
	var results_per_page = 10;
	var start_pow = results_per_page * (current_page_num - 1);
	var end_pow = results_per_page * (current_page_num);
	
	/* POWER BUTTONS */
	for (var i = start_pow; i<end_pow && i < power_list.length; i++ ){
		var pow = power_list[i];
		pow_buttons += getLinkButton(pow) + "\n";
		//button autofocus
	}
	document.getElementById("power-list").innerHTML = pow_buttons;
	
	/* POWER NAV */
	pages = power_list.length / results_per_page;
	
	var nav_pages = "";
	if (current_page_num > 1){
		nav_pages += `<a onclick="getResultsPage('${'<'}')" href="#">${'<'} </a> `;
	}
	for (var i = 0; i < pages; i++){
		nav_pages += `<a onclick="getResultsPage('${i+1}')" href="#">${i+1}</a> `;
	}
	if (current_page_num < pages-1){
		nav_pages += `<a onclick="getResultsPage('${'>'}')" href="#">${'>'} </a> `;
	}
	document.getElementById("power-list-nav").innerHTML = nav_pages;
	
}


function getCategoryName(category_path){
	var prefix = "Category:";
	if (category_path.includes(prefix)){
		return ((category_path.substring(prefix.length)).replace(/_/g," "));
	}
	return null;
}


function getResultsPage(nav_char){
	if (nav_char == '>'){
		current_page_num += 1;
	}else if (nav_char == '<'){
		current_page_num -= 1;
	}else{
		current_page_num = parseInt(nav_char);
	}
	popPowerList();
}