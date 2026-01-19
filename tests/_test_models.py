import pytest
from pydal import DAL
import datetime as dt
from signCheckIn.models import db


@pytest.fixture(scope="module")
def test_db():
    # Create an in-memory SQLite database for testing
    test_db = DAL('sqlite:memory:')
    # Redefine the table in the test db
    test_db.define_table('clients',
        test_db.Field('nom', 'string'),
        test_db.Field('email', 'string'),
        test_db.Field('telephone', 'string'),
        test_db.Field('checkin', 'date'),
        test_db.Field('checkout', 'date'),
        test_db.Field('cb', 'string'),
        test_db.Field("signed", "boolean", default=False),
        test_db.Field("active", "boolean", default=False),
        test_db.Field('created_on', 'datetime', default=dt.datetime.now()),
    )
    test_db.commit()
    yield test_db
    test_db.close()


def test_clients_table_definition(test_db):
    """Test that the clients table is properly defined."""
    table = test_db.clients
    assert 'nom' in table.fields
    assert 'email' in table.fields
    assert 'telephone' in table.fields
    assert 'checkin' in table.fields
    assert 'checkout' in table.fields
    assert 'cb' in table.fields
    assert 'signed' in table.fields
    assert 'active' in table.fields
    assert 'created_on' in table.fields


def test_clients_table_insert_and_query(test_db):
    """Test inserting a record into clients table and querying it."""
    table = test_db.clients
    # Insert a test record
    record_id = table.insert(
        nom='John Doe',
        email='john@example.com',
        telephone='123456789',
        checkin=dt.date.today(),
        checkout=dt.date.today() + dt.timedelta(days=1),
        cb='1234-5678-9012-3456',
        signed=True,
        active=True
    )
    test_db.commit()
    
    # Query the record
    record = table[record_id]
    assert record.nom == 'John Doe'
    assert record.email == 'john@example.com'
    assert record.signed == True
    assert record.active == True
    assert isinstance(record.created_on, dt.datetime)


def test_clients_table_defaults(test_db):
    """Test default values for signed and active fields."""
    table = test_db.clients
    # Insert without specifying signed and active
    record_id = table.insert(
        nom='Jane Doe',
        email='jane@example.com',
        telephone='987654321',
        checkin=dt.date.today(),
        checkout=dt.date.today() + dt.timedelta(days=2),
        cb='4321-8765-2109-6543'
    )
    test_db.commit()
    
    record = table[record_id]
    assert record.signed == False  # default
    assert record.active == False  # default
    assert record.created_on is not None