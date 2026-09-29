// Spike: Apps Script bridge. Runs in the owner's own Google account as a private web app.
// The local agent POSTs {secret, action, args}. No "send" action exists: read and draft only.

function doPost(e) {
  var req = JSON.parse((e.postData && e.postData.contents) || '{}');
  if (req.secret !== SECRET) return out({ ok: false, error: 'unauthorized' });
  var fn = ACTIONS[req.action];
  if (!fn) return out({ ok: false, error: 'unknown action' });
  try {
    return out({ ok: true, result: fn(req.args || {}) });
  } catch (err) {
    return out({ ok: false, error: String(err) });
  }
}

function doGet() {
  return out({ ok: false, error: 'unauthorized' });
}

var ACTIONS = {
  'gmail.search': function (a) {
    return GmailApp.search(a.q || 'in:inbox', 0, a.max || 5).map(function (t) {
      var m = t.getMessages().pop();
      return { thread: t.getId(), subject: t.getFirstMessageSubject(), from: m.getFrom(), date: m.getDate(), snippet: m.getPlainBody().slice(0, 200) };
    });
  },
  'gmail.draft': function (a) {
    return GmailApp.createDraft(a.to, a.subject, a.body).getId();
  },
  'sheets.create': function (a) {
    return SpreadsheetApp.create(a.title).getId();
  },
  'sheets.append': function (a) {
    SpreadsheetApp.openById(a.id).getSheets()[0].appendRow(a.row);
    return true;
  },
  'sheets.read': function (a) {
    return SpreadsheetApp.openById(a.id).getSheets()[0].getDataRange().getValues();
  },
  'docs.create': function (a) {
    return DocumentApp.create(a.title).getId();
  },
  'docs.append': function (a) {
    DocumentApp.openById(a.id).getBody().appendParagraph(a.text);
    return true;
  },
  'docs.read': function (a) {
    return DocumentApp.openById(a.id).getBody().getText();
  },
  // Spike cleanup only (a customer account runs this test): remove what the test created.
  'gmail.deleteDraft': function (a) {
    GmailApp.getDraft(a.id).deleteDraft();
    return true;
  },
  'drive.trash': function (a) {
    DriveApp.getFileById(a.id).setTrashed(true);
    return true;
  },
};

// Run once from the editor. Apps Script asks for every scope the project uses on the first run,
// so one harmless read is enough — nothing is created in the account.
function authorize() {
  GmailApp.getInboxUnreadCount();
}

function out(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
