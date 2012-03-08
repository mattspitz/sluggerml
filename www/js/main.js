$(function() {
	setupInputs();
});

function drawPieCharts(baseline, bundle) {
	$.each({"#baseline_chart": {"vals": baseline, "title": "Baseline Probability"},
				"#features_chart": {"vals": bundle, "title": "Featureset Probability"}},
		function(selector, d) {

			var data = new google.visualization.DataTable();
			data.addColumn("string", "Action");
			data.addColumn("number", "P(Action)");
			data.addRows([
				  ["Home Run", d["vals"]["HR"]],
				  ["Strikeout", d["vals"]["K"]],
				  ["(other)", 1.0 - Math.min(1.0, (d["vals"]["HR"] + d["vals"]["K"]))]
						  ]);

			var options = {
				title: d["title"]
			};

			var chart = new google.visualization.PieChart($(selector)[0]);
			chart.draw(data, options);
		});
}

function drawColumnChart(baseline, bundle) {
	var data = new google.visualization.DataTable();

	data.addColumn("string", "Label");
	data.addColumn("number", "Correlation Index");

	var HR = (bundle["HR"] / baseline["HR"]) - 1;
	var K = (bundle["K"] / baseline["K"]) - 1;

	data.addRows([["Home Run", HR], ["Strikeout", K]]);

	var max = 0.4999999999; // just shy of 50%
	var minVal = Math.min(HR, K, -1*max);
	var maxVal = Math.max(HR, K, max);

	/* stretch equally far in each direction */
	minVal = Math.min(-1*maxVal, minVal);
	maxVal = Math.max(-1*minVal, maxVal);

	/* make sure the number of gridlines matches with our stretch */
	var gridlines = 5 + 2 * Math.max(Math.ceil((maxVal/max) - 1), Math.ceil((-1*minVal/max) - 1));

	var options = {"vAxis": {format:"###%", minValue: minVal, maxValue: maxVal, gridlines: {count: gridlines}},
				   "legend": {position:"none"},
				   "title": "Correlation Index"};

	var chart = new google.visualization.ColumnChart($("#column_chart")[0]);
	chart.draw(data, options);
}

function addFeatureSelector(allFeatures) {
	var groupDisplay = {"game": "Game",
						"ab": "At-Bat",
						"batter": "Batter",
						"pitcher": "Pitcher"};
	var groupOrder = ["game", "ab", "batter", "pitcher"];

	var displayMap = {
		"game_daynight": "Game: Day/Night",
		"game_month": "Game: Month",
		"game_number": "Game: First/Doubleheader",
		"game_site": "Game: Site",
		"game_temp": "Game: Temperature",
		"game_winddir": "Game: Wind Direction",
		"game_year": "Game: Year",

		"ab_inning": "Inning",
		"ab_lrmatchup": "Lefty-Righty Matchup",
		"ab_numballs": "Number of Balls",
		"ab_numstrikes": "Number of Strikes",

		"batter_age": "Batter: Age",
		"batter_batpos": "Batter: Lineup Position",
		"batter_bats": "Batter: Bats",
		"batter_birthCountry": "Batter: Birth Country",
		"batter_experience": "Batter: Experience (Years)",
		"batter_fieldpos": "Batter: Fielding Position",
		"batter_height": "Batter: Height (Inches)",
		"batter_team": "Batter: Team",
		"batter_throws": "Batter: Throws",
		"batter_visorhome": "Batter: Home/Visitor",
		"batter_weight": "Batter: Weight",

		"pitcher_age": "Pitcher: Age",
		"pitcher_birthCountry": "Pitcher: Birth Country",
		"pitcher_experience": "Pitcher: Experience (Years)",
		"pitcher_height": "Pitcher: Height (Inches)",
		"pitcher_team": "Pitcher: Team",
		"pitcher_throws": "Pitcher: Throws",
		"pitcher_weight": "Pitcher: Weight"}

	var existingFeatures = {}
	$.each($("#userinput select.feature"), function(idx, select) {
			existingFeatures[$(select).val()] = 1;
		});

	var groupMap = {};
	var featureMap = {};
	$.each($(allFeatures), function(idx, tpl) {
			var fname = tpl[0], fvals = tpl[1];

			/* used later; yes, created each time; lame, right? */
			featureMap[fname] = fvals;

			if (existingFeatures[fname])
				return;

			var display = displayMap[fname] || fname;
			var group = fname.split("_")[0];
			if (!groupMap[group])
				groupMap[group] = [];

			groupMap[group].push( [ fname, display ] );
		});

	var $featureSelector = $(document.createElement("select"));

	$featureSelector
		.attr("data-placeholder", "Pick a feature...")

	$(document.createElement("option")).appendTo($featureSelector);

	$.each(groupOrder, function(idx, group) {
			var optgroup = document.createElement("optgroup");
			optgroup.label = groupDisplay[group];

			$.each(groupMap[group], function(idx, tpl) {
					var fname = tpl[0], display = tpl[1];
					var option = document.createElement("option");
					option.value = fname;

					$(option)
						.html(display)
						.appendTo(optgroup);
				});
			$(optgroup)
				.appendTo($featureSelector);
		});

	var $featureWrapper = $(document.createElement("span")).addClass("feature");
	var $valueWrapper = $(document.createElement("span"));

	$featureSelector
		.addClass("feature")
		.change(function() {
				var $valueSelector = $(document.createElement("select")).addClass("value");
				$.each(featureMap[$featureSelector.val()], function(idx, val) {
						var option = document.createElement("option");
						option.value = val;
						$(option)
							.html(val)
							.appendTo($valueSelector);
					});
				$valueWrapper
					.empty()
					.append($valueSelector);

				/* have to call chosen after it's appended to the dom */
				$valueSelector.chosen();
			})
		.appendTo($featureWrapper);

	var chooser = document.createElement("div");

	var $subtractor = $(document.createElement("span"))
		.addClass("subtractor")
		.html('<a href="#">-</a>')
		.click(function() {
				$(chooser).remove();
			});

	/* TODO add buttons for more/fewer features (automatic?) */

	$(chooser)
		.addClass("chooser")
		.append($subtractor)
		.append($featureWrapper)
		.append($valueWrapper)
		.appendTo("#userinput .features");

	$featureSelector.chosen();
}

function submitQuery() {
	var query = {};
	$.each($("#userinput .features .chooser"), function(idx, elem) {
			var feature = $(elem).find("select.feature").val();
			if (feature) {
				query[feature] = $(elem).find("select.value").val();
			}
		});

	$.getJSON("/cmd?type=predict",
			  query,
			  function(data) {
				  $("#results").show();
				  drawPieCharts(data["baseline"], data["bundle"]);
				  drawColumnChart(data["baseline"], data["bundle"]);
			  });
}

function setupInputs() {
	$.getJSON("/cmd?type=features",
			  function (data) {
				  addFeatureSelector(data["features"]);
				  $("#userinput .adder")
					  .click(function(e){
							  e.preventDefault();
							  addFeatureSelector(data["features"]);
						  });
				  $("#userinput .submit")
					  .click(function(e){
							  e.preventDefault();
							  submitQuery();
						  });
			  });
}
