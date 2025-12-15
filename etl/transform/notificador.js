/***************
 * CONFIG
 ***************/
const CONFIG = {
  HIST_SHEET_NAME: 'HistÇürico',
  RESP_SHEET_NAME: 'ResponsÇ­veis',
  HIST_COL_REGION: 1,    // A
  HIST_COL_TIMESTAMP: 2, // B
  HIST_COL_LAT: 3,       // C
  HIST_COL_LNG: 4,       // D
  HIST_COL_NOTIFIED: 5   // E
};

/**
 * HTTP GET entrypoint
 * Expects query params: regionId, timestamp, lat, lng
 *
 * Example:
 *  https://script.google.com/macros/s/DEPLOYMENT_ID/exec?regionId=R1&timestamp=2025-12-08T20:00:00Z&lat=-22.9&lng=-43.2
 */
function doGet(e) {
  try {
    // --- 1. Validate and extract params ---
    if (!e || !e.parameter) {
      return jsonResponse({ success: false, error: 'Missing parameters object' }, 400);
    }

    const regionId  = e.parameter.regionId;
    const ts        = e.parameter.timestamp;
    const lat       = e.parameter.lat;
    const lng       = e.parameter.lng;

    if (!regionId || !ts || !lat || !lng) {
      return jsonResponse({
        success: false,
        error: 'Missing one or more required params: regionId, timestamp, lat, lng'
      }, 400);
    }

    // --- 1.1. Validate timestamp format (Brazilian dd/MM/yyyy HH:mm[:ss]) ---
    if (!isBrazilianDateTime(ts)) {
      return jsonResponse({
        success: false,
        error: 'timestamp must be in Brazilian format dd/MM/yyyy HH:mm[:ss]'
      }, 400);
    }
    const tsBr = toBrasilia(ts); // normalized to America/Sao_Paulo

    const ss = SpreadsheetApp.getActive();
    const histSheet = ss.getSheetByName(CONFIG.HIST_SHEET_NAME);
    const respSheet = ss.getSheetByName(CONFIG.RESP_SHEET_NAME);

    if (!histSheet) {
      return jsonResponse({ success: false, error: 'HistÇürico sheet not found' }, 500);
    }
    if (!respSheet) {
      return jsonResponse({ success: false, error: 'ResponsÇ­veis sheet not found' }, 500);
    }

    // --- 2. Skip duplicates (same region + timestamp + lat + lng) ---
    const histValues = histSheet.getDataRange().getValues(); // includes header
    const duplicateRowIndex = histValues.findIndex((row, idx) => {
      if (idx === 0) return false; // assume header

      const rowRegionId = row[CONFIG.HIST_COL_REGION - 1];
      const rowTs       = row[CONFIG.HIST_COL_TIMESTAMP - 1];
      const rowLat      = row[CONFIG.HIST_COL_LAT - 1];
      const rowLng      = row[CONFIG.HIST_COL_LNG - 1];

      return (
        String(rowRegionId) === String(regionId) &&
        String(rowTs) === String(tsBr) &&
        String(rowLat) === String(lat) &&
        String(rowLng) === String(lng)
      );
    });

    if (duplicateRowIndex !== -1) {
      return jsonResponse({
        success: true,
        duplicate: true,
        message: 'Duplicate event ignored (already notified)',
        regionId: regionId,
        row: duplicateRowIndex + 1
      }, 200);
    }

    // --- 3. Append record to "HistÇürico" ---
    // We can also store "serverTime" if you want: new Date()
    const newRowValues = [
      regionId,
      tsBr,
      lat,
      lng,
      '' // placeholder for notified status
    ];

    histSheet.appendRow(newRowValues);
    const lastRow = histSheet.getLastRow();

    // --- 4. Find responsible email for the region in "ResponsÇ­veis" ---
    const respRange = respSheet.getDataRange();
    const respValues = respRange.getValues(); // 2D: [ [Region, Email], ... ]

    // Assume first row is header. You can remove "+ 1" if not.
    let responsibleEmail = null;
    for (let i = 1; i < respValues.length; i++) {
      const rowRegionId = respValues[i][0]; // Col A
      const rowEmail    = respValues[i][1]; // Col B

      if (String(rowRegionId) === String(regionId)) {
        responsibleEmail = rowEmail;
        break;
      }
    }

    if (!responsibleEmail) {
      // No responsible found: mark in HistÇürico and return
      histSheet.getRange(lastRow, CONFIG.HIST_COL_NOTIFIED).setValue('no-responsible-found');
      return jsonResponse({
        success: false,
        error: 'No responsible email found for region',
        regionId: regionId
      }, 404);
    }

    // --- 5. Send email to responsible ---
    const mapsLink = 'https://www.google.com/maps/search/?api=1&query=' + lat + ',' + lng;
    const subject = 'Novo registro na regiÇœo ' + regionId;
    const body =
      'OlÇ­,\n\n' +
      'Foi registrado um novo evento na regiÇœo ' + regionId + '.\n\n' +
      'Dados recebidos:\n' +
      ' - Timestamp (BrasÇília): ' + tsBr + '\n' +
      ' - Latitude: ' + lat + '\n' +
      ' - Longitude: ' + lng + '\n' +
      ' - Google Maps: ' + mapsLink + '\n\n' +
      'Atenciosamente,\n' +
      'Sistema de Monitoramento';

    MailApp.sendEmail(responsibleEmail, subject, body);

    // --- 6. Mark as "notified" in HistÇürico ---
    histSheet.getRange(lastRow, CONFIG.HIST_COL_NOTIFIED).setValue('notified');

    // --- 7. HTTP response ---
    return jsonResponse({
      success: true,
      message: 'Record stored and email sent',
      regionId: regionId,
      row: lastRow,
      responsibleEmail: responsibleEmail
    }, 200);

  } catch (err) {
    // Basic error handling + JSON response
    return jsonResponse({
      success: false,
      error: err && err.message ? err.message : String(err)
    }, 500);
  }
}

