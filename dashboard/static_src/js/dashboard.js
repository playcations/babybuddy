/* Baby Buddy Dashboard
 *
 * Provides a "watch" function to update the dashboard at one minute intervals
 * and/or on visibility state changes.
 */
BabyBuddy.Dashboard = (function ($) {
  var runIntervalId = null;
  var dashboardElement = null;
  var hidden = null;

  var Dashboard = {
    watch: function (element_id, refresh_rate) {
      dashboardElement = $("#" + element_id);

      if (dashboardElement.length == 0) {
        console.error("Baby Buddy: Dashboard element not found.");
        return false;
      }

      if (typeof document.hidden !== "undefined") {
        hidden = "hidden";
      } else if (typeof document.msHidden !== "undefined") {
        hidden = "msHidden";
      } else if (typeof document.webkitHidden !== "undefined") {
        hidden = "webkitHidden";
      }

      if (
        typeof window.addEventListener === "undefined" ||
        typeof document.hidden === "undefined"
      ) {
        if (refresh_rate) {
          runIntervalId = setInterval(this.update, refresh_rate);
        }
      } else {
        window.addEventListener(
          "focus",
          Dashboard.handleVisibilityChange,
          false,
        );
        if (refresh_rate) {
          runIntervalId = setInterval(
            Dashboard.handleVisibilityChange,
            refresh_rate,
          );
        }
      }
    },

    handleVisibilityChange: function () {
      if (!document[hidden]) {
        Dashboard.update();
      }
    },

    update: function () {
      // TODO: Someday maybe update in place?
      location.reload();
    },
  };

  // Get CSRF token from cookie
  function getCsrfToken() {
    var cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      var cookies = document.cookie.split(";");
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, 10) === "csrftoken=") {
          cookieValue = decodeURIComponent(cookie.substring(10));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Medicine status card button handlers
  $(document).on("click", ".repeat-dose-btn", function () {
    var btn = $(this);
    var url = btn.data("url");
    var name = btn.data("medicine-name");

    if (!confirm("Repeat dose of " + name + "?")) {
      return;
    }

    $.ajax({
      url: url,
      type: "POST",
      headers: {
        "X-CSRFToken": getCsrfToken(),
      },
      success: function (response) {
        location.reload();
      },
      error: function (xhr) {
        alert(
          "Error: " + (xhr.responseJSON?.message || "Failed to repeat dose"),
        );
      },
    });
  });

  $(document).on("click", ".remove-medicine-btn", function () {
    var btn = $(this);
    var url = btn.data("url");
    var name = btn.data("medicine-name");

    if (!confirm("Remove " + name + " from active tracking?")) {
      return;
    }

    $.ajax({
      url: url,
      type: "POST",
      headers: {
        "X-CSRFToken": getCsrfToken(),
      },
      success: function (response) {
        location.reload();
      },
      error: function (xhr) {
        alert(
          "Error: " +
            (xhr.responseJSON?.message || "Failed to remove medication"),
        );
      },
    });
  });

  return Dashboard;
})(jQuery);
