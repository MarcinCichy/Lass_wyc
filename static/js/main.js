$(document).ready(function() {

  // Handler dla przycisku plus – otwiera ukryty input pliku
  $("#plusButton").click(function() {
    console.log("Plus button clicked");
    $("#fileInput").click();
  });

  // Handler dla przycisku zmiany motywu (dark/light)
  $("#themeToggle").click(function(){
    var darkTheme = $("#themeToggle").data("darkTheme");
    if(darkTheme === undefined) darkTheme = true;
    if(darkTheme) {
      $("#themeStylesheet").attr("href", "https://stackpath.bootstrapcdn.com/bootswatch/4.5.0/flatly/bootstrap.min.css");
      $("#themeIcon").text("☾");
      $("#themeToggle").data("darkTheme", false);
      $("body").addClass("light-theme");
    } else {
      $("#themeStylesheet").attr("href", "https://stackpath.bootstrapcdn.com/bootswatch/4.5.0/darkly/bootstrap.min.css");
      $("#themeIcon").text("☀");
      $("#themeToggle").data("darkTheme", true);
      $("body").removeClass("light-theme");
    }
  });

  // Handler dla checkboxa "select all" w nagłówku tabeli Detale
  $(document).on("change", "#selectAllCheckbox", function() {
    var checked = $(this).prop("checked");
    $(".detailCheckbox").prop("checked", checked);
    recalcSummary();
  });

  function generateProgramId() {
    return 'program_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
  }

  function formatSecondsToHMS(seconds) {
    var h = Math.floor(seconds / 3600);
    var m = Math.floor((seconds % 3600) / 60);
    var s = seconds % 60;
    return (h < 10 ? "0" + h : h) + ":" +
           (m < 10 ? "0" + m : m) + ":" +
           (s < 10 ? "0" + s : s);
  }

  // Funkcja do ładowania konfiguracji z backendu
  function loadConfig() {
    $.ajax({
      url: '/get_config',
      type: 'GET',
      dataType: 'json',
      success: function(configData) {
        $("#cuttingCostBlack").val(configData.cutting_costs.stal_czarna);
        $("#cuttingCostStainless").val(configData.cutting_costs.stal_nierdzewna);
        $("#cuttingCostAluminium").val(configData.cutting_costs.aluminium);
        $("#materialCostBlack").val(configData.material_costs.stal_czarna);
        $("#materialCostStainless").val(configData.material_costs.stal_nierdzewna);
        $("#materialCostAluminium").val(configData.material_costs.aluminium);
        $("#bendingCostSum").val(configData.suma_kosztow_giecia);
      },
      error: function(xhr, status, error) {
        console.error("Błąd przy pobieraniu konfiguracji:", error);
      }
    });
  }

  // Wywołujemy loadConfig przy ładowaniu strony
  loadConfig();

  // Funkcja updateConfig – wysyła nowe wartości z panelu do backendu, a następnie przelicza ceny w tabeli
  function updateConfig() {
    var newConfig = {
      cutting_costs: {
        stal_czarna: parseFloat($("#cuttingCostBlack").val()),
        stal_nierdzewna: parseFloat($("#cuttingCostStainless").val()),
        aluminium: parseFloat($("#cuttingCostAluminium").val())
      },
      material_costs: {
        stal_czarna: parseFloat($("#materialCostBlack").val()),
        stal_nierdzewna: parseFloat($("#materialCostStainless").val()),
        aluminium: parseFloat($("#materialCostAluminium").val())
      },
      suma_kosztow_giecia: parseFloat($("#bendingCostSum").val())
    };
    $.ajax({
      url: '/update_config',
      type: 'POST',
      data: JSON.stringify(newConfig),
      contentType: 'application/json',
      success: function(response) {
        console.log("Konfiguracja zaktualizowana:", response);
        recalcAllRows();
        recalcSummary();
      },
      error: function(xhr, status, error) {
        console.error("Błąd przy aktualizacji konfiguracji:", error);
      }
    });
  }

  // Nasłuchiwanie zmian w polach formularza w panelu bocznym
  $("#pricingForm input").on("change", function() {
    updateConfig();
  });

  // Funkcje do pobierania stawek z formularza na podstawie tekstu z kolumny "Materiał"
  function getCuttingRate(material) {
    material = material.toLowerCase();
    if (material.indexOf("1.4301") !== -1) {
      return parseFloat($("#cuttingCostStainless").val()) || 0;
    } else if (material.indexOf("1.0038") !== -1 || material.indexOf("st37") !== -1) {
      return parseFloat($("#cuttingCostBlack").val()) || 0;
    } else if (material.indexOf("aluminium") !== -1) {
      return parseFloat($("#cuttingCostAluminium").val()) || 0;
    }
    return parseFloat($("#cuttingCostBlack").val()) || 0;
  }

  function getMaterialRate(material) {
    material = material.toLowerCase();
    if (material.indexOf("1.4301") !== -1) {
      return parseFloat($("#materialCostStainless").val()) || 0;
    } else if (material.indexOf("1.0038") !== -1 || material.indexOf("st37") !== -1) {
      return parseFloat($("#materialCostBlack").val()) || 0;
    } else if (material.indexOf("aluminium") !== -1) {
      return parseFloat($("#materialCostAluminium").val()) || 0;
    }
    return parseFloat($("#materialCostBlack").val()) || 0;
  }

  // Funkcja przeliczająca koszty dla jednego wiersza detalu
  function recalcRow($row) {
    var cutTime = parseFloat($row.data("cut-time")) || 0; // czas cięcia w godzinach
    var weight = parseFloat($row.data("weight")) || 0;
    var material = $row.find("td").eq(3).text();
    var newCuttingRate = getCuttingRate(material);
    var newMaterialRate = getMaterialRate(material);
    var newCuttingCost = cutTime * newCuttingRate;
    var newMaterialCost = weight * newMaterialRate;
    var baseCost = newCuttingCost + newMaterialCost;
    var bendingCount = parseFloat($row.find("input.bending-input").val()) || 0;
    if (bendingCount < 0) {
      bendingCount = 0;
      $row.find("input.bending-input").val(0);
    }
    var bendingCost = parseFloat($("#bendingCostSum").val()) || 0;
    var newDetailCost = baseCost + (bendingCount * bendingCost);
    // Ustawiamy wartości w kolumnach: Koszt cięcia (11), Koszt materiału (12), Koszt detalu (13)
    $row.find("td").eq(11).text(newCuttingCost.toFixed(2));
    $row.find("td").eq(12).text(newMaterialCost.toFixed(2));
    $row.find("td").eq(13).text(newDetailCost.toFixed(2));

    // Ostatnia kolumna: Całkowity koszt
    var quantity = parseFloat($row.find("td").eq(10).text()) || 1;
    var totalCost = newDetailCost * quantity;
    $row.find("td").eq(14).text(totalCost.toFixed(2));
  }

  // Przeliczenie wszystkich wierszy
  function recalcAllRows() {
    $("#detailsTableBody tr").each(function(){
      recalcRow($(this));
    });
  }

  // Funkcja przeliczająca podsumowanie wyceny w karcie "Wycena:"
  function recalcSummary() {
    console.log("RecalcSummary() wywołane");
    var detailCount = 0;
    var totalCuttingCost = 0;
    var totalMaterialCost = 0;
    var totalPrice = 0;
    var materialBreakdown = {};

    $("#detailsTableBody tr").each(function(){
      var $row = $(this);
      // Sprawdzamy, czy checkbox w pierwszej kolumnie jest zaznaczony
      if ($row.find("input.detailCheckbox").prop("checked")) {
        var qty = parseFloat($row.find("td").eq(10).text()) || 1;
        detailCount += qty;
        var cuttingCost = parseFloat($row.find("td").eq(11).text()) || 0;
        totalCuttingCost += cuttingCost;
        var materialCost = parseFloat($row.find("td").eq(12).text()) || 0;
        totalMaterialCost += materialCost;
        var rowTotal = parseFloat($row.find("td").eq(14).text()) || 0;
        totalPrice += rowTotal;
        var materialText = $row.find("td").eq(3).text().toLowerCase();
        var key = "Inne";
        if (materialText.indexOf("1.0038") !== -1 || materialText.indexOf("st37") !== -1) {
          key = "Stal czarna";
        } else if (materialText.indexOf("1.4301") !== -1) {
          key = "Stal nierdzewna";
        } else if (materialText.indexOf("aluminium") !== -1) {
          key = "Aluminium";
        }
        if (!materialBreakdown[key]) {
          materialBreakdown[key] = 0;
        }
        materialBreakdown[key] += materialCost;
      }
    });

    var summaryHtml = "<p>Ilość detali: " + detailCount + "</p>";
    summaryHtml += "<p>Łączny koszt cięcia: " + totalCuttingCost.toFixed(2) + "</p>";
    summaryHtml += "<p>Łączny koszt materiału:</p><ul>";
    for (var key in materialBreakdown) {
      summaryHtml += "<li>" + key + ": " + materialBreakdown[key].toFixed(2) + "</li>";
    }
    summaryHtml += "</ul>";
    summaryHtml += "<p>Całkowita cena: " + totalPrice.toFixed(2) + "</p>";

    $("#pricingSummary").html(summaryHtml);
  }

  // Nasłuchiwanie zmian w polach "Ilość gięć" w tabeli detali
  $(document).on("change", ".bending-input", function() {
    var $row = $(this).closest("tr");
    recalcRow($row);
    recalcSummary();
  });

  // Nasłuchiwanie zmian checkboxów detali
  $(document).on("change", ".detailCheckbox", function() {
    recalcSummary();
  });

  // Obsługa uploadu pliku
  $("#fileInput").change(function(){
    var fileName = $(this).val().split("\\").pop();
    var programId = generateProgramId();
    $("#loading").show();
    var file = $(this)[0].files[0];
    if (!file) return;
    var formData = new FormData();
    formData.append("file", file);

    $.ajax({
      url: '/upload',
      type: 'POST',
      data: formData,
      contentType: false,
      processData: false,
      success: function(response) {
        $("#loading").hide();
        // Dodajemy wiersz programu do tabeli programów
        var programsTbody = $("#programsTableBody");
        var progRow = "<tr data-program-id='" + programId + "'>";
        progRow += "<td><button class='btn btn-danger btn-sm remove-program' data-program-id='" + programId + "'>-</button></td>";
        progRow += "<td>" + (response.name || "") + "</td>";
        progRow += "<td>" + (response.material || "") + "</td>";
        progRow += "<td>" + (response.thicknes || "") + "</td>";
        progRow += "<td>" + (response.machine_time || "") + "</td>";
        progRow += "<td>" + (response.program_counts || "") + "</td>";
        progRow += "</tr>";
        programsTbody.append(progRow);

        // Dodajemy wiersze detali do tabeli
        var detailsTbody = $("#detailsTableBody");
        response.details.forEach(function(detail) {
          // W kolumnach "Koszt detalu" i "Całkowity koszt" wstawiamy puste wartości (zamiast detail.total_cost)
          var detailRow = "<tr data-program-id='" + programId + "' data-cut-time='" + detail.cut_time + "' data-weight='" + detail.weight + "'>";
          detailRow += "<td><input type='checkbox' class='detailCheckbox' checked></td>";
          if(detail.image_path) {
            detailRow += "<td><img src='" + detail.image_path + "' alt='Rysunek' style='max-width:100px;'></td>";
          } else {
            detailRow += "<td></td>";
          }
          detailRow += "<td>" + detail.name + "</td>";
          detailRow += "<td>" + (response.material || "") + "</td>";
          detailRow += "<td>" + (response.thicknes || "") + "</td>";
          detailRow += "<td>" + (detail.dim_x || "") + "</td>";
          detailRow += "<td>" + (detail.dim_y || "") + "</td>";
          detailRow += "<td>" + parseFloat(detail.weight).toFixed(2) + "</td>"; // waga
          // Ilość gięć
          detailRow += "<td><input type='number' class='bending-input' value='0' min='0' style='width:100%; background:inherit; border:none; text-align:center;'/></td>";
          // Czas cięcia
          detailRow += "<td>" + formatSecondsToHMS(detail.cut_time * 3600) + "</td>";
          // Ilość
          detailRow += "<td>" + detail.quantity + "</td>";
          // Koszt cięcia (puste, bo recalcRow ustawi)
          detailRow += "<td></td>";
          // Koszt materiału (puste)
          detailRow += "<td></td>";
          // Koszt detalu (puste)
          detailRow += "<td></td>";
          // Całkowity koszt (puste)
          detailRow += "<td></td>";
          detailRow += "</tr>";
          detailsTbody.append(detailRow);
        });

        // Jeśli plugin colResizable jest dostępny, inicjujemy go
        if (typeof $.fn.colResizable === "function") {
          $("#detailsTable").colResizable({ liveDrag: true });
        } else {
          console.warn("colResizable plugin is not loaded");
        }

        // Automatycznie przeliczamy wiersze i podsumowanie po dodaniu
        recalcAllRows();
        setTimeout(function() {
          recalcSummary();
        }, 300);
      },
      error: function(xhr) {
        $("#loading").hide();
        alert("Wystąpił błąd: " + xhr.responseJSON.error);
      }
    });
  });

  // Obsługa usuwania programu
  $(document).on("click", ".remove-program", function(){
    var programId = $(this).data("program-id");
    $("#programsTableBody tr[data-program-id='" + programId + "']").remove();
    $("#detailsTableBody tr[data-program-id='" + programId + "']").remove();
    recalcSummary();
  });
});


$("#sidebarToggle").click(function(){
  $("#sidebar").toggleClass("expanded");
  if ($("#sidebar").hasClass("expanded")) {
    $(".main-container").removeClass("collapsed").addClass("expanded");
    $(this).text("〈");
  } else {
    $(".main-container").removeClass("expanded").addClass("collapsed");
    $(this).text("〉");
  }
});

document.getElementById("themeToggle").addEventListener("click", function() {
    document.body.classList.toggle("light-mode");
    const themeIcon = document.getElementById("themeIcon");
    if (document.body.classList.contains("light-mode")) {
        themeIcon.textContent = "🌙";
    } else {
        themeIcon.textContent = "☀";
    }
});