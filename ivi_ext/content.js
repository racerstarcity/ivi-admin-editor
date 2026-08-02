(function() {
  if (document.getElementById('ivi-fill-btn')) return;

  var btn = document.createElement('button');
  btn.id = 'ivi-fill-btn';
  btn.textContent = 'Заполнить из IVI';
  btn.style.cssText =
    'position:fixed;top:10px;right:10px;z-index:9999;' +
    'background:#0d6efd;color:white;border:none;border-radius:6px;' +
    'padding:10px 18px;font:bold 14px sans-serif;cursor:pointer;' +
    'box-shadow:0 2px 8px rgba(0,0,0,.3);';

  var loading = false;
  btn.onclick = function() {
    if (loading) return;
    loading = true;
    btn.textContent = 'Загрузка...';
    btn.style.background = '#6c757d';

    fetch('http://localhost:8766')
      .then(function(r) { return r.json(); })
      .then(function(d) {
        if (d.error) { alert('Ошибка: ' + d.error); return; }

        function arrow(el) {
          if (!el) return;
          el.dispatchEvent(new KeyboardEvent('keydown', {key:'ArrowRight',keyCode:39,bubbles:true}));
          el.dispatchEvent(new KeyboardEvent('keyup', {key:'ArrowRight',keyCode:39,bubbles:true}));
        }
        function doubleArrow(el) { arrow(el); arrow(el); }

        var parent = document.querySelector('.middroll_block tbody') || document.querySelector('.middroll_block');
        for (var i = 1; i < d.midrolls.length; i++) {
          var tf = document.getElementById('id_middroll-TOTAL_FORMS');
          tf.value = parseInt(tf.value) + 1;
          var first = document.querySelector('.middroll_block .middroll_formset_tr');
          if (!first) break;
          var row = first.cloneNode(true);
          row.querySelectorAll('[name],[id]').forEach(function(el) {
            if (el.name) el.name = el.name.replace('middroll-0-', 'middroll-' + i + '-');
            if (el.id) el.id = el.id.replace('middroll-0-', 'middroll-' + i + '-');
            if (el.type == 'checkbox') el.checked = false;
            if (el.type == 'text' || el.type == 'hidden') el.value = '';
          });
          parent.appendChild(row);
        }

        d.midrolls.forEach(function(v, i) {
          var inp = document.getElementById('id_middroll-' + i + '-time');
          if (inp) { inp.value = v; inp.dispatchEvent(new Event('input', {bubbles:true})); doubleArrow(inp); }
        });

        function findOrCreateLocRow(markerType, startVal, finishVal) {
          var sel = document.querySelector('[name$="-marker_type"]');
          if (!sel) return;
          var prefix = sel.name.replace('-marker_type', '');
          var baseIdx = prefix.match(/\d+$/);
          if (!baseIdx) return;
          var idx0 = parseInt(baseIdx[0]);

          // Try to find existing row with this marker_type, or first empty row
          var allTypes = document.querySelectorAll('[name$="-marker_type"]');
          var existingRow = null;
          var emptyRow = null;
          allTypes.forEach(function(el) {
            if (el.name.indexOf('__prefix__') != -1) return;
            if (el.value == markerType) existingRow = el;
            if (!emptyRow && el.value == '') emptyRow = el;
          });
          var target = existingRow || emptyRow;
          if (target) {
            var rowPrefix = target.name.replace('-marker_type', '');
            target.value = markerType;
            target.dispatchEvent(new Event('change', {bubbles:true}));
            document.getElementById('id_' + rowPrefix + '-start').value = startVal;
            arrow(document.getElementById('id_' + rowPrefix + '-start'));
            document.getElementById('id_' + rowPrefix + '-finish').value = finishVal;
            arrow(document.getElementById('id_' + rowPrefix + '-finish'));
            return;
          }

          // Add new row
          var tf = document.querySelector('[name="localization_labels-TOTAL_FORMS"]');
          var n = parseInt(tf.value);
          tf.value = n + 1;
          var tbody = document.querySelector('.localization_labels_tr').closest('tbody');
          var first = tbody.querySelector('.localization_labels_tr');
          var row = first.cloneNode(true);
          row.querySelectorAll('[name],[id]').forEach(function(el) {
            if (el.name) el.name = el.name.replace('localization_labels-' + idx0 + '-', 'localization_labels-' + n + '-');
            if (el.id) el.id = el.id.replace('localization_labels-' + idx0 + '-', 'localization_labels-' + n + '-');
            if (el.type == 'checkbox') el.checked = false;
            if (el.type != 'select-one') el.value = '';
          });
          tbody.appendChild(row);
          document.getElementById('id_localization_labels-' + n + '-marker_type').value = markerType;
          document.getElementById('id_localization_labels-' + n + '-start').value = startVal;
          arrow(document.getElementById('id_localization_labels-' + n + '-start'));
          document.getElementById('id_localization_labels-' + n + '-finish').value = finishVal;
          arrow(document.getElementById('id_localization_labels-' + n + '-finish'));
        }

        if (d.finish_scale > 0) {
          findOrCreateLocRow('2', d.start_scale, d.finish_scale);
        }

        if (d.finish_prev > 0) {
          findOrCreateLocRow('1', d.start_prev, d.finish_prev);
        }

        var cr = document.getElementById('id_credits_begin_time');
        if (cr) { cr.value = d.postroll; arrow(cr); }
        var du = document.getElementById('id_duration');
        if (du) { du.value = d.duration; arrow(du); }

        document.querySelectorAll('.localization_formset_tr').forEach(function(row) {
          var lang = row.querySelector('select[name$="-localization_type"]');
          if (!lang || !lang.value) return;
          var idx = lang.name.match(/localizations-(\d+)-/);
          if (!idx) return;
          var i = idx[1];
          var dur = row.querySelector('[name="localizations-' + i + '-duration"]');
          if (dur) { dur.value = d.duration; arrow(dur); }
          var cr2 = row.querySelector('[name="localizations-' + i + '-credits_begin_time"]');
          if (cr2) { cr2.value = d.postroll; arrow(cr2); }
          function findInnerLocRow(row, markerType, startVal, finishVal) {
            var allTypes = row.querySelectorAll('[name^="custom_localization_labels-localizations-' + i + '-form-"][name$="-marker_type"]');
            var existing = null;
            var emptyRow = null;
            allTypes.forEach(function(el) {
              if (el.name.indexOf('__prefix__') != -1) return;
              if (el.value == markerType) existing = el;
              if (!emptyRow && el.value == '') emptyRow = el;
            });
            var target = existing || emptyRow;
            if (target) {
              var p = target.name.replace('-marker_type', '');
              target.value = markerType;
              target.dispatchEvent(new Event('change', {bubbles:true}));
              var inpS = row.querySelector('[name="' + p + '-start"]');
              if (inpS) { inpS.value = startVal; arrow(inpS); }
              var inpF = row.querySelector('[name="' + p + '-finish"]');
              if (inpF) { inpF.value = finishVal; arrow(inpF); }
              return;
            }
            var tf = row.querySelector('[name^="custom_localization_labels-localizations-' + i + '-form-TOTAL_FORMS"]');
            if (!tf) return;
            var n = parseInt(tf.value);
            tf.value = n + 1;
            var emptyForm = row.querySelector('.empty-form.nested-loc-form');
            if (!emptyForm) return;
            var newRow = emptyForm.cloneNode(true);
            newRow.classList.remove('empty-form');
            newRow.querySelectorAll('[name],[id]').forEach(function(el) {
              if (el.name) el.name = el.name.replace(/form-__prefix__-/, 'form-' + n + '-');
              if (el.id) el.id = el.id.replace(/form-__prefix__-/, 'form-' + n + '-');
              if (el.type == 'checkbox') el.checked = false;
              if (el.type != 'select-one') el.value = '';
            });
            emptyForm.parentNode.insertBefore(newRow, emptyForm);
            var mt = newRow.querySelector('[name$="-marker_type"]');
            if (mt) { mt.value = markerType; mt.dispatchEvent(new Event('change', {bubbles:true})); }
            var inpS = newRow.querySelector('[name$="-start"]');
            if (inpS) { inpS.value = startVal; arrow(inpS); }
            var inpF = newRow.querySelector('[name$="-finish"]');
            if (inpF) { inpF.value = finishVal; arrow(inpF); }
          }
          if (d.finish_scale > 0) {
            findInnerLocRow(row, '2', d.start_scale, d.finish_scale);
          }
          if (d.finish_prev > 0) {
            findInnerLocRow(row, '1', d.start_prev, d.finish_prev);
          }
        });

        alert('Готово! Форма заполнена.');
      })
      .catch(function(e) {
        alert('Ошибка подключения к серверу: ' + e.message + '\n\nУбедитесь, что ivi_meta.exe запущен.');
      })
      .then(function() {
        loading = false;
        btn.textContent = 'Заполнить из IVI';
        btn.style.background = '#0d6efd';
      });
  };

  document.body.appendChild(btn);
})();

