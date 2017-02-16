import $ from 'jquery';
import {getLocalStorageKey} from './utils';

let _escape = require("lodash/escape");
let _unescape = require("lodash/unescape");

class UberEditor {
    static init(textarea) {
        const $textarea = $(textarea);
        const $container = $("<div/>").insertAfter($textarea);
        $container.css('border', '1px solid #f2f2f2');
        const autoSaveEnabled = $textarea.data('local-persist') === true;
        let buttonFullscreen = true;
        if ($textarea.data('button-fullscreen') !== undefined) {
            buttonFullscreen = $textarea.data('button-fullscreen');
        }
        $textarea.hide();
        $textarea.removeProp("required");
        const shouldFocus = $textarea.prop("autofocus");

        const opts = {
            container: $container[0],
            textarea: $textarea[0],
            parser: null,
            focusOnLoad: shouldFocus,
            basePath: "/static/js/vendor/EpicEditor-v0.2.2",
            clientSideStorage: autoSaveEnabled,
            autogrow: {minHeight: 200},
            button: {bar: "show", fullscreen: buttonFullscreen},
            theme: {
                base: '/themes/base/epiceditor.css',
                editor: '/themes/editor/epic-light.css'
            }
        };

        if (autoSaveEnabled) {
            if (textarea.name === undefined) {
                console.error("Missing attr `name` for textarea. " +
                    "Text restore will be buggy.")
            }
            // Presume textarea name is unique for page!
            let filename = getLocalStorageKey(textarea);
            opts['file'] = {
                name: filename,
                defaultContent: "",
                autoSave: 200
            };
        }

        const editor = new EpicEditor(opts);
        editor.load();

        const previewer = editor.getElement("previewer");
        const previewerIframe = editor.getElement("previewerIframe");
        // Append MathJax Configuration
        const iframe_window = previewerIframe.contentWindow || previewerIframe;
        iframe_window.MathJax = window.MathJax;
        // Append MathJax src file
        const mathjax = previewer.createElement('script');
        mathjax.type = 'text/javascript';
        mathjax.src = window.CSC.config.JS_SRC.MATHJAX;
        previewer.body.appendChild(mathjax);

        editor.on('preview', function () {
            var contentDocument
                = editor.getElement('previewerIframe').contentDocument;
            var target = $("#epiceditor-preview", contentDocument).get(0);

            var text = _unescape(target.innerHTML);
            if (text.length > 0) {
                $.ajax({
                    method: "POST",
                    url: "/tools/markdown/preview/",
                    traditional: true,
                    data: {text: text},
                    dataType: "json"
                })
                .done(function (data) {
                    if (data.status === 'OK') {
                        target.innerHTML = data.text;
                        editor.getElement('previewerIframe').contentWindow.MathJax.Hub.Queue(function () {
                            editor.getElement('previewerIframe').contentWindow.MathJax.Hub.Typeset(target, function() {
                                $(target).find("pre").addClass("hljs");
                                if (!editor.is('fullscreen')) {
                                    let height = Math.max(
                                        $(target).height() + 20,
                                        editor.settings.autogrow.minHeight
                                    );
                                    $container.height(height);
                                }
                                editor.reflow();

                                });
                        });
                    }
                }).error(function (data) {
                    let text;
                    if (data.status === 403) {
                        // csrf token wrong?
                        text = 'Action forbidden';
                    } else {
                        text = "Unknown error. Please, save results of your work first, then try to reload page.";
                    }
                    swal({
                        title: "Error",
                        text: text,
                        type: "error"
                    });
                });

            }

        });

        // Restore label behavior
        $('label[for=id_' + textarea.name + ']').click(function() {
            editor.focus();
        });
        // Try to fix contenteditable focus problem in Chrome
        $(editor.getElement("editor")).click(function() {
            editor.focus();
        });

        // How often people use this button?
        editor.on('fullscreenenter', function () {
            if (window.yaCounter25844420 !== undefined) {
                window.yaCounter25844420.reachGoal('MARKDOWN_PREVIEW_FULLSCREEN');
            }
        });

        editor.on('edit', function () {
            if (!editor.is('fullscreen')) {
                var height = Math.max(
                    $(editor.getElement('editor').body).height() + 20,
                    editor.settings.autogrow.minHeight
                );
                $container.height(height);
            }
            editor.reflow();
        });

        // Ctrl+Enter to send form
        // Submit button value won't be attached to form data, be aware
        // if your form process logic depends on prefix, for example
        if ($textarea[0].dataset.quicksend == 'true') {
            var editorBody = editor.getElement('editor').body;
            // FIXME: use .on here
            editorBody.addEventListener('keydown', function (e) {
                if (e.keyCode === 13 && (e.metaKey || e.ctrlKey)) {
                    $textarea.closest("form").submit();
                }
            });
        }
        return editor;
    }

    // FIXME: make it callable once!
    static preload(callback = function() {}) {
        const scripts = [CSC.config.JS_SRC.MATHJAX,
                         CSC.config.JS_SRC.HIGHLIGHTJS];
        const deferred = $.Deferred();
        let chained = deferred;
        $.each(scripts, function(i, url) {
             chained = chained.then(function() {
                 return $.ajax({
                     url: url,
                     dataType: "script",
                     cache: true,
                 });
             });
        });
        chained.done(callback);
        deferred.resolve();
    }

    static render(target) {
        MathJax.Hub.Queue(["Typeset", MathJax.Hub, target, function () {
            $(target)
                .find("pre").addClass("hljs")
                .find('code').each(function (i, block) {
                // Some teachers use escape entities inside code block
                // To prevent &amp;lt; instead of "&lt;", lets double
                // unescape (&amp; first, then &lt;) and escape again
                // Note: It can be unpredictable if you want show "&amp;lt;"
                const t = block.innerHTML;
                block.innerHTML = _escape(_unescape(_unescape(t)));
                hljs.highlightBlock(block);
            });
        }]);
    }
}


export default UberEditor;