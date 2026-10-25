const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('static/js/manual_vinculos.js', 'utf8');
const response = (status = 200) => ({status, ok: status === 200, redirected: false,
    headers: {get: () => 'application/json'}, json: async () => status === 200 ?
        {ok: true, message: 'Vinculación confirmada', cuenta: {id: 1, codigoagrupador: '101.01', nombre_sat: 'Caja y efectivo'}} : {ok: false, message: 'No se pudo guardar'}});
function setup(fetcher = async () => response()) {
    const notices = [], requests = [];
    const classes = () => ({add() {}, remove() {}});
    const makeRow = id => {
        const button = {dataset: {accountId: id, codigoSat: '101.01', url: `/catalogo/confirmar/${id}/`},
            disabled: false, textContent: 'Confirmar vinculación',
            addEventListener(name, fn) {this.click = fn;}, remove() {this.removed = true;}};
        const input = {disabled: true, checked: false};
        const status = {textContent: 'Vinculación sugerida · pendiente de confirmar', classList: classes()};
        const sat = {textContent: '', hidden: true};
        const row = {dataset: {manualAccount: id, mostrarSat: 'true'}, classList: classes(),
            querySelector: selector => (selector === '[data-confirmar-sugerencia]' || selector === '[data-account-action]') ? button :
                selector === 'input[data-account-id]' ? input : selector === '[data-account-status]' ? status : selector === '[data-account-sat]' ? sat : {classList: classes()}};
        return {row, button, input, status};
    };
    const own = makeRow('1'), inverse = makeRow('1'), other = makeRow('2');
    const all = [own, inverse, other];
    const handlers = {};
    const form = {querySelectorAll: selector => selector === '[data-sat-target]' ? [] : all.map(item => selector === '[data-manual-account]' ? item.row : item.button),
        addEventListener(name, fn) {handlers[name] = fn;}, querySelector: selector => selector === '[name="csrfmiddlewaretoken"]' ? {value: 'csrf-test'} : null};
    vm.runInNewContext(source, {
        document: {getElementById: () => form},
        window: {Swal: {fire: options => {notices.push(options); return new Promise(() => {});}},
            setTimeout: () => 1, clearTimeout() {}},
        URLSearchParams, AbortController, TypeError,
        fetch: async (...args) => {requests.push(args); return fetcher(...args);}
    });
    return {own, inverse, other, notices, requests, handlers};
}
test('un clic confirma y habilita la cuenta en ambas vistas sin seleccionar ni recargar', async () => {
    const app = setup();
    await app.own.button.click();
    assert.equal(app.requests.length, 1);
    assert.equal(app.requests[0][1].body.get('codigoagrupador'), '101.01');
    assert.equal(app.requests[0][1].body.get('csrfmiddlewaretoken'), 'csrf-test');
    for (const item of [app.own, app.inverse]) {
        assert.equal(item.input.disabled, false);
        assert.equal(item.input.checked, false);
        assert.equal(item.status.textContent, 'Vinculación confirmada');
        assert.equal(item.button.removed, true);
    }
    assert.equal(app.other.input.disabled, true);
    assert.equal(app.notices[0].icon, 'success');
});
test('no duplica la petición si se pulsa desde las dos vistas mientras se guarda', async () => {
    let done;
    const app = setup(() => new Promise(resolve => {done = resolve;}));
    const first = app.own.button.click();
    assert.equal(app.inverse.button.disabled, true);
    await app.inverse.button.click();
    assert.equal(app.requests.length, 1);
    done(response());
    await first;
});
test('un error mantiene la cuenta sin confirmar y permite reintentar', async () => {
    const app = setup(async () => response(400));
    await app.own.button.click();
    assert.equal(app.own.input.disabled, true);
    assert.equal(app.inverse.input.disabled, true);
    assert.equal(app.own.button.disabled, false);
    assert.equal(app.own.button.removed, undefined);
    assert.equal(app.notices[0].icon, 'error');
});
test('una conexión fallida libera ambos botones aunque el aviso siga abierto', async () => {
    const app = setup(async () => {throw new TypeError('Network error');});
    await app.own.button.click();
    assert.equal(app.own.button.disabled, false);
    assert.equal(app.inverse.button.disabled, false);
    assert.match(app.notices[0].text, /comprobar el guardado/);
});

test('la confirmación del modal actualiza ambas copias mediante el mismo manejador', () => {
    const app = setup();
    app.handlers['manual-vinculo-confirmado']({detail: {id: 1, codigoagrupador: '101.01', nombre_sat: 'Caja y efectivo'}});
    assert.equal(app.own.input.disabled, false);
    assert.equal(app.inverse.input.disabled, false);
    assert.equal(app.other.input.disabled, true);
    assert.equal(app.requests.length, 0);
});
