from crypt import methods
from fileinput import close
from hashlib import sha256
import json
from flask import Flask, render_template,request,redirect,session, url_for
import pickle
import numpy as np
import pandas as pd
import requests
import os
import mysql.connector
from flask_mail import *
from otp import rand_pass
from itsdangerous import URLSafeTimedSerializer
from passlib.hash import sha256_crypt


app=Flask(__name__)
with open("config.json", "r") as f:
    params=json.load(f)['params']

app.secret_key=os.urandom(24)

s=URLSafeTimedSerializer(app.secret_key)

app.config["MAIL_SERVER"]="smtp.gmail.com"
app.config["MAIL_PORT"]=465
app.config["MAIL_USERNAME"]=params['gmail-user']
app.config["MAIL_PASSWORD"]=params['gmail-password']
app.config["MAIL_USE_TLS"]=False
app.config["MAIL_USE_SSL"]=True

users=[{'name':'Aayush','email':'ayushregmi@gmail.com'},
        {'name':'Aayush_Regmi','email':'aayushregmi131@gmail.com'}]

mail=Mail(app)


movies_dict = pickle.load(open("data_files/movie_dict.pkl","rb"))
movies = pd.DataFrame(movies_dict)
similarity=pickle.load(open("data_files/similarity.pkl","rb"))
popularity_df=pickle.load(open("data_files/popularity_df.pkl","rb"))
movie_poster=pickle.load(open("data_files/movie_poster.pkl","rb"))
movies_description=pickle.load(open("data_files/movies_description.pkl","rb"))
overview = list(popularity_df['overview'])

def fetch_poster(movie_id):
    response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US'.format(movie_id))
    data = response.json()
    # st.text(data)
    # print(data['production_companies'][0]['name'])

    return "https://image.tmdb.org/t/p/w500/"+data['poster_path']


def fetch_data(movie_id):
    response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US'.format(movie_id))
    data = response.json()
    # st.text(data)
    # print(data['production_companies'][0]['name'])

    return "https://image.tmdb.org/t/p/w500/"+data['poster_path'],data["tagline"],data['production_companies'][0]['name']

def recommend(movie):
    movie_index = movies[movies['title']==movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)),reverse=True,key=lambda x : x[1])[1:6]


    recommended_movies = []
    recommended_movies_posters=[]
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movies_posters.append(fetch_poster(movie_id))
    return recommended_movies,recommended_movies_posters

movie_title = list(popularity_df['title'].values)
popularity_val = list(popularity_df['popularity'].values)


# for i in movie_title:
#     movie_index=movies[movies['title']==i].index[0]
#     # print(movie_index)
#     new_movie_id=movies.iloc[movie_index].movie_id
#     movie_poster.append(fetch_poster(new_movie_id))



@app.route("/movie_description")
def movie_description():
    if 'user_name' in session:
        args=request.args.to_dict()
        # print(args['name'])
        movies_id=movies_description[movies_description['title']==args['name']].index[0]
        distances = similarity[movies_id]
        movies_list = sorted(list(enumerate(distances)),reverse=True,key=lambda x : x[1])[1:6]

        movie_title=movies_description['title'][movies_id]
        movie_overview=" ".join(movies_description['overview'][movies_id])
        movie_genres=" ".join(movies_description['genres'][movies_id])
        movie_keywords=" ".join(movies_description['keywords'][movies_id])
        movie_casts=" ".join(movies_description['cast'][movies_id])
        movie_crew=movies_description['crew'][movies_id]
        tmdb_id=movies_description.iloc[movies_id].movie_id
        movie_poster,movie_tagline,production_company=fetch_data(tmdb_id)
        recommended_movies = []
        recommended_movies_posters=[]
        for i in movies_list:
            movie_id = movies.iloc[i[0]].movie_id
            recommended_movies.append(movies.iloc[i[0]].title)
            recommended_movies_posters.append(fetch_poster(movie_id))
        return render_template("movie_templates/movie_description.html",movie_title = movie_title,
                                                        overview=movie_overview,
                                                        genres=movie_genres,
                                                        keywords=movie_keywords,
                                                        casts=movie_casts,
                                                        crew=movie_crew,
                                                        movie_poster=movie_poster,
                                                        movie_tagline=movie_tagline,
                                                        production_company=production_company,
                                                        recommended_movies=recommended_movies,
                                                        recommended_movies_posters=recommended_movies_posters,)

@app.route('/')
def index():
    if 'user_name' in session:
        # user_info=eval(name)
        return render_template("movie_templates/index.html",movie_title = movie_title[:50],
                                                        popularity_val=popularity_val[:50],
                                                        movie_poster=movie_poster,
                                                        overview=overview,
                                                        name=session)
    else:
        return redirect('/login')


@app.route('/recommend/')
def recommend_ui():
    if 'user_name' in session:

        return render_template("movie_templates/recommend.html",movie_title = movie_title,
                                                        popularity_val=popularity_val,
                                                        movie_poster=movie_poster,
                                                        overview=overview,
                                                        name=session)
    else:
        return redirect('/login')

@app.route('/recommend_movies',methods=['post'])
def recommend_movie():
    user_input=request.form.get('user_input')
    movie_index = movies[movies['title']==user_input].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)),reverse=True,key=lambda x : x[1])[1:6]


    recommended_movies = []
    recommended_movies_posters=[]
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movies_posters.append(fetch_poster(movie_id))
    return render_template("movie_templates/recommend.html",
                                                        typed_value = user_input,
                                                        movie_title = movie_title,
                                                        popularity_val=popularity_val,
                                                        movie_poster=movie_poster,
                                                        overview=overview,
                                                        recommended_movies=recommended_movies,
                                                        recommended_movies_posters=recommended_movies_posters,
                                                        name=session

                                                        )

