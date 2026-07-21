'use strict';
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        var $ = django.jQuery;
        var $work = $('#id_work');
        var $addSpkr = $('#add_id_spkr');
        var $addAddr = $('#add_id_addr');
        if (!$work.length || (!$addSpkr.length && !$addAddr.length)) return;

        function setContextParam($link, contextText) {
            if (!$link.length) return;
            var url = new URL($link.attr('href'), window.location.href);
            url.searchParams.set('context', contextText);
            $link.attr('href', url.pathname + '?' + url.searchParams.toString());
        }

        function updateContext() {
            if (!$.fn.select2) return;
            var data = $work.select2('data');
            var text = (data && data.length) ? data[0].text : '';
            if (!text) return;
            setContextParam($addSpkr, text);
            setContextParam($addAddr, text);
        }

        $work.on('change select2:select', updateContext);
    });

    document.addEventListener('DOMContentLoaded', function() {
        var $ = django.jQuery;
        var $work = $('#id_work');
        var $lfi = $('#id_l_fi');
        var $lla = $('#id_l_la');
        var $level = $('#id_level');
        var $embeddedIn = $('#id_embedded_in');
        if (!$work.length || !$lfi.length || !$lla.length || !$level.length || !$embeddedIn.length) return;

        function adminBase() {
            var path = window.location.pathname;
            path = path.replace(/add\/$/, '');
            path = path.replace(/[^/]+\/change\/$/, '');
            return path;
        }

        var m = window.location.pathname.match(/\/(\d+)\/change\/$/);
        var currentId = m ? m[1] : null;

        function currentLevel() {
            var v = parseInt($level.val(), 10);
            return isNaN(v) ? 0 : v;
        }

        function suggestEnclosing() {
            // a top-level (level 0) speech is never embedded in anything
            if (currentLevel() <= 0) return;
            // never clobber a value the user has already picked
            if ($embeddedIn.val()) return;

            var workId = $work.val();
            var lFi = $lfi.val();
            var lLa = $lla.val();
            if (!workId || !lFi || !lLa) return;

            var params = new URLSearchParams({work: workId, l_fi: lFi, l_la: lLa, level: currentLevel()});
            if (currentId) params.set('exclude', currentId);

            fetch(adminBase() + 'guess-enclosing/?' + params.toString())
                .then(function(resp) { return resp.ok ? resp.json() : null; })
                .then(function(data) {
                    if (!data || !data.id || $embeddedIn.val()) return;
                    var opt = new Option(data.text, data.id, true, true);
                    $embeddedIn.append(opt).trigger('change');
                });
        }

        function checkLevelWarning() {
            var inconsistent = currentLevel() <= 0 && !!$embeddedIn.val();
            var $warning = $('#embedded-level-warning');

            if (inconsistent) {
                if (!$warning.length) {
                    $warning = $(
                        '<div id="embedded-level-warning" style="' +
                        'color:#a94442;background:#f2dede;border:1px solid #ebccd1;' +
                        'padding:6px 10px;margin:6px 0;border-radius:4px;">' +
                        '⚠ level is 0 (not embedded) but embedded_in is set. ' +
                        'A top-level speech shouldn’t have an enclosing speech.</div>'
                    );
                    var $row = $embeddedIn.closest('.form-row, .field-embedded_in');
                    ($row.length ? $row : $embeddedIn).after($warning);
                }
            } else {
                $warning.remove();
            }
        }

        $lfi.on('blur', suggestEnclosing);
        $lla.on('blur', suggestEnclosing);
        $work.on('change select2:select', suggestEnclosing);
        $level.on('change', function() { suggestEnclosing(); checkLevelWarning(); });
        $embeddedIn.on('change select2:select select2:unselect', checkLevelWarning);

        checkLevelWarning();
    });
})();