// Auto-sync: detect video state and notify ivi_meta
(function() {
  var lastSent = 0;

  function sync(state, time, duration) {
    var url = 'http://localhost:8766/sync?state=' + encodeURIComponent(state);
    if (time !== undefined) url += '&time=' + Math.floor(time);
    if (duration !== undefined) url += '&duration=' + Math.floor(duration);
    fetch(url).catch(function(e) {
      console.error('ivi-sync error:', e);
    });
  }

  function setupVideo(video) {
    if (video.dataset.iviSync) return;
    video.dataset.iviSync = '1';

    var sendWithDuration = function(state, time) {
      sync(state, time, video.duration || undefined);
    };

    // Send initial state with duration
    sendWithDuration(video.paused ? 'pause' : 'play', video.currentTime);

    video.addEventListener('loadedmetadata', function() {
      sendWithDuration(video.paused ? 'pause' : 'play', video.currentTime);
    });
    video.addEventListener('play', function() {
      sendWithDuration('play', video.currentTime);
    });
    video.addEventListener('pause', function() {
      sendWithDuration('pause', video.currentTime);
    });
    video.addEventListener('seeked', function() {
      sendWithDuration(video.paused ? 'pause' : 'seek', video.currentTime);
    });
    // timeupdate as fallback for custom players
    video.addEventListener('timeupdate', function() {
      var now = Date.now();
      if (now - lastSent >= 1000) {
        lastSent = now;
        if (!video.paused) sendWithDuration('play', video.currentTime);
      }
    });
  }

  function findVideos() {
    document.querySelectorAll('video:not([data-ivi-sync])').forEach(setupVideo);
  }

  findVideos();
  var observer = new MutationObserver(findVideos);
  observer.observe(document.body, { childList: true, subtree: true });
})();

