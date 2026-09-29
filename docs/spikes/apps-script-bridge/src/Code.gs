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
};

// Run once from the editor: triggers the single consent screen for every scope above.
function authorize() {
  GmailApp.getInboxUnreadCount();
  SpreadsheetApp.create('assistantOS authorize check');
  DocumentApp.create('assistantOS authorize check');
}

function out(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
