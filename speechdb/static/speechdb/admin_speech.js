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
})();
