from quart import Quart
from quart_auth import QuartAuth

app = Quart("megameck-multi-server")
app.secret_key = "868051d50a154c19d7f284e74012056cbe957e045658df388c4554d85d57a8a6"

QuartAuth(app)


@app.route('/')
async def hello():
    return 'hello'

app.run()
