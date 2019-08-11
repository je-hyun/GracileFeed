from app import app, db
from forms import LoginForm, RegisterForm, SubscriptionAddForm, SubscriptionDeleteForm
from models import User, Source, Subscription, Article, ArticleSource, Favorite

from flask import render_template, redirect, url_for, request, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from feed_processing import GracileArticle, get_rss_articles, get_source_from_rss

#Testing variables
RSS_FEEDS_LIST = {'bbc': 'http://feeds.bbci.co.uk/news/rss.xml',
                  'cnn': 'http://rss.cnn.com/rss/edition.rss',
                  'fox': 'http://feeds.foxnews.com/foxnews/latest',
                  'iol': 'http://www.iol.co.za/cmlink/1.640',
                  'smbc': 'http://www.smbc-comics.com/comic/rss',
                  'aww': 'https://www.reddit.com/r/aww.rss',
                  'askreddit': 'https://www.reddit.com/r/askreddit.rss'}

RSS_TEST = RSS_FEEDS_LIST['smbc']

def cache_subscription(subscription: Subscription):
    '''
    Takes a Subscription and downloads its articles into the database (in tables ArticleSource and Article)
    :param subscription: Subscription object which contains user_id, rss_url and daily_amount.
    :return:
    '''
    li_gracile_articles = get_rss_articles(rss_url=subscription.rss_url, max_amount=subscription.daily_amount)
    for ga in li_gracile_articles:
        my_article = Article.query.filter_by(url=ga.url).first()
        if not my_article:
            my_article = Article(url=ga.url, title=ga.title, image_url=ga.top_image, publish_date=ga.publish_date,
                                  text=ga.text)
            db.session.add(my_article)
            new_articlesource = ArticleSource(article=my_article, source=Source.query.filter_by(
                rss_url=subscription.rss_url).first())
            db.session.add(new_articlesource)
    db.session.commit()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
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
            source = get_source_from_rss(form_add_sub.rss_url.data)
            db.session.add(source)
            db.session.commit()

        # Find the user and source for subscription
        sub_user = User.query.filter_by(id=current_user.id).first()
        if not sub_user:
            raise Exception('Current user not found in database. The account may have been deleted.')

        # add subscription for current user
        sub = Subscription(user=sub_user, source=source,
                           daily_amount=form_add_sub.daily_amount.data)
        db.session.add(sub)
        db.session.commit()
        cache_subscription(sub)
        return redirect(url_for('subscriptions'))

    flash('Error: could not subscribe. Please check your url and daily amount.')
    return redirect(url_for('subscriptions'))

@app.route('/process_del_subscription', methods=['POST'])
def process_del_subscription():
    sub_url_to_delete = request.form["submit_del"]
    sub_to_delete =\
        db.session.query(Subscription).filter(Subscription.user_id == current_user.id,
                                              Subscription.rss_url == sub_url_to_delete).first()
    db.session.delete(sub_to_delete)
    db.session.commit()
    return redirect(url_for('subscriptions'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ============================================================
# ======================== TEST VIEWS ========================
# ============================================================

@app.route('/feed')
@login_required
def feed():
    # Find all articles associated with ArticleSource associated with Source associated with Subscriptions to
    # current_user
    gracile_articles = []
    user_subscriptions = Subscription.query.filter_by(user_id=current_user.id)
    for sub in user_subscriptions:
        user_article_sources = ArticleSource.query.filter_by(rss_url=sub.source.rss_url).\
            join(ArticleSource.article).order_by(Article.publish_date.desc()).limit(sub.daily_amount)
        for art_src in user_article_sources:
            gracile_articles.append(GracileArticle.from_model(article=art_src.article, source=sub.source))

    return render_template('feed.html', feed=gracile_articles, user_subscriptions=user_subscriptions)

@app.route('/testAjax')
def testAjax():
    form_add_sub = SubscriptionAddForm()
    return render_template('testAjax.html', form_add_sub=form_add_sub)

@app.route('/process', methods=['POST'])
def process():
    form_add_sub = SubscriptionAddForm()
    user_id = current_user.id
    rss_url = form_add_sub.rss_url.data
    daily_amount = form_add_sub.daily_amount.data
    if form_add_sub.validate_on_submit():
        new_sub = Subscription(user_id=user_id, rss_url=rss_url, daily_amount=daily_amount)
        db.session.add(new_sub)
        db.session.commit()
        return jsonify({'rss_url': rss_url})
    return jsonify({'error': f'Error! {form_add_sub.errors}'})

