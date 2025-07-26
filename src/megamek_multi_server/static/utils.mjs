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