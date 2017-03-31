from flask import Flask, render_template, session, redirect, url_for, request
from flask_script import Manager
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
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
    name = StringField('Shell command')
    submit = SubmitField('Submit')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/telnet', methods=['GET', 'POST'])
def telnet():
    if request.method == 'POST':
        session['telnetip'] = request.form['telnetip']
        session['username'] = request.form['username']
        session['password'] = request.form['password']
        return redirect(url_for('index'))
    return '''
            <form action="" method="post">
                <p><input type=text name=telnetip>
                <p><input type=text name=username>
                <p><input type=text name=password>
                <p><input type=submit value=Login>
            </form>
        '''

resp=''
@app.route('/', methods=['GET', 'POST'])
def index():
    global resp
    if 'telnetip' in session:
        print(session['telnetip'], session['username'], session['password'])
        tn = get_connect_telnet(session['telnetip'], usr=session['username'], pwd=session['password'])
    else:
        resp=''
    name = ''

    form = NameForm()
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        print(name)
        if name == '':
            tn.write(b"ls\n")
            time.sleep(1)
            tmp = tn.read_very_eager().decode('utf-8')
            # tmp = re.sub(r'\[(\d;)\d{1,2}?m', '', tmp)
            resp=resp+tmp
            tn.write(b'exit\n')
        else:
            tn.write(name.encode('ascii') + b"\n")
            time.sleep(1)
            tmp = tn.read_very_eager().decode('utf-8')
            print(tmp)
            # tmp = re.sub(r'\[\d;\d{1,2}?m|\[\d{1,2}?m', '', tmp)
            resp=resp+tmp
    # print(res)
    return render_template('index.html', form=form, name=name, res=resp)


def get_connect_telnet(host, usr, pwd):
    HOST = host
    user = usr
    password = pwd
    tn = telnetlib.Telnet(HOST,timeout=1)
    tn.read_until(b"login: ")
    tn.write(user.encode('ascii') + b"\n")
    if password:
        tn.read_until(b"Password: ")
        tn.write(password.encode('ascii') + b"\n")
    return tn


if __name__ == '__main__':


    manager.run()
