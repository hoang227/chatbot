from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from flask import Flask, render_template, redirect, request, url_for, session
from helpers import add_message, get_messages, create_user, login_required, login_user

from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea

import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'you-will-never-guess'

class Ask(FlaskForm):
    query_input = StringField(u'Query', widget=TextArea())
    submit = SubmitField(u"")

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Register')
    
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

def initialize_llama3():
    try:
        create_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "you will assist our customer support team in answering client inquiries"),
                ("user", "Question: {question}")
            ]
        )
        
        llama_model = Ollama(model = "llama3")
        format_output = StrOutputParser()
        
        chatbot_pipeline = create_prompt | llama_model | format_output
        
        return chatbot_pipeline
    except Exception as e:
        logging.error(f"Error initializing llama3: {e}")
        raise
    
chatbot_pipeline = initialize_llama3()

@app.route('/', methods=['GET', 'POST'])
@login_required
def main():
    form = Ask()
    user = session.get('username', None)
    history = get_messages(user)
    if request.method == 'POST':
        query_input = form.query_input.data
        if query_input:
            try:
                add_message(user, query_input, "user")
                return redirect(url_for('chatbot_response', query=query_input))
            except Exception as e:
                logging.error(f"Error running chatbot pipeline: {e}")
    return render_template("index.html", history=history, form=form)

@app.route('/chatbot_response')
@login_required
def chatbot_response():
    user = session.get('username', None)
    query = request.args.get('query')
    response = chatbot_pipeline.invoke({'question': query})
    add_message(user, response, "chatbot")
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        confirm = form.confirm_password.data
        
        if password != confirm:
            return render_template('register.html', form=form, error="Passwords do not match")
        
        try:
            if create_user(username, password):
                return redirect(url_for('login'))
            else:
                return render_template('register.html', form=form, error="Username already exists")
        except:
            return "An error occurred while trying to create a new user"
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if login_user(username, password):
            session['username'] = username
            return redirect('/')
        else:
            return render_template('login.html', form=form, error="Invalid username or password")
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.context_processor
def inject_user():
    if 'username' in session:
        user = session['username']
        return {'user': user}
    else:
        return {'user': None}
         
if __name__ == '__main__':
    app.run(debug=True)