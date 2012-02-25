$(function() {
	console.log("jquery online.");
	setupInputs();
});

function addFeatureSelector(allFeatures) {
	var groupDisplay = {"game": "Game",
						"ab": "At-Bat",
						"batter": "Batter",
						"pitcher": "Pitcher"};
	var groupOrder = ["game", "ab", "batter", "pitcher"];

	var displayMap = {"ab_inning": "Inning"} //TODO populate



	var existingFeatures = {}
	$.each($("#userinput select.feature"), function(idx, select) {
			existingFeatures[select.val()] = 1;
		});

	console.log(existingFeatures);

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

	var featureWrapper = document.createElement("div");
	var valueWrapper = document.createElement("div");

	$featureSelector
		.addClass("feature")
		.change(function() {
				console.log($featureSelector.val());

				var $valueSelector = $(document.createElement("select"));
				$.each(featureMap[$featureSelector.val()], function(idx, val) {
						var option = document.createElement("option");
						option.value = val;
						$(option)
							.html(val)
							.appendTo($valueSelector);
					});
				$(valueWrapper)
					.empty()
					.append($valueSelector);
			})
		.appendTo(featureWrapper);

	/* TODO add buttons for more/fewer features (automatic?) */

	$(document.createElement("div"))
		.append(featureWrapper)
		.append(valueWrapper)
		.appendTo("#userinput");

	$featureSelector.chosen();
}

function setupInputs() {
	$.getJSON("/cmd?t=features",
			  function (data, response) {
				  addFeatureSelector(data["features"]);
			  });
}

