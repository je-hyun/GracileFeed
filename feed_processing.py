import feedparser
import bleach
from newspaper import Article


class GracileArticle:
    def __init__(self, title=None, url=None, source_name=None, source_url=None, publish_date=None, text=None,
                 top_image=None):
        self.title = title
        self.url = url
        self.source_name = source_name
        self.source_url = source_url
        self.top_image = top_image
        self.publish_date = publish_date
        self.text = text

    def __str__(self):
        return f"title:{self.title} url:{self.url} source_name:{self.source_name} source_url:{self.source_url}" \
            f" publish_date:{self.publish_date} text:{self.text} top_image:{self.top_image}"

def get_rss_articles(rss_url, max_amount=-1):
    """
    Returns a list of GracileArticle objects from rss url. It first uses data from rss metadata, and then fills the
    remaining missing information with scraped data.

    For text and top_image, scraped data is prioritized and RSS is used as fallback.
    For the rest, RSS metadata is prioritized and scraped data is used as fallback.
    For source_name,

    :param rss_url: the url to rss feed
    :param max_amount: maximum number of articles to fetch
    :return: list of Article objects from rss link
    """
    result = []
    feed = feedparser.parse(rss_url)
    i = 0

    while i < len(feed['entries']) and (max_amount == -1 or i < max_amount):
        cur_article = GracileArticle()
        newspaper_article = None
        # url
        if 'link' in feed['entries'][i]:
            cur_article.url = feed['entries'][i]['link']
            newspaper_article = Article(feed['entries'][i]['link'])
            newspaper_article.download()
            newspaper_article.parse()

        # title
        if 'title' in feed['entries'][i]:
            cur_article.title = feed['entries'][i]['title']
        elif newspaper_article.title != '':
            cur_article.title = newspaper_article.title

        # source_url
        if 'link' in feed['feed']:
            cur_article.source_url = feed['feed']['link']
        elif newspaper_article.source_url != '':
            cur_article.source_url = newspaper_article.source_url

        # source_name
        if 'title' in feed['feed']:
            cur_article.source_name = feed['feed']['title']
        else:
            cur_article.source_name = cur_article.source_url

        # publish_date
        if 'published' in feed['entries'][i]:
            cur_article.publish_date = feed['entries'][i]['published']
        elif newspaper_article.publish_date != '':
            cur_article.publish_date = newspaper_article.publish_date

        # text
        if newspaper_article.text != '':
            cur_article.text = bleach.clean(newspaper_article.text)
        elif 'description' in feed['entries'][i]:
            cur_article.text = bleach.clean(feed['entries'][i]['description'])

        # top_image
        if newspaper_article.top_image != '':
            cur_article.top_image = newspaper_article.top_image
        elif 'image' in feed['feed']:
            cur_article.top_image = feed['feed']['image']

        result.append(cur_article)
        i += 1
    return result
