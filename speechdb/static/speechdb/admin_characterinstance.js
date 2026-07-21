'use strict';
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        var $ = django.jQuery;
        var $char = $('#id_char');
        if (!$char.length) return;

        function adminBase() {
            var path = window.location.pathname;
            path = path.replace(/add\/$/, '');
            path = path.replace(/[^/]+\/change\/$/, '');
            return path;
        }

        $char.on('change', function() {
            var charId = $(this).val();
            if (!charId) return;

            fetch(adminBase() + 'character-defaults/' + charId + '/')
                .then(function(resp) { return resp.ok ? resp.json() : null; })
                .then(function(data) {
                    if (!data) return;
                    $('#id_being').val(data.being).trigger('change');
                    $('#id_gender').val(data.gender).trigger('change');
                    $('#id_number').val(data.number).trigger('change');
                });
        });
    });
})();
