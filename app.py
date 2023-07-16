from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pickle
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import pymysql
import bcrypt

app = Flask(__name__)


pymysql.install_as_MySQLdb()
app.config['DEBUG'] = True
app.config['ENV'] = 'development'
app.config['FLASK_ENV'] = 'development'
app.config['SECRET_KEY'] = 'ItShouldBeALongStringOfRandomCharacters'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Password0!@localhost:3306/loan_approval_system'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.app_context().push()
db = SQLAlchemy(app)
class users(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    user_name = db.Column (db.String(255))
    password = db.Column(db.String(255))
    def __init__(self,user_name,password):
        self.user_name = user_name
        self.password = password

db.create_all()

## open and load the pickle file provided in read mode.
model = pickle.load(open('loan_estimator.pkl', 'rb'))

#Mapping of column gender is {'female': 0, 'male': 1}
        #Mapping of column married is {'no': 0, 'yes': 1}
        #Mapping of column education is {'graduate': 0, 'not graduate': 1}
        #Mapping of column self_employed is {'no': 0, 'yes': 1}
        #Mapping of column property_area is {'rural': 0, 'semiurban': 1, 'urban': 2}
        #Mapping of credit_history is {"yes" : 1,"no":0}

conversion_map = {
    'gender': {'female': 0,'male': 1 },
    'married': {'no': 0, 'yes': 1},
    'education': {'graduate': 0, 'not_graduate':1},
    'self_employed': {'no': 0, 'yes': 1},
    'credit_history': {'no': 0, 'yes': 1},
    'property_area': { 'rural': 0, 'semiurban': 1, 'urban': 2,}
}

def predict_loan_eligibility (data) :

    for col, mapping in conversion_map.items():
       data[col] = data[col].map(mapping)

    prediction = model.predict(data)
    return prediction

@app.route('/')
def home():
    return render_template("home.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Perform necessary operations to store the user data in the database
        data = users(username,hashed_password)
        db.session.add(data)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    print("here")
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']

        # Perform necessary operations to verify the user credentials
        user = db.session.query(users).filter(users.user_name == username).first()
        #user_list = users.query.filter_by(user_name == username).all()
        if user is not None:
            stored_password = user.password  # Assuming the hashed password is stored in the third column of the user table

            # Compare the hashed password with the provided password
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                # Password matches, user authenticated
                session['loggedin'] = True
                session['id'] = user.id
                session['username'] = user.user_name
                return redirect(url_for('predict'))  # Redirect to the predict page
            else:
                return render_template('login.html',error_text ="The username and password dont match, please re-enter the details." )
        else :
            return redirect(url_for('register'))
    return render_template('login.html')


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        # Get form data
        gender = request.form['gender']
        married = request.form['married']
        dependents = int(request.form['dependents'])
        education = request.form['education']
        self_employed = request.form['self_employed']
        applicant_income = int(request.form['applicant_income'])
        coapplicant_income = int(request.form['coapplicant_income'])
        loan_amount = int(request.form['loan_amount'])
        loan_amount_term = int(request.form['loan_amount_term'])
        credit_history = request.form['credit_history']
        property_area = request.form['property_area']
        toal_income = applicant_income+coapplicant_income

        data = pd.DataFrame({
        'gender': [gender],
        'married': [married],
        'dependents': [dependents],
        'education': [education],
        'self_employed': [self_employed],
        'loan_amount': [loan_amount],
        'loan_amount_term': [loan_amount_term],
        'credit_history': [credit_history],
        'property_area': [property_area],
        'total_income' : [toal_income]
    })

        # Perform the prediction using your model
        prediction = predict_loan_eligibility(data)

        # Process the prediction result
        if prediction == 1:
            output = "Congrats!! You are eligible for the loan."
        else:
            output = "Sorry, you are not eligible for the loan."

        # Render the template with the prediction result and form data
        return render_template('predict.html', prediction_text=output )

    return render_template('predict.html')


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug = True,port = 5007)
