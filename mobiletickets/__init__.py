import config
from flask import Flask, Request
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(config)

import mobiletickets.views

if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler('127.0.0.1',
                               app.config['MAIL_FROM'],
                               app.config['ADMINS'], "mobile tickets error")
    mail_handler.setFormatter(logging.Formatter('''
Message type:       %(levelname)s
Time:               %(asctime)s

Message:

%(message)s
'''))
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)
