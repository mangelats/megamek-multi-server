from . import app

# This is run on dev
if __name__ == "__main__":
    app.secret_key = "868051d50a154c19d7f284e74012056cbe957e045658df388c4554d85d57a8a6"
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.run()
