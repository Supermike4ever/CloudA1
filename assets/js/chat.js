var checkout = {};

$(document).ready(function () {
  var $messages = $(".messages-content"),
    d,
    h,
    m,
    i = 0;

  $(window).load(function () {
    $messages.mCustomScrollbar();
    insertResponseMessage(
      "Hi there, I'm your personal Concierge. How can I help?"
    );
  });

  function updateScrollbar() {
    // Force layout recalculation
    $messages.find(".mCSB_container").css("height", "auto");

    // Get actual content height by measuring all children
    var totalHeight = 0;
    $messages
      .find(".mCSB_container")
      .children()
      .each(function () {
        totalHeight += $(this).outerHeight(true);
      });

    // Set explicit height if needed
    if (totalHeight > 0 && $messages.find(".mCSB_container").height() === 0) {
      $messages.find(".mCSB_container").height(totalHeight);
    }
    
    $messages
      .mCustomScrollbar("update")
      .mCustomScrollbar("scrollTo", "bottom", {
        scrollInertia: 10,
        timeout: 0,
      });
  }

  function setDate() {
    d = new Date();
    if (m != d.getMinutes()) {
      m = d.getMinutes();
      $('<div class="timestamp">' + d.getHours() + ":" + m + "</div>").appendTo(
        $(".message:last")
      );
    }
  }

  function callChatbotApi(message) {
    // params, body, additionalParams
    return sdk.chatbotPost(
      {},
      {
        messages: [
          {
            type: "unstructured",
            unstructured: {
              text: message,
            },
          },
        ],
      },
      {}
    );
  }

  function insertMessage() {
    msg = $(".message-input").val();
    if ($.trim(msg) == "") {
      return false;
    }
    $('<div class="message message-personal">' + msg + "</div>")
      .appendTo($(".mCSB_container"))
      .addClass("new");
    setDate();
    $(".message-input").val(null);
    updateScrollbar();

    callChatbotApi(msg)
      .then((response) => {
        console.log(response);
        var data = response.data;
        let reply_message;

        if (data.body) {
          reply_message = JSON.parse(data.body)["botReply"];
          for (const msg of reply_message) {
            insertResponseMessage(msg);
          }
        } else {
          insertResponseMessage(
            "Oops, something went wrong. Please try again."
          );
        }
      })
      .catch((error) => {
        console.log("an error occurred", error);
        insertResponseMessage("Oops, something went wrong. Please try again.");
      });
  }

  $(".message-submit").click(function () {
    insertMessage();
  });

  $(window).on("keydown", function (e) {
    if (e.which == 13) {
      insertMessage();
      return false;
    }
  });

  function insertResponseMessage(content) {
    $(
      '<div class="message loading new"><figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure><span></span></div>'
    ).appendTo($(".mCSB_container"));
    updateScrollbar();

    setTimeout(function () {
      $(".message.loading").remove();
      $(
        '<div class="message new"><figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure>' +
          content +
          "</div>"
      )
        .appendTo($(".mCSB_container"))
        .addClass("new");
      setDate();
      updateScrollbar();
      i++;
    }, 500);
  }
});
