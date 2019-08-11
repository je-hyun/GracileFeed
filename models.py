from flask_login import UserMixin

from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    subscriptions = db.relationship('Subscription', cascade="all,delete", backref='user') #subscriptions = db.relationship('Subscription', cascade = "all,delete", backref='user')
    favorites = db.relationship('Favorite', cascade="all,delete", backref='user')

    def __repr__(self):
        return f'User {self.username}'

class Source(db.Model):
    rss_url = db.Column(db.String(512), primary_key=True)
    homepage_url = db.Column(db.String(512))
    name = db.Column(db.String(80))
    subscriptions = db.relationship('Subscription', cascade="all,delete", backref='source')
    articles = db.relationship('ArticleSource', cascade="all,delete", backref='source')

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
    source = db.relationship('ArticleSource', cascade="all,delete", backref='article')
    favorites = db.relationship('Favorite', cascade="all,delete", backref='article')

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