// Hotkeys from browser: 1-7 trigger markers in ivi_meta
(function() {
  var keyMap = {
    '1': 'midroll',
    '2': 'start_scale',
    '3': 'finish_scale',
    '4': 'start_prev',
    '5': 'finish_prev',
    '6': 'postroll',
    '7': 'duration',
  };

  function getVideoTime() {
    var v = document.querySelector('video');
    return v ? Math.floor(v.currentTime) : 0;
  }

  document.addEventListener('keydown', function(e) {
    // Ctrl+M → click "Заполнить из IVI"
    if (e.ctrlKey && (e.key === 'm' || e.key === 'M')) {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) return;
      e.preventDefault();
      var fillBtn = document.getElementById('ivi-fill-btn');
      if (fillBtn) fillBtn.click();
      return;
    }
    var digit = e.key;
    // Allow numpad digits too (e.key may be digit with numlock ON)
    if (!(digit >= '1' && digit <= '7') && e.code.indexOf('Numpad') === 0) {
      digit = e.code.replace('Numpad', '');
    }
    var marker = keyMap[digit];
    if (!marker) return;
    // Don't trigger if typing in an input/textarea
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) return;
    e.preventDefault();
    var t = getVideoTime();
    fetch('http://localhost:8766/sync?key=' + marker + '&time=' + t).catch(function(err) {
      console.error('ivi-key error:', err);
    });
  });
})();

// Import from card: collect form data back into ivi_meta
(function() {
  var lastReqId = 0;

  function collectFromForm() {
    var out = {
      midrolls: [], start_scale: 0, finish_scale: 0,
      start_prev: 0, finish_prev: 0, postroll: 0, duration: 0
    };
    var found = false;

    // поля админки имеют class="thousand_separator" — значения вида "2 550"
    function num(v) {
      if (v === undefined || v === null) return NaN;
      return parseFloat(String(v).replace(/[^\d.\-]/g, ''));
    }

    var tf = document.getElementById('id_middroll-TOTAL_FORMS');
    if (tf) {
      var count = parseInt(tf.value) || 0;
      for (var i = 0; i < count; i++) {
        var inp = document.getElementById('id_middroll-' + i + '-time');
        if (inp && inp.value !== '') {
          var v = num(inp.value);
          if (!isNaN(v)) { out.midrolls.push(Math.round(v)); found = true; }
        }
      }
    }

    document.querySelectorAll('[name$="-marker_type"]').forEach(function(el) {
      if (el.name.indexOf('__prefix__') != -1) return;
      var p = el.name.replace('-marker_type', '');
      var s = document.getElementById('id_' + p + '-start');
      var f = document.getElementById('id_' + p + '-finish');
      var sv = s ? num(s.value) : NaN;
      var fv = f ? num(f.value) : NaN;
      if (el.value == '2') {
        out.start_scale = isNaN(sv) ? 0 : Math.round(sv);
        out.finish_scale = isNaN(fv) ? 0 : Math.round(fv);
        found = true;
      } else if (el.value == '1') {
        out.start_prev = isNaN(sv) ? 0 : Math.round(sv);
        out.finish_prev = isNaN(fv) ? 0 : Math.round(fv);
        found = true;
      }
    });

    var cr = document.getElementById('id_credits_begin_time');
    if (cr && cr.value !== '') {
      var pv = num(cr.value);
      if (!isNaN(pv)) { out.postroll = Math.round(pv); found = true; }
    }
    var du = document.getElementById('id_duration');
    if (du && du.value !== '') {
      var dv = num(du.value);
      if (!isNaN(dv)) { out.duration = Math.round(dv); found = true; }
    }

    return {data: out, found: found};
  }

  function pollImport() {
    fetch('http://localhost:8766/import_request')
      .then(function(r) { return r.json(); })
      .then(function(res) {
        var rid = res.req_id || 0;
        if (rid === 0 || rid === lastReqId) return;
        var collected = collectFromForm();
        var payload;
        if (!collected.found) {
          payload = {id: rid, error: 'форма карточки не найдена на этой странице — откройте карточку'};
        } else {
          payload = {id: rid, data: collected.data};
        }
        fetch('http://localhost:8766/import', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        }).then(function() {
          lastReqId = rid;
        }).catch(function(e) {
          console.error('ivi-import-post error:', e);
        });
      })
      .catch(function() {});
  }

  setInterval(pollImport, 2000);
  setTimeout(pollImport, 500);
})();
