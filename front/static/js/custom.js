$(document).ready (function () {
    /* setting home tag to fill the freakn inital screen */
    $(function() {
    	/* -------------------------------- setting home to 100% on height --------------------------------*/
        $('#home').css({
            'height': ($(window).height()) + 'px'
        });

        $(window).resize (function() {
            $('#home').css({
                'height': ($(window).height()) + 'px'
            });
        });
        /* ------------------------------------------------------------------------------------------------*/



		/*------------------------------------- setting min-hights ----------------------------------------*/
        $('#aboooot').css({
            'min-height': ($(window).height()) + 'px'
        });

        $(window).resize (function() {
            $('#aboooot').css({
                'min-height': ($(window).height()) + 'px'
            });
        });



        $('#admissions').css({
            'min-height': ($(window).height()) + 'px'
        });

        $(window).resize (function() {
            $('#admissions').css({
                'min-height': ($(window).height()) + 'px'
            });
        });



        $('#gallery').css({
            'min-height': ($(window).height()) + 'px'
        });

        $(window).resize (function() {
            $('#gallery').css({
                'min-height': ($(window).height()) + 'px'
            });
        });



		$('#events').css({
            'min-height': ($(window).height()) + 'px'
        });

        $(window).resize (function() {
            $('#events').css({
                'min-height': ($(window).height()) + 'px'
            });
        });



        $('#contactus').css({
            'min-height': ($(window).height()) + 'px'
        });

        $(window).resize (function() {
            $('#contactus').css({
                'min-height': ($(window).height()) + 'px'
            });
        });
        /* ------------------------------------------------------------------------------------------------*/
    });

    $("html").niceScroll ({
        zindex: 2e6,
    });

    $('#MENUX').scrollspy();

    $('#da-slider').cslider({
        bgincrement : 65,
        autoplay    : true,
        interval    : 4575
    });

    $('.project').click (function () {
        /* making sure only ONE image is XXXL-ed at a time */
        /*
        THISX = this;

        $(".project").each (function () {
            if (this !== THISX) {
                $(this).removeClass("XXXL", 475);
            }
        });

        $(this).toggleClass ("XXXL", 475);
        */

		$(this).attr("img-src");
		$(".modal-body").html("<img src='/"+ $(this).attr("img-src") +"' style='max-height:500px; margin-left:10px;' />")
		$('#myModal').modal({
			backdrop: false
		});
    });

    /*
    STATIC_URL = $("#STATIC_URL").val();
    $(".CUT_PATH").each(function (){
        IMAGE_NAME = $(this).attr("src").slice(7);
        $(this).attr({"src":  STATIC_URL + IMAGE_NAME });
    });
    */

    $('body').stellar({
        horizontalScrolling: true,
        verticalScrolling: true,
        responsive: true,
    });
});

$(".nav li a[href^='#']").click (function (event) {
    event.preventDefault();
    var full_url = this.href;
    var parts = full_url.split("#");
    var trgt = parts[1];

    var target_offset = $("#" + trgt).offset();
    var target_top = target_offset.top - 0;
    $('html, body').animate({
        scrollTop: target_top
    }, 1500, 'easeInOutExpo');
});


/* validating the input on contact us form */
BLCOK = false; /* used to block clicks when an ajax request is in progress */
VALID = true; /* yep every user is an angle or is it angel --- duuuuuuuuuuuuuuuuuuude */

$("#SUBMIT").click (function () {
	if (!BLCOK) {
		$(".REQ").each (function () {
			if ($(this).val().length == 0) {
				alert ("Please fill all the fields.");
				VALID = false;
				return false;
			}
		});

		if (VALID) {
			/* email validation goes here id: EMAIL */
			/* Sending, am assuming you have validated the email --- Note it'll be validated @server so no biggie... */
			BLOCK = true; /* since all is well we should start blocking... */

			CSRF = $("input[type='hidden']").val();
			NAME = $("#NAME").val().length == 0 ? "Anonymous" : $("#NAME").val();
			EMAIL = $("#EMAIL").val();
			MESSAGE = $("#MESSAGE").val();

			$("#SUBMIT").addClass ("disabled", 10, function () {
				$("#MX").html ("Sending...");
				$("#ICONX").attr({"class": "icon-spinner icon-spin"});
			});

			AJAX = $.ajax ({
                type: "POST",
                url: "/contact_us/",
                data: "csrfmiddlewaretoken="+ CSRF +"&NAME="+ escape (NAME) +"&EMAIL="+ escape (EMAIL) +"&MESSAGE="+ escape (MESSAGE),
            });

			AJAX.done (function (msg) { /* something happened -- we have value from the server  */
				//alert ("we have something -- process it!");
				if (msg == "1") { /* we have a post -- disable the form */
					$(".DX").attr({"disabled": ""});
					$("#ICONX").attr({"class": "icon icon-ok"});
					$("#MX").html ("Message Sent");
					BLCOK = true; /* blocking since the user has sent message to the school */
				}

				else {
					alert ("The email you have provided is invalid, Please correct it and try again, thank you.");
					$("#ICONX").attr({"class": "icon icon-envelope"});
					$("#MX").html ("Send");
					$("#SUBMIT").removeClass ("disabled");
					BLOCK = false;
				}
			});

			AJAX.error (function (msg) {
				alert ("Something Horrible has gone wrong...");
				BLCOK = false; /* re-releasing */
			});
		}
	}
});

