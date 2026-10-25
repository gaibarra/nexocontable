const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('static/js/notifications.js', 'utf8');
const tick = () => new Promise(resolve => setImmediate(resolve));
function setup(notifications = [], confirmed = true, available = true) {
    const calls = [];
    const fallback = {hidden: false};
    let submit;
    const window = {confirm: () => confirmed};
    if (available) window.Swal = {fire: async options => { calls.push(options); return {isConfirmed: confirmed}; }};
    const document = {
        getElementById: id => id === 'app-notifications' ? {textContent: JSON.stringify(notifications)} : fallback,
        addEventListener: (name, handler) => { submit = handler; }
    };
    vm.runInNewContext(source, {window, document});
    let submissions = 0;
    const button = {};
    const form = {
        matches: () => true, dataset: {confirm: '¿Eliminar <script>?'},
        requestSubmit: value => {
            assert.equal(value, button);
            const event = {target: form, submitter: button, prevented: false, preventDefault() {this.prevented = true;}};
            submit(event);
            if (!event.prevented) submissions++;
        }
    };
    return {calls, fallback, run: () => submit({target: form, submitter: button, preventDefault() {}}), count: () => submissions};
}
test('presenta todos los mensajes en orden como texto', async () => {
    const app = setup([{icon: 'success', text: 'Guardado'}, {icon: 'error', text: '<script>peligro</script>'}]);
    await tick();
    assert.deepEqual(app.calls.map(x => x.text), ['Guardado', '<script>peligro</script>']);
    assert.ok(app.calls.every(x => x.html === undefined));
    assert.equal(app.fallback.hidden, true);
});
test('cancelar no envía el formulario', async () => {
    const app = setup([], false);
    await app.run();
    assert.equal(app.count(), 0);
});
test('confirmar envía una sola vez incluso ante doble clic', async () => {
    const app = setup();
    await Promise.all([app.run(), app.run()]);
    assert.equal(app.count(), 1);
    assert.equal(app.calls.length, 1);
});
test('sin SweetAlert2 conserva mensajes y confirmación segura', async () => {
    const app = setup([{icon: 'error', text: 'Error'}], false, false);
    await app.run();
    assert.equal(app.fallback.hidden, false);
    assert.equal(app.count(), 0);
});
