import sys, os
from ConfigParser import SafeConfigParser

from modbot_site import app
from flaskext.sqlalchemy import SQLAlchemy


cfg_file = SafeConfigParser()
path_to_cfg = os.path.abspath(os.path.dirname(sys.argv[0]))
cfg_file.read(os.path.join(path_to_cfg, 'modbot.cfg'))

app.config['SQLALCHEMY_DATABASE_URI'] = \
    cfg_file.get('database', 'system')+'://'+\
    cfg_file.get('database', 'username')+':'+\
    cfg_file.get('database', 'password')+'@'+\
    cfg_file.get('database', 'host')+'/'+\
    cfg_file.get('database', 'database')
db = SQLAlchemy(app)


class Subreddit(db.Model):

    """Table containing the subreddits for the bot to monitor.

    name - The subreddit's name. "gaming", not "/r/gaming".
    enabled - Subreddit will not be checked if False
    last_submission - The newest unfiltered submission the bot has seen
    last_spam - The newest filtered submission the bot has seen
    report_threshold - Any items with at least this many reports will trigger
        a mod-mail alert

    """

    __tablename__ = 'subreddits'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    last_submission = db.Column(db.DateTime)
    last_spam = db.Column(db.DateTime)
    report_threshold = db.Column(db.Integer)


class Condition(db.Model):

    """Table containing the conditions for each subreddit.

    subject - The type of item to check
    attribute - Which attribute of the item to check
    value - A regex checked against the attribute. Automatically surrounded
        by ^ and $ when checked, so looks for "whole string" matches. To
        do a "contains" check, put .* on each end
    is_gold - If True, item's author must have reddit gold
    min_account_age - Minimum account age (in days) for the item's author
    min_link_karma - Minimum link karma for the item's author
    min_comment_karma - Minimum comment karma for the item's author
    min_combined_karma - Minimum combined karma for the item's author
    inverse - If True, result of check will be reversed. Useful for
        "anything except" or "does not include"-type checks
    parent_id - The id of the condition this is a sub-condition of. If this
        is a top-level condition, will be null
    action - Which action to perform if this condition is matched

    """

    __tablename__ = 'conditions'

    id = db.Column(db.Integer, primary_key=True)
    subreddit_id = db.Column(db.Integer, db.ForeignKey('subreddits.id'))
    subject = db.Column(db.Enum('submission',
                                'comment',
                                name='condition_subject'),
                        nullable=False)
    attribute = db.Column(db.Enum('user',
                                  'title',
                                  'domain',
                                  'url',
                                  'body',
                                  'meme_name',
                                  name='condition_attribute'),
                          nullable=False)
    value = db.Column(db.Text, nullable=False)
    is_gold = db.Column(db.Boolean, nullable=False, default=False)
    min_account_age = db.Column(db.Integer, nullable=False, default=0)
    min_link_karma = db.Column(db.Integer, nullable=False, default=0)
    min_comment_karma = db.Column(db.Integer, nullable=False, default=0)
    min_combined_karma = db.Column(db.Integer, nullable=False, default=0)
    inverse = db.Column(db.Boolean, nullable=False, default=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('conditions.id'))
    action = db.Column(db.Enum('approve',
                               'remove',
                               'alert',
                               name='action'))

    subreddit = db.relationship('Subreddit',
        backref=db.backref('conditions', lazy='dynamic'))

    additional_conditions = db.relationship('Condition',
        lazy='joined', join_depth=1)


class ActionLog(db.Model):
    """Table containing a log of the bot's actions."""
    __tablename__ = 'action_log'

    id = db.Column(db.Integer, primary_key=True)
    subreddit_id = db.Column(db.Integer,
                             db.ForeignKey('subreddits.id'),
                             nullable=False)
    title = db.Column(db.Text)
    user = db.Column(db.String(255))
    url = db.Column(db.String(255))
    domain = db.Column(db.String(255))
    permalink = db.Column(db.String(255))
    created_utc = db.Column(db.DateTime)
    action_time = db.Column(db.DateTime)
    action = db.Column(db.Enum('approve',
                               'remove',
                               'alert',
                               name='action'))
    matched_condition = db.Column(db.Integer, db.ForeignKey('conditions.id'))

    subreddit = db.relationship('Subreddit',
        backref=db.backref('actions', lazy='dynamic'))

    condition = db.relationship('Condition',
        backref=db.backref('actions', lazy='dynamic'))

