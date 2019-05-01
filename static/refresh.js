function updatePosts() {
    $("#posts-holder").empty();

    $.getJSON('/newPosts', function(data){
        for (var post in response) {
            if (response.hasOwnProperty(post)) {
                $("#posts-holder").append($.parseHTML(post))
            }
        }
    });
}

// setInterval('updatePosts()', 1000 * 15);
// setInterval('updatePosts()', 1000 * 15);