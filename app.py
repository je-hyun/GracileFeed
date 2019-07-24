import feedparser
from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, IntegerField, SubmitField, HiddenField
from wtforms.validators import InputRequired, Email, Length, NumberRange, URL
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from feed_processing import get_rss_articles

app = Flask(__name__)
app.config['SECRET_KEY'] = "REMINDER_make_this_an_environment_variable"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['WTF_CSRF_ENABLED'] = False # Change this when deploying
Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#Testing variables
RSS_FEEDS_LIST = {'bbc': 'http://feeds.bbci.co.uk/news/rss.xml',
                  'cnn': 'http://rss.cnn.com/rss/edition.rss',
                  'fox': 'http://feeds.foxnews.com/foxnews/latest',
                  'iol': 'http://www.iol.co.za/cmlink/1.640',
                  'smbc': 'http://www.smbc-comics.com/comic/rss',
                  'aww': 'https://www.reddit.com/r/aww.rss',
                  'askreddit': 'https://www.reddit.com/r/askreddit.rss'}

RSS_TEST = RSS_FEEDS_LIST['smbc']

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))

    def __repr__(self):
        return f'User {self.username}'

class Source(db.Model):
    rss_url = db.Column(db.String(512), primary_key=True)
    homepage_url = db.Column(db.String(512))
    name = db.Column(db.String(80))

    def __repr__(self):
        return f'Source {self.rss_url}'

class Subscription(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    rss_url = db.Column(db.String(512), db.ForeignKey("source.rss_url"), primary_key=True)
    daily_amount = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'Subscription {self.user_id} - {self.rss_url}'

class Article(db.Model):
    url = db.Column(db.String(512), primary_key=True)
    title = db.Column(db.String(256))
    image_url = db.Column(db.String(512))
    publish_date = db.Column(db.DateTime())
    text = db.Column(db.Text())

    def __repr__(self):
        return f'Article {self.url}'

class ArticleSource(db.Model):
    article_url = db.Column(db.String(512), db.ForeignKey("article.url"), primary_key=True)
    rss_url = db.Column(db.String(512), db.ForeignKey("source.rss_url"), primary_key=True)

    def __repr__(self):
        return f'ArticleSource {self.article_url} - {self.rss_url}'

class Favorite(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    article_url = db.Column(db.String(512), db.ForeignKey("article.url"), primary_key=True)

    def __repr__(self):
        return f'Favorite {self.user_id} - {self.article_url}'



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid Email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])

class SubscriptionAddForm(FlaskForm):
    rss_url = StringField('', validators=[InputRequired(), Length(max=512), URL()])
    daily_amount = IntegerField('', validators=[InputRequired(), NumberRange(min=1, max=99)])
    submit_add = SubmitField('Subscribe')

class SubscriptionDeleteForm(FlaskForm):
    submit_del = SubmitField('Delete')


@app.route('/')
def index():
    if current_user.is_authenticated:
        feed = get_rss_articles(RSS_TEST, 10)
        return render_template('feed.html', feed=feed)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('index'))
        return '<h1>Invalid username or password</h>'

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return '<h1>New User has been created!</h1>'
    return render_template('signup.html', form=form)

@app.route('/subscriptions', methods=['GET', 'POST'])
@login_required
def subscriptions():
    form_add_sub = SubscriptionAddForm()
    form_del_sub = SubscriptionDeleteForm()
    current_user_subscriptions = db.session.query(Subscription).filter(Subscription.user_id == current_user.id)
    return render_template('subscriptions.html', form_add_sub=form_add_sub, form_del_sub=form_del_sub,
                           user_subscriptions=current_user_subscriptions)

@app.route('/process_add_subscription', methods=['POST'])
def process_add_subscription():
    form_add_sub = SubscriptionAddForm()
    if form_add_sub.validate():
        # add source if it doesn't exist
        source = Source.query.filter_by(rss_url=form_add_sub.rss_url.data).first()
        if not source:
            source = Source(rss_url=form_add_sub.rss_url.data, homepage_url=form_add_sub.rss_url.data,
                            name=form_add_sub.rss_url.data)
            db.session.add(source)
        # add subscription for current user
        sub = Subscription(user_id=current_user.id, rss_url=form_add_sub.rss_url.data,
                           daily_amount=form_add_sub.daily_amount.data)
        db.session.add(sub)
        db.session.commit()
        return redirect(url_for('subscriptions'))
    flash('Error: could not subscribe. Please check your url and daily amount.')
    return redirect(url_for('subscriptions'))

@app.route('/process_del_subscription', methods=['POST'])
def process_del_subscription():
    sub_to_delete =\
        db.session.query(Subscription).filter(Subscription.user_id == current_user.id,
                                              Subscription.rss_url == request.form["submit_del"]).first()
    db.session.delete(sub_to_delete)
    db.session.commit()
    return redirect(url_for('subscriptions'))


@app.route('/test')
def test():
    form_add_sub = SubscriptionAddForm()
    return render_template('test.html', form_add_sub=form_add_sub)

@app.route('/process', methods=['POST'])
def process():
    form_add_sub = SubscriptionAddForm()
    user_id = current_user.id
    rss_url = form_add_sub.rss_url.data
    daily_amount = form_add_sub.daily_amount.data
    if form_add_sub.validate_on_submit(): #user_id and rss_url and daily_amount:
        new_sub = Subscription(user_id=user_id, rss_url=rss_url, daily_amount=daily_amount)
        db.session.add(new_sub)
        db.session.commit()
        return jsonify({'rss_url': rss_url})
    return jsonify({'error': f'Error! {form_add_sub.errors}'})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(port=5000, debug=True)