/**
 * Helper to create JSON HTTP response
 */
function jsonResponse(obj, statusCode) {
  const output = ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);

  // Apps Script Web Apps donƒ?Tt support status codes directly,
  // but we include it in the JSON anyway.
  // If you use an Add-on or API Executable, you can adapt this.
  return output;
}

/**
 * Validate Brazilian datetime format dd/MM/yyyy HH:mm[:ss]
 */
function isBrazilianDateTime(value) {
  if (typeof value !== 'string') return false;

  const regex = /^([0][1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0-2])\/\d{4} ([01]\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?$/;
  if (!regex.test(value)) return false;

  // Optional: basic Date validity (e.g., 31/02 rejected)
  const parts = value.split(/[\/ :]/);
  const day = parseInt(parts[0], 10);
  const month = parseInt(parts[1], 10) - 1; // zero-based
  const year = parseInt(parts[2], 10);
  const hour = parseInt(parts[3], 10);
  const minute = parseInt(parts[4], 10);
  const second = parts[5] ? parseInt(parts[5], 10) : 0;

  const d = new Date(year, month, day, hour, minute, second);
  return (
    d.getFullYear() === year &&
    d.getMonth() === month &&
    d.getDate() === day &&
    d.getHours() === hour &&
    d.getMinutes() === minute &&
    d.getSeconds() === second
  );
}

/**
 * Convert Brazilian datetime string to Brasília time (America/Sao_Paulo) and return formatted string.
 */
function toBrasilia(value) {
  if (typeof value !== 'string') return value;

  const parts = value.split(/[\/ :]/);
  const day = parseInt(parts[0], 10);
  const month = parseInt(parts[1], 10) - 1; // zero-based
  const year = parseInt(parts[2], 10);
  const hour = parseInt(parts[3], 10);
  const minute = parseInt(parts[4], 10);
  const second = parts[5] ? parseInt(parts[5], 10) : 0;

  const d = new Date(year, month, day, hour, minute, second);
  return Utilities.formatDate(d, 'America/Sao_Paulo', 'dd/MM/yyyy HH:mm:ss');
}
