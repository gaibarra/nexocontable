const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('static/js/confirmar_relacion.js', 'utf8');
const reply = (status = 200, body = {ok: true, message: 'Cuenta vinculada', cuenta: {id: 1, codigoagrupador: '102.01', nombre_sat: 'Bancos nacionales'}}) => ({
    status, ok: status < 400, redirected: false, headers: {get: () => 'application/json'}, json: async () => body
});
function setup(fetcher = async () => reply(), swalFire = null) {
    const notifications = [], requests = [];
    const makeForm = () => {
        const code = {textContent: '101 - Caja'};
        const status = {textContent: 'Sugerida'};
        const button = {disabled: false, textContent: 'Confirmar relación'};
        const select = {disabled: false, value: '102.01', listeners: {}, addEventListener(name, handler) {this.listeners[name] = handler;}, focus() {this.focused = true;}};
        const hint = {textContent: ''};
        const cell = {querySelector: key => key === '[data-relacion-codigo]' ? code : status};
        const form = {
            action: '/catalogo/confirmar/1/', attributes: {}, dataset: {confirmedCode: ''},
            querySelector: key => key.startsWith('input') ? select : key === '[data-relacion-ayuda]' ? hint : button,
            closest: () => cell,
            setAttribute(key, value) {this.attributes[key] = value;},
            removeAttribute(key) {delete this.attributes[key];},
            addEventListener(name, handler) {this.submit = handler;}
        };
        return {form, code, status, button, select, hint};
    };
    const row = makeForm(), other = makeForm();
    vm.runInNewContext(source, {
        window: {Swal: {fire: swalFire || (async options => {notifications.push(options);})}, setTimeout: () => 1, clearTimeout() {}},
        document: {querySelectorAll: selector => selector === '#codigos-sat option' ? [{value: '101'}, {value: '102.01'}] : [row.form, other.form]},
        FormData: class {constructor(form) {this.form = form;}},
        AbortController, TypeError,
        fetch: async (...args) => {requests.push(args); return fetcher(...args);}
    });
    let prevented = 0;
    return {row, other, notifications, requests, run: () => row.form.submit({preventDefault() {prevented++;}}), prevented: () => prevented};
}
test('actualiza solo la fila confirmada y avisa con SweetAlert2 sin navegar', async () => {
    const app = setup();
    await app.run();
    assert.equal(app.prevented(), 1);
    assert.equal(app.requests.length, 1);
    assert.equal(app.requests[0][1].method, 'POST');
    assert.equal(app.requests[0][1].headers['X-Requested-With'], 'XMLHttpRequest');
    assert.equal(app.row.code.textContent, '102.01 - Bancos nacionales');
    assert.equal(app.row.status.textContent, 'Vinculación confirmada');
    assert.equal(app.other.code.textContent, '101 - Caja');
    assert.equal(app.other.status.textContent, 'Sugerida');
    assert.equal(app.notifications[0].icon, 'success');
    assert.equal(app.notifications[0].html, undefined);
    assert.equal(app.row.button.disabled, true);
});
test('evita envíos duplicados mientras se guarda', async () => {
    let resolve;
    const app = setup(() => new Promise(done => {resolve = done;}));
    const first = app.run();
    assert.equal(app.row.button.disabled, true);
    assert.equal(app.row.status.textContent, 'Guardando vinculación...');
    await app.run();
    assert.equal(app.requests.length, 1);
    resolve(reply());
    await first;
    assert.equal(app.row.button.disabled, true);
});
test('código vacío muestra advertencia y no envía', async () => {
    const app = setup();
    app.row.select.value = '';
    await app.run();
    assert.equal(app.requests.length, 0);
    assert.equal(app.notifications[0].icon, 'warning');
    assert.equal(app.row.select.focused, true);
});
test('un error conserva el estado y permite volver a confirmar', async () => {
    const app = setup(async () => reply(400, {ok: false, message: 'Código inválido'}));
    await app.run();
    assert.equal(app.row.code.textContent, '101 - Caja');
    assert.equal(app.row.status.textContent, 'Sugerida');
    assert.equal(app.row.button.disabled, false);
    assert.equal(app.row.select.disabled, false);
    assert.equal(app.notifications[0].text, 'Código inválido');
});
test('sesión expirada da un aviso y no actualiza la fila', async () => {
    const app = setup(async () => ({...reply(), redirected: true}));
    await app.run();
    assert.match(app.notifications[0].text, /sesión/);
    assert.equal(app.row.code.textContent, '101 - Caja');
});
test('fallo de red informa que el guardado no pudo comprobarse', async () => {
    const app = setup(async () => {throw new TypeError('Network error');});
    await app.run();
    assert.match(app.notifications[0].text, /podría haberse guardado/);
    assert.equal(app.row.button.disabled, false);
});

test('sin código el botón permanece deshabilitado hasta elegir uno válido', () => {
    const app = setup();
    app.row.select.value = '';
    app.row.select.listeners.input();
    assert.equal(app.row.button.disabled, true);
    assert.match(app.row.hint.textContent, /Primero selecciona/);
    app.row.select.value = 'desconocido';
    app.row.select.listeners.input();
    assert.equal(app.row.button.disabled, true);
    app.row.select.value = '101';
    app.row.select.listeners.change();
    assert.equal(app.row.button.disabled, false);
});
test('no vuelve a guardar la misma relación confirmada', async () => {
    const app = setup();
    await app.run();
    await app.run();
    assert.equal(app.requests.length, 1);
    assert.equal(app.row.button.textContent, 'Relación confirmada');
    app.row.select.value = '101';
    app.row.select.listeners.input();
    assert.equal(app.row.button.disabled, false);
});
test('un SweetAlert pendiente no deja los controles ocupados', async () => {
    const app = setup(async () => reply(400, {ok: false, message: 'Error'}), () => new Promise(() => {}));
    await app.run();
    assert.equal(app.row.button.disabled, false);
    assert.equal(app.row.select.disabled, false);
    assert.equal(app.row.form.attributes['aria-busy'], undefined);
});
test('si SweetAlert falla el formulario vuelve a quedar disponible', async () => {
    const app = setup(async () => reply(400, {ok: false, message: 'Error'}), () => {throw new Error('UI failed');});
    await app.run();
    assert.equal(app.row.button.disabled, false);
    assert.equal(app.row.select.disabled, false);
});
