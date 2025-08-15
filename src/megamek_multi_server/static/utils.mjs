export function noop() {}


export function afterLoad(f) {
    if (document.readyState !== 'loading') {
        f()
    } else {
        const handler = () => {
            document.removeEventListener('DOMContentLoaded', handler)
            f()
        }
        document.addEventListener('DOMContentLoaded', handler)
    }
}

export function stateEl(state) {
    const el = document.createElement('span')
    el.classList.add('state')
    updateStateEl(el, state)
    return el
}
export function updateStateEl(el, state) {
    el.textContent = stateEmoji(state)
    el.setAttribute('data-tooltip', stateTooltip(state))
}

function stateEmoji(state) {
    const EMOJIS = {
        fresh: "📡",
        setting_up: "⏳",
        spawning: "⏳",
        running: "👍",
        stopping: "⏳",
        cleaning_up: "⏳",
        dead: "💀",
        zombie: "🧟",
    }
    if (state in EMOJIS) {
        return EMOJIS[state]
    } else {
        console.warn("Unknown state value (emoji)", state)
        return "???"
    }
}
function stateTooltip(state) {
    const TOOLTIPS = {
        fresh: "Reservat",
        setting_up: "Preparant",
        spawning: "Aixecant",
        running: "Funcionant",
        stopping: "Parant",
        cleaning_up: "Natejant",
        dead: "Parat",
        zombie: "Zombie",
    }
    if (state in TOOLTIPS) {
        return TOOLTIPS[state]
    } else {
        console.warn("Unknown state value (tooltip)", state)
        return "???"
    }
}
