from . import app

# This is run on dev
if __name__ == "__main__":
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.run()
