const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('static/js/manual_modal_vinculo.js', 'utf8');
const reply = (status = 200) => ({status, ok: status === 200, redirected: false,
    headers: {get: () => 'application/json'}, json: async () => status === 200 ?
        {ok: true, message: 'Guardada', cuenta: {id: 1, codigoagrupador: '101.01', nombre_sat: 'Caja y efectivo'}} :
        {ok: false, message: 'No se pudo guardar'}});
function setup(fetcher = async () => reply()) {
    const events = [], requests = [], notices = [];
    const node = () => ({disabled: false, value: '', textContent: '', handlers: {},
        addEventListener(name, fn) {this.handlers[name] = fn;}, focus() {this.focused = true;}});
    const search = node(), select = node(), save = node(), cancel = node(), feedback = node(), cuenta = node();
    select.replaceChildren = (...options) => {select.options = options; select.value = '';};
    const button = {...node(), dataset: {accountId: '1', cuenta: '1000.01', url: '/catalogo/confirmar/1/'}};
    const dialog = {...node(), open: false, showModal() {this.open = true;}, close() {this.open = false;},
        querySelector: selector => ({'[data-modal-guardar]': save, '[data-modal-cancelar]': cancel,
            '[data-modal-feedback]': feedback, '[data-modal-cuenta]': cuenta})[selector]};
    const form = {querySelectorAll: () => [button], querySelector: () => ({value: 'csrf-test'}), dispatchEvent: event => events.push(event)};
    const ids = {'modal-vincular-sat': dialog, 'manual-generation-form': form,
        'buscar-sat-modal': search, 'codigo-sat-modal': select,
        'opciones-sat-modal': {textContent: JSON.stringify([
            {codigo: '101.01', nombre: 'Caja y efectivo'}, {codigo: '102.01', nombre: 'Bancos nacionales'}, {codigo: '103', nombre: 'Inversión'}])}};
    vm.runInNewContext(source, {
        document: {getElementById: id => ids[id]},
        window: {setTimeout: () => 1, clearTimeout() {}, Swal: {fire: async opts => notices.push(opts)}},
        Option: function(text, value) {this.text = text; this.value = value;},
        CustomEvent: function(type, options) {this.type = type; this.detail = options.detail;},
        URLSearchParams, AbortController, TypeError,
        fetch: async (...args) => {requests.push(args); return fetcher(...args);}
    });
    return {button, dialog, search, select, save, cancel, feedback, events, requests, notices};
}
test('abre un modal con búsqueda, no permite guardar vacío y cancelar no escribe', async () => {
    const app = setup();
    app.button.handlers.click();
    assert.equal(app.dialog.open, true);
    assert.equal(app.save.disabled, true);
    await app.save.handlers.click();
    assert.equal(app.requests.length, 0);
    app.search.value = 'inversion';
    app.search.handlers.input();
    assert.equal(app.select.options.length, 1);
    assert.equal(app.select.options[0].value, '103');
    app.cancel.handlers.click();
    assert.equal(app.dialog.open, false);
    assert.equal(app.events.length, 0);
});
test('guardar vincula solo esa cuenta con CSRF y notifica actualización sin recarga', async () => {
    const app = setup();
    app.button.handlers.click();
    app.select.value = '101.01';
    app.select.handlers.change();
    assert.equal(app.save.disabled, false);
    await app.save.handlers.click();
    assert.equal(app.requests[0][0], '/catalogo/confirmar/1/');
    assert.equal(app.requests[0][1].body.get('csrfmiddlewaretoken'), 'csrf-test');
    assert.equal(app.requests[0][1].body.get('codigoagrupador'), '101.01');
    assert.equal(app.events[0].type, 'manual-vinculo-confirmado');
    assert.equal(app.events[0].detail.id, 1);
    assert.equal(app.dialog.open, false);
    assert.equal(app.notices[0].icon, 'success');
});
test('errores permanecen en el modal y permiten reintentar', async () => {
    const app = setup(async () => reply(400));
    app.button.handlers.click();
    app.select.value = '101.01';
    await app.save.handlers.click();
    assert.equal(app.dialog.open, true);
    assert.match(app.feedback.textContent, /No se pudo guardar/);
    assert.equal(app.save.disabled, false);
    assert.equal(app.cancel.disabled, false);
    assert.equal(app.events.length, 0);
});
test('evita doble guardado y cerrar mientras la petición está en curso', async () => {
    let done;
    const app = setup(() => new Promise(resolve => {done = resolve;}));
    app.button.handlers.click();
    app.select.value = '101.01';
    const first = app.save.handlers.click();
    await app.save.handlers.click();
    assert.equal(app.requests.length, 1);
    let prevented = false;
    app.dialog.handlers.cancel({preventDefault() {prevented = true;}});
    assert.equal(prevented, true);
    done(reply());
    await first;
    assert.equal(app.cancel.disabled, false);
});