@app.route('/login')
def login():
    if 'user_name' not in session:
        args=request.args.to_dict()
        value=""
        if 'authentication' in args:
            value=args['authentication']
        if 'values' in args:
            value=args['values']
        return render_template("movie_templates/login.html",status=value)
    else:
        return redirect('/')

@app.route('/register')
def about():
    if 'username' not in session:
        return render_template("movie_templates/register.html",)
    else:
        return redirect('/')


@app.route('/login_validation',methods=['POST'])
def login_validation():
    email=request.form.get("email")
    password=request.form.get("password")
    if email!="" or password!="":
        conn = mysql.connector.connect(host='localhost',database='my_db',user='root',password='A@yush@8131')
        cursor = conn.cursor()

        cursor.execute("""SELECT * from `users` WHERE `email` LIKE '{}'""".format(email))
        users = cursor.fetchall()
        cursor.close()
        retrieved_password = users[0][3]
        if(sha256_crypt.verify(password,retrieved_password)):
            session['user_name']=users[0][1]
            session['user_email']= users[0][2]
            
            # print(session['user_email'])
            return redirect('/')
        else:
            return redirect('/login?authentication=no')
    else:
        return redirect('/login?values=blank')
    


@app.route("/feedback",methods=["POST"])
def feedback():
    if "user_name" in session:
        firstname=request.form.get("firstname")
        lastname=request.form.get("lastname")
        contact=request.form.get("areacode")+request.form.get("telnum")
        email=request.form.get("emailid")
        feedback=request.form.get("feedback")
        value=request.form.get('approve')
        print(firstname,lastname,contact,email,value,feedback)
        if(firstname!="" and lastname!="" and contact!="" and email!="" and feedback!=""):
            conn = mysql.connector.connect(host='localhost',database='my_db',user='root',password='A@yush@8131')
            cursor = conn.cursor()
            if(value=="ok"):
                msg=Message('Thank you for your feedback',sender='aayush.181509@ncit.edu.np',recipients=[email])
                msg.body='Welcome to MyMovies. Thank you for your feedback. Visit MyMovies to recieve exciting recommendations about movies.'
                mail.send(msg)
                
                
            else:
                pass
            cursor.execute("""INSERT INTO `feedback` (`id`,`firstname`,`lastname`,`contact`,`email`,`feedback`) VALUES
                (NULL,'{}','{}','{}','{}','{}')""".format(firstname,lastname,contact, session['user_email'],feedback))
            conn.commit()
            cursor,close()
            return redirect("/")
        else:
            print('Please leave no empty fields')
    else:
        return redirect("/")

otp=rand_pass(6)
user_info_dict={'name':"",'email':"",'password':""}

@app.route('/add_user',methods=['POST'])
def add_user():
    name=request.form.get("uname")
    email=request.form.get("uemail")
    password=request.form.get('upassword')
    user_info_dict['name']=name
    user_info_dict["email"]=email
    user_info_dict["password"]=password
    if(name != "" and email!="" and password!=""):
        conn = mysql.connector.connect(host='localhost',database='my_db',user='root',password='A@yush@8131')
        cursor = conn.cursor()

        cursor.execute("""SELECT * from `users` WHERE `email` LIKE '{}'""".format(email))
        users=cursor.fetchall()
        cursor.close()
        if len(users) > 0:
            print("This email has already been registered")
            return redirect('/register')
        else:
            token=s.dumps(email,salt='email-confirm')
            msg=Message('OTP',sender='aayush.181509@ncit.edu.np',recipients=[email])
            link=url_for("confirm",token=token,_external=True)
            msg.body='The otp is: '+otp+' Token Link is : '+link
            mail.send(msg)
            return render_template("movie_templates/enter_otp.html")
            
    else:
        return redirect("/register")

@app.route('/confirm/<token>')
def confirm(token):
    if 'user_name' in session:
        return redirect("/login")
    else:
        try:
            email=s.loads(token,salt='email-confirm',max_age=60)
        except Exception as e:
            return "Invalid Token"

        name=user_info_dict['name']
        email=user_info_dict['email']
        password=user_info_dict['password']
        encpassword=sha256_crypt.encrypt(password)
        conn = mysql.connector.connect(host='localhost',database='my_db',user='root',password='A@yush@8131')
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO `users` (`user_id`,`name`,`email`,`password`) VALUES
            (NULL,'{}','{}','{}')""".format(name,email,encpassword))
        conn.commit()
        cursor.close()

        session['user_name']=name
        session['user_email']=email
        return redirect('/login')


@app.route("/otp_validation",methods=["POST"])
def otp_validation():
    if 'user_name' in session:
        return redirect("/login")
    else:
        form_otp=request.form.get("otp")
        name=user_info_dict['name']
        email=user_info_dict['email']
        password=user_info_dict['password']
        if form_otp==otp:
            conn = mysql.connector.connect(host='localhost',database='my_db',user='root',password='A@yush@8131')
            cursor = conn.cursor()
            encpassword=sha256_crypt.encrypt(password)
            cursor.execute("""INSERT INTO `users` (`user_id`,`name`,`email`,`password`) VALUES
                (NULL,'{}','{}','{}')""".format(name,email,encpassword))
            conn.commit()
            cursor.close()

            session['user_name']=name
            session['user_email']=email
            return redirect('/login')
        else :
            return redirect("/register")
@app.route("/logout")
def logout():
    session.pop("user_name")
    session.pop("user_email")

    return redirect("/login")

@app.route("/contact")
def contact():
    if 'user_name' in session:
        return render_template("movie_templates/contact.html",name=session)
    else:
        return redirect("/")


@app.route("/test")
def test():
    return render_template("movie_templates/test.html")


if __name__=="__main__":
    app.run(debug=True) 