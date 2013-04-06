/**
 *
 *  File:
 *
 *  Project:
 *  Component:
 *
 *  Authors:    Dominic May;
 *              Lord_DeathMatch;
 *              Mause
 *
 *  Description:
 *
**/

var processing_occured_this_page_load = false;

function update_progress(){
    $.getJSON(status_url, function(cur_status){
        tobe_status = 'status; '+cur_status.cur_index + '/' + cur_status.queue.length;
        if (cur_status.running) {
            processing_occured_this_page_load = true;
            var percentage = cur_status.cur_index / cur_status.queue.length * 100;
            $('#analysis_progress').animate({width: String(percentage) + '%'}, 200 );
            // setTimeout(update_progress, 2000);
        } else {
            tobe_status += ', No analysis currently running';
            $('#analysis_progress').animate({width: '0%'}, 200 );
            if (processing_occured_this_page_load){
                $("#progress_bar_container").slideIn("slow");
            }
        }
        console.log(tobe_status);
    });
}

update_progress();

$(document).ready(function(){
    setInterval(update_progress, 2000);
});
