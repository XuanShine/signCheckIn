"""
This file defines the database models
"""

from pydal.validators import *
import datetime as dt

from .common import Field, db

### Define your table below
# db.define_table('thing', Field('name'))

db.define_table('clients',
    Field('nom', 'string'),
    Field('email', 'string'),
    Field('telephone', 'string'),
    Field('checkin', 'date'),
    Field('checkout', 'date'),
    Field('cb', 'string'),
    Field("signed", "boolean", default=False),
    Field("active", "boolean", default=False),
    Field('created_on', 'datetime', default=dt.datetime.now()),
)

# always commit your models to avoid problems later
db.commit()

