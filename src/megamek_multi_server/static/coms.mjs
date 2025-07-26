import { noop } from './utils.mjs'

export class ServerComs {
    constructor() {
        this.ws = new WebSocket(`ws://${location.host}/ws`)
        this.listeners = []
        this.ws.addEventListener('message', e => {
            const event = JSON.parse(e.data)
            for (const l of this.listeners) {
                l(event)
            }
        });
    }

    addEventListener(listener) {
        if (typeof listener === 'function') {
            this.listeners.push(listener)
        } else {
            const serversSet = asListener(listener, 'serversSet');
            const serverAdded = asListener(listener, 'serverAdded');
            const serverStateChanged = asListener(listener, 'serverStateChanged');
            const serverRemoved = asListener(listener, 'serverRemoved');
            this.addEventListener((event) => {
                if (event.event_type === 'servers_set') {
                    serversSet(event.servers)
                } else if (event.event_type === 'server_added') {
                    serverAdded(event.info)
                } else if (event.event_type === 'server_state_changed') {
                    serverStateChanged(event.id, event.new_state)
                } else if (event.event_type === 'server_removed') {
                    serverRemoved(event.id)
                } else {
                    console.warn("Unknown event", event)
                }
            })
        }
    }

    create(server, id = null) {
        console.debug("Creating server", server)
        const message = {
            cmd_type: 'create_server',
            server,
            id,
        }
        const event = JSON.stringify(message)
        this.ws.send(event)
    }

    destroy(id) {
        console.debug("Destroying server", id)
        const message = {
            cmd_type: 'destroy_server',
            id,
        }
        const event = JSON.stringify(message)
        this.ws.send(event)
    }
}


function asListener(obj, name) {
    const f = obj[name]
    if (typeof f === 'function') {
        return f.bind(obj)
    } else {
        return noop
    }
}