/*
$(document).ready(function() {
    prepare_tooltips();
    setup_tabs();

    var firstTab = "voting";
    if (window.location.hash) {
        var hashVal = window.location.hash.substring(1);
        if ($("ul.tabs ." + hashVal).length > 0)
            firstTab = hashVal;
    }
    $("ul.tabs ." + firstTab).click();
});

function get_cookie(c_name)
{
    var i,x,y,ARRcookies=document.cookie.split(";");
    for (i=0;i<ARRcookies.length;i++)
    {
        x=ARRcookies[i].substr(0,ARRcookies[i].indexOf("="));
        y=ARRcookies[i].substr(ARRcookies[i].indexOf("=")+1);
        x=x.replace(/^\s+|\s+$/g,"");
        if (x==c_name)
        {
            return y;
        }
    }
}

function set_cookie(c_name,value,exdays)
{
    var exdate=new Date();
    exdate.setDate(exdate.getDate() + exdays);
    var c_value=value + ((exdays==null) ? "" : "; expires="+exdate.toUTCString());
    document.cookie=c_name + "=" + c_value;
}

function add_seen_tooltip(tooltip_id) {
    var seen = Array();
    if (get_cookie("seen_tooltips"))
        seen = get_cookie("seen_tooltips").split(",");

    if ($.inArray(tooltip_id, seen) < 0) {
        seen.push(tooltip_id);
        set_cookie("seen_tooltips", seen.join(","), 3);
    }
}

function has_seen_tooltip(tooltip_id) {
    var seen = Array();
    if (get_cookie("seen_tooltips"))
        seen = get_cookie("seen_tooltips").split(",");

    return $.inArray(tooltip_id, seen) >= 0;
}

function show_tooltip(name, selector, config) {
    if (!has_seen_tooltip(name)) {
        $(selector).qtip(config);
        add_seen_tooltip(name);
    }
}

function process_vote(doc_id, val) {
    // kill all tooltips; hopefully they know what they're doing at this point...
    $(".qtip").hide();

    vote(doc_id, val);
    $("#twss_text").stop(true, true); // stop an existing fade-in
    $("#twss_text").fadeOut("fast");
}

function fade_to(text_selector, fade_to_color) {
    // fade to color
    $(text_selector).animate({ backgroundColor: fade_to_color },
                             { duration: "fast",
                               complete: function() {
                                   // fade back to black
                                   $(text_selector).animate({ backgroundColor: "#eeeeee" },
                                                            { duration: "slow"}); }
                             });
}

function yes_vote() {
    fade_to($("#positive"), "#22CC33");
    process_vote($("#twss_text").attr("doc_id"), 1);

    $("#share_tweet").show();
    $("#share_tweet .text").html($("#twss_text").html());

    var tweet = 'Yep, that\'s what she said: "' + $("#twss_text").attr("raw_text").replace(/@(\w+)/g, "\$1")  + '"';
    if ($("#twss_text").attr("screen_name"))
        tweet = "@" + $("#twss_text").attr("screen_name") + " " + tweet;

    var tweetIframe = $("#share_tweet .tweet iframe");

    // strip out old text, force reload
    var new_src = tweetIframe.attr("src")
        .replace(/&text=[^&$]+/, "")
        .replace(/tweet_button.html(\?\d+)?/, "tweet_button.html?"+Math.floor(Math.random()*8675309));

    // add new text
    new_src += "&text=" + encodeURIComponent(tweet);

    tweetIframe.attr("src", new_src);

    show_tooltip("tweet", "#share_tweet .tweet", {
        position: {
            corner: {
                tooltip: "leftMiddle",
                target: "rightMiddle",
            },
        },
        show: {
            when: false, // show on load
            ready: true,
            effect: { type: "fade", length: 200 }
            },
        hide: "mouseover", // hide on first mouseover
        style: {
            border: {
                width: 2,
                radius: 10
            },
                padding: 10,
            tip: true,
            name: "last_twss"
        }
    });
}

function no_vote() {
    fade_to($("#negative"), "#EE0000");
    process_vote($("#twss_text").attr("doc_id"), -1);
}

function parse_text(text) {
    var make_link = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
    text = text.replace(make_link,'<a class="link" href="$1" target="_new">$1</a>');

    var make_ats = /@([a-zA-Z_0-9]+)/g;
    text = text.replace(make_ats,'@<a class="link" href="http://twitter.com/$1">$1</a>');

    var make_hashes = /(#[-a-zA-Z_0-9]+)/g;
    text = text.replace(make_hashes,'<a class="link" href="http://twitter.com/search?q=$1" target="_new">$1</a>');
    return text
}
function twss_query(url) {
    $.ajax({
        url: url,
        dataType: "json",
        error: function () {
			// wait a second and just load a new twss
            setTimeout(load_twss, 1000);
        },
        success: function (data, textStatus, jqXHR) {
            if (data && (data["stat"] == "ok")) {
                // we'll always have another TWSS to share
                var twss_text_node = $("#twss_text");
                $(twss_text_node).attr("doc_id", data["data"]["doc_id"])
                    .attr("raw_text", data["data"]["twss"])
                    .attr("screen_name", data["data"]["screen_name"] || "");

                twss_text_node.stop(true, true); // stop an existing fade-out
                parsed_text = parse_text(data["data"]["twss"]);

                $(twss_text_node).hide();
                // get the line height with just a single character
                var lineHeight = twss_text_node.html("A")[0].offsetHeight;

                // now get the line height as parsed and if it's greater than one line, align left
                $(twss_text_node).html(parsed_text);
                $("#twss_text_shell")[0].style.textAlign = twss_text_node[0].offsetHeight > lineHeight ? "left" : "center";

                $(twss_text_node)
                    .hide()
                    .fadeIn("slow");

                // setup the onclicks for the various buttons
                $("#positive").unbind("click").click(yes_vote);
                $("#negative").unbind("click").click(no_vote);
            } else {
                // wait a second and just load a new twss
                setTimeout(load_twss, 1000);
            }
        }
        });
}
function vote(doc_id, vote) {
    var url = "/cmd?q=vote&d=" + doc_id + "&v=" + vote;
    twss_query(url);
}

function load_twss() {
    var url = encodeURI("/cmd?q=next");
    twss_query(url);
}

function setup_keyboard_shortcuts() {
    var fired = false;
    $(document).keydown(function(event) {
        if (fired) {
            return false;
        }
        if (event.keyCode == "89"        // y
            || event.keyCode == "187"    // +=
            || event.keyCode == "107") { // + (keypad)
            yes_vote();
        } else if (event.keyCode == "78"        // n
                  || event.keyCode == "189"     // _-
                  || event.keyCode == "109" ) { // - (keypad)
            no_vote();
        } else {
            return true;
        }
        event.preventDefault();
        fired = true;
    }).keyup(function(event) {
        fired = false;
    });
}

function prepare_tooltips() {
    $.fn.qtip.styles.positive = {
        background: '#22CC33',
        color: '#000',
        textAlign: 'left',
        border: {
            width: 3,
            radius: 5,
            color: '#227733'
        },
        padding: 5,
        tip: true,
        name: 'dark' // Inherit the rest of the attributes from the preset dark style
    }

    $.fn.qtip.styles.negative = {
        background: '#EE2222',
        color: '#000',
        textAlign: 'left',
        border: {
            width: 3,
            radius: 5,
            color: '#840000',
        },
        padding: 5,
        tip: true,
        name: 'dark' // Inherit the rest of the attributes from the preset dark style
    }

    $.fn.qtip.styles.last_twss = {
        background: '#F9FF4A',
        color: '#000',
        textAlign: 'left',
        border: {
            width: 3,
            radius: 5,
            color: '#D5DB25',
        },
        padding: 5,
        tip: true,
        name: 'dark' // Inherit the rest of the attributes from the preset dark style
    }
}

function show_response_helper_tooltips() {
    var mapping = {"positive": {selector: "#positive",
                                 style: "positive",
                                 tooltip: "bottomRight",
                                 target: "topMiddle"},
                   "negative": {selector: "#negative",
                                 style: "negative",
                                 tooltip: "bottomLeft",
                                 target: "topMiddle"}}
    $.each(mapping, function (name, attributes) {
        show_tooltip(name, attributes["selector"], {
            position: {
                corner: {
                    tooltip: attributes["tooltip"],
                    target: attributes["target"]
                }
            },
            show: {
                when: false, // show on load
                ready: true,
                effect: { type: "fade", length: 600 }
            },
            hide: "mouseover", // hide on first mouseover
            style: {
                border: {
                    width: 2,
                    radius: 10
                },
                padding: 10,
                tip: true,
                name: attributes["style"]
            }
        });
    });
}

function load_leaderboard(time_period) {
    function displayLeaders(leaders) {
        var list_elem = document.createElement("ol");
        $.each(leaders, function(idx, leader) {
            $(document.createElement("li"))
                .html(leader)
                .appendTo(list_elem);
        });

        $(".leaderboard")
            .hide()
            .append(list_elem)
            .fadeIn("fast");
    }

    $(".leaderboard").empty();

    var cached_leaders = $(".leaderboard").data(time_period);
    if (cached_leaders) {
        displayLeaders(cached_leaders);
    } else {
        $.ajax({
            url: "/cmd?q=lb&tp="+time_period,
            dataType: "json",
            error: function () {
				// wait a second and retry
                setTimeout(function() { load_leaderboard(time_period); }, 1000);
            },
            success: function (data, textStatus, jqXHR) {
                if (data && (data["stat"] == "ok")) {
                    // cache them for later
                    var leaders = data["data"]["leaders"];
                    $(".leaderboard").data(time_period, leaders);
                    displayLeaders(leaders);
                } else {
                    // wait a second and retry
                    setTimeout(function () { load_leaderboard(time_period); }, 1000);
                }
            }
        });
    }
}

function setup_tab(tab_selector, tab_content, load_fn) {
    $(tab_selector).click(function (evt) {
        $("ul.tabs .active").removeClass("active");
        $(".tab-content").hide();
        $(".qtip").hide();

        $(tab_selector).addClass("active");
        if ($(tab_content).hasClass("text-tab")) {
            $("ul.tabs").css("border-bottom", "1px solid #999");
            $("ul.tabs li").css("border-bottom", "1px solid #999");
        } else {
            $("ul.tabs").css("border-bottom", "none");
            $("ul.tabs li").css("border-bottom", "none");
        }

        $(tab_content).show();

        if (load_fn)
            load_fn();
    });
}

function setup_time_period_links() {
    $.each($("#bestof_tab .tp_menu a"), function(idx, elem) {
        $(elem).click(function(event) {
            event.preventDefault();
            $("#bestof_tab .tp_menu a.active").removeClass("active");
            $(elem).addClass("active");
            load_leaderboard($(elem).attr("tp"));
        });
    });
}

function setup_tabs() {
    setup_tab("ul.tabs .voting", "#voting_tab", function() {
        if (!$("#voting_tab").attr("loaded")) {
            setup_keyboard_shortcuts();
            show_response_helper_tooltips();
            load_twss();
            $("#voting_tab").attr("loaded", true);
        }
        // focus on the document so we can utilize keyboard shortcuts
        $(document).focus();
    });

    setup_tab("ul.tabs .bestof", "#bestof_tab", function() {
        if (!$("#bestof_tab").attr("loaded")) {
            setup_time_period_links();
            load_initial_leaderboard();
            $("#bestof_tab").attr("loaded", true);
        }
    });
    setup_tab("ul.tabs .faq", "#faq_tab");
}

function load_initial_leaderboard() {
    load_leaderboard("last_week");
}*/