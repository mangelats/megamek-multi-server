import flask
import flask_login
from flask import Flask, render_template, request, session
import auth

app = Flask(__name__)
app.secret_key = "868051d50a154c19d7f284e74012056cbe957e045658df388c4554d85d57a8a6"
app.config["USE_SESSION_FOR_NEXT"] = True
auth.login_manager.init_app(app)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    next = session.get('next')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if user := auth.login(username, password):
            if next:
                del session['next']
            return flask.redirect(next or '/')

    return render_template("login.html", error=error)

@app.route("/")
@flask_login.login_required
def index():
    return render_template("index.html", name=auth.current_user.username)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    next = session.get('next')
    auth.logout()
    if next:
        del session['next']
    return flask.redirect(next or 'login')
