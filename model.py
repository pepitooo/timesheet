import os

import sqlobject
from sqlobject import SQLObject, StringCol, FloatCol, BoolCol, connectionForURI

db_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bluetooth-scan.db')
db_scheme = 'sqlite:' + db_filename
sqlobject.sqlhub.processConnection = connectionForURI(db_scheme)


class Device(SQLObject):
    mac_address = StringCol(length=17)


class Scan(SQLObject):
    timestamp = FloatCol(notNone=False)
    device = sqlobject.ForeignKey('Device')
    present = BoolCol(default=False)


try:
    Device.createTable(ifNotExists=True)
    Scan.createTable(ifNotExists=True)
except sqlobject.dberrors.OperationalError:
    pass  # table already exist
