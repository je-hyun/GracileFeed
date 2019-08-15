# GracileFeed

GracileFeed is an RSS reader website which allows users to limit the amount of posts to see daily. Its goal is to allow users to portion their media consumption the way they want to, and reduce the time wasted hopping sites to get their daily internet dose from their favorite sources.

## Getting Started

The following instructions are for setting up a local development environment on your computer and running it.

### Prerequisites

[Python3](https://www.python.org/) is required to run this package.

### Installing

To get your development environment running, it is recommended to use a virtual environment like [venv](https://docs.python.org/3/library/venv.html) or [conda](https://docs.conda.io/en/latest/).

1. Clone or download GracileFeed repository and enter its root directory.
2. Create and activate your virtual environment.
3. Install requirements via ```$pip install -r requirements.txt```.
4. Add the environment variable to the location of the app ```export FLASK_APP=app.py```.
5. Run the local server ```flask run```

## Built With

* [Flask](https://flask.palletsprojects.com/en/1.0.x/) - The web framework used
* [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/) - Database Object Relational Mapper (ORM) used (currently using SQLite, but may change in the future).
* [Flask-Boostrap](https://pythonhosted.org/Flask-Bootstrap/) - Front end styling used
* [Newspaper](https://github.com/codelucas/newspaper) - Article scraping and processing tool used
* [Feedparser](https://pythonhosted.org/feedparser/) - RSS handler used
* [Bleach](https://github.com/mozilla/bleach) - Tool used for sanatizing HTML


## Authors

* **Je Hyun Kim** - *Initial work* - [Je Hyun Kim](https://github.com/je-hyun/)

See also the list of [contributors](https://github.com/je-hyun/GracileFeed/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
