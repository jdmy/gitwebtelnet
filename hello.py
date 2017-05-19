from flask import Flask, render_template, session, redirect, url_for, request, g, current_app, flash
from flask_script import Manager
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import Required
import re
import time
import telnetlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)


class NameForm(FlaskForm):
    cmd = StringField('Shell command')
    submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    telnetip = StringField('IP')
    username = StringField('Username', validators=[Required()])
    password = PasswordField('Password', validators=[Required()])
    submit = SubmitField('Submit', validators=[Required()])


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('telnetip', None)
    session.pop('username', None)
    session.pop('password', None)
    session['logged_in'] = False
    # session['session'] = False
    current_app.res = ''
    # do_cmd(current_app.tn, 'exit')
    current_app.tn.close()
    return redirect(url_for('telnet'))


@app.route('/telnet', methods=['GET', 'POST'])
def telnet():
    form = LoginForm()
    if request.method == 'POST':
        if request.form.get('ip') != None:
            # print(request.form)
            session['telnetip'] = request.form.get('ip')
            session['username'] = request.form.get('usr')
            session['password'] = request.form.get('pwd')
            current_app.tn = get_connect_telnet(session['telnetip'], username=session['username'],
                                                password=session['password'])
            if not current_app.tn.sock:
                flash('登录失败')
                session['logged_in'] = False
                # return redirect(url_for('index'))
            else:
                session['logged_in'] = True
                # return redirect(url_for('index'))
            # print(request.args)
            return redirect(url_for('index'))

        if form.validate_on_submit():
            session['telnetip'] = form.telnetip.data
            session['username'] = form.username.data
            session['password'] = form.password.data
            current_app.tn = get_connect_telnet(session['telnetip'], username=session['username'],
                                                password=session['password'])
            if not current_app.tn.sock:
                flash('登录失败')
                session['logged_in'] = False
                # return redirect(url_for('index'))
            else:
                session['logged_in'] = True
                # return redirect(url_for('index'))
            return redirect(url_for('index'))
    elif request.method=='GET':
        if request.args.get('ip') != None:
            # print(request.form)
            session['telnetip'] = request.args.get('ip')
            session['username'] = request.args.get('usr')
            session['password'] = request.args.get('pwd')
            current_app.tn = get_connect_telnet(session['telnetip'], username=session['username'],
                                                password=session['password'])
            if not current_app.tn.sock:
                flash('登录失败')
                session['logged_in'] = False
                # return redirect(url_for('index'))
            else:
                session['logged_in'] = True
                # return redirect(url_for('index'))
            # print(request.args)
            return redirect(url_for('index'))
        else:
            return render_template('telnetlogin.html', form=form)


@app.route('/', methods=['GET', 'POST'])
def index():
    # print("logged_in", session.get('logged_in'))

    if not session.get('logged_in'):
        current_app.res = ''
        return redirect(url_for('telnet'))
    form = NameForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            cmd = form.cmd.data
            form.cmd.data = ''
            tmp = do_cmd(current_app.tn, cmd)
            tmp = re.sub(r'\[\d;\d{1,2}?m|\[\d{1,2}?m', '', tmp)
            current_app.res = current_app.res + tmp
        return render_template('index.html', form=form, res=current_app.res)
    return render_template('index.html', form=form, res=current_app.res)


@app.before_first_request
def before_first_request():
    session['logged_in'] = False;
    current_app.res = ''


def get_connect_telnet(host, username, password=None):
    tn = telnetlib.Telnet(host, timeout=1)
    tn.read_until(b"login: ")
    tn.write(username.encode('ascii') + b"\n")
    if password:
        tn.read_until(b"Password: ")
        tn.write(password.encode('ascii') + b"\n")
    tmp = tn.read_until(b'incorrect', timeout=5)
    # print(tmp)
    print(type(tmp))
    if tn.read_until(b'incorrect', timeout=10):
        # print("失败")
        tn.close()
    else:
        pass
        # print("成功")
    return tn


def do_cmd(tn, cmd):
    tn.write(cmd.encode('ascii') + b"\n")
    time.sleep(1)
    return tn.read_very_eager().decode('utf-8')


if __name__ == '__main__':
    manager.run()
