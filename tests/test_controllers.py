import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from pydal import DAL, Field
from py4web import request, HTTP
from ombott.response import HTTPError

# Import the functions from controllers.py
from signCheckIn.controllers import insert, modify, list, client, active_client, disable_all_other_clients
from signCheckIn.models import db

@pytest.fixture(scope="function")
def test_db():
    # Use an in-memory SQLite database for testing
    test_db = DAL('sqlite:memory:')
    test_db.define_table('clients',
        Field('nom', 'string'),
        Field('email', 'string'),
        Field('telephone', 'string'),
        Field('checkin', 'date'),
        Field('checkout', 'date'),
        Field('cb', 'string'),
        Field("signed", "boolean", default=False),
        Field("active", "boolean", default=False),
        Field('created_on', 'datetime', default=datetime.now),
    )
    test_db.commit()
    # Temporarily replace the global db
    import signCheckIn.controllers as controllers
    original_db = controllers.db
    controllers.db = test_db
    yield test_db
    controllers.db = original_db
    test_db.close()
    

@pytest.fixture(scope="function")
def test_db_with_data(test_db):
    # Add some initial data to the test database
    test_db.clients.insert(
        nom='CLient1 Active',
        email='fake1@example.com',
        telephone='111111111',
        checkin='2023-01-01',
        checkout='2023-01-02',
        cb='1234',
        signed=False,
        active=True
    )
    test_db.clients.insert(
        nom='Client2 Inactive',
        email='fake2@example.com',
        telephone='123456789',
        checkin='2023-01-01',
        checkout='2023-01-02',
        cb='1234',
        signed=False,
        active=False
    )
    test_db.commit()
    
    # Verify active client
    active_clients = test_db(test_db.clients.active == True).select()
    assert len(active_clients) == 1  # There should be always only one active client
    assert active_clients[0].email == 'fake1@example.com'
    
    yield test_db

    
@patch('signCheckIn.controllers.request')
def test_insert(mock_req, test_db_with_data):
    # Mocking request for POST method
    mock_req.method = "POST"
    mock_req.json = {
        'nom': 'New Insert Client',
        'email': 'new@example.com',
        'telephone': '1122334455',
        'checkin': '2023-10-01',
        'checkout': '2023-10-05',
        'cb': '4321'
    }

    # Call the insert function
    response = insert()

    # Assertions
    assert response == "Client inserted successfully"

    # Verify new client exists and is active
    new_client = test_db_with_data(test_db_with_data.clients.nom == 'New Insert Client').select().first()
    assert new_client is not None
    assert new_client.email == 'new@example.com'
    assert new_client.active is True
    assert new_client.signed is False

    # Verify active client
    active_clients = test_db_with_data(test_db_with_data.clients.active == True).select()
    assert len(active_clients) == 1  # There should be always only one active client
    assert active_clients[0].email == 'new@example.com'
    
    # Verify all other clients are inactive
    other_clients = test_db_with_data(test_db_with_data.clients.nom != 'New Insert Client').select()
    for each_client in other_clients:
        assert each_client.active is False  # All other clients should be inactive


@patch('signCheckIn.controllers.request')
def test_modify(mock_req, test_db_with_data):
    # Find a client to modify (e.g., Client2 Inactive)
    target_client = test_db_with_data(test_db_with_data.clients.nom == 'Client2 Inactive').select().first()
    client_id = target_client.id
    
    mock_req.method = "POST"
    mock_req.json = {
        'nom': 'Client2 Modified',
        'email': 'modified@example.com',
        'telephone': '999999999',
        'checkin': '2023-05-01',
        'checkout': '2023-05-05',
        'cb': '9999'
    }

    # Call the modify function
    # Note: modify deactivates all clients, including the modified one (active=False)
    response = modify(client_id)

    assert response == "Client modified successfully"

    # Verify fields updated
    updated_client = test_db_with_data.clients[client_id]
    assert updated_client.nom == 'Client2 Modified'
    assert updated_client.email == 'modified@example.com'
    assert updated_client.active is False
    
    # Verify the OTHER previously active client is now inactive
    previous_active = test_db_with_data(test_db_with_data.clients.nom == 'CLient1 Active').select().first()
    assert previous_active.active is False
    
    # Verify NO active clients exist now
    count_active = test_db_with_data(test_db_with_data.clients.active == True).count()
    assert count_active == 0


@patch('signCheckIn.controllers.request')
def test_modify_client_not_found(mock_req, test_db_with_data):
    old_active = test_db_with_data(test_db_with_data.clients.active == True).select().first()
    
    # Try to modify a non-existent client
    non_existent_id = 999
    
    mock_req.method = "POST"
    mock_req.json = {
        'nom': 'Ghost Client',
    }

    # Call the modify function - should raise HTTP 404
    with pytest.raises(HTTPError):
        modify(non_existent_id)
    
    # Verify that active clients are NOT deactivated (since check happens before disable_all_other_clients)
    active_count = test_db_with_data(test_db_with_data.clients.active == True).count()
    actual_active = test_db_with_data(test_db_with_data.clients.active == True).select().first()
    assert active_count == 1  # Still active
    assert old_active.id == actual_active.id


"""
@pytest.fixture
def mock_request():
    return MagicMock()

def test_disable_all_other_clients(test_db):
    # Insert some test clients
    test_db.clients.insert(nom='Client1', active=True)
    test_db.clients.insert(nom='Client2', active=True)
    test_db.commit()

    # Call the function
    disable_all_other_clients()

    # Check that all are inactive
    rows = test_db(test_db.clients.active == True).select()
    assert len(rows) == 0

@patch('controllers.request')
def test_insert(mock_req, test_db):
    mock_req.method = "POST"
    mock_req.json = {
        'nom': 'Test Client',
        'email': 'test@example.com',
        'telephone': '123456789',
        'checkin': '2023-01-01',
        'checkout': '2023-01-02',
        'cb': '1234'
    }

    # Insert an existing active client
    test_db.clients.insert(nom='Existing', active=True)
    test_db.commit()

    response = insert()

    assert response == "Client inserted successfully"

    # Check db
    row = test_db(test_db.clients.nom == 'Test Client').select().first()
    assert row is not None
    assert row.active == True
    assert row.signed == False

    # Check that existing is disabled
    existing = test_db(test_db.clients.nom == 'Existing').select().first()
    assert existing.active == False

@patch('controllers.request')
def test_modify(mock_req, test_db):
    # Insert a client
    client_id = test_db.clients.insert(nom='Old Name', active=True)
    test_db.commit()

    mock_req.method = "POST"
    mock_req.json = {
        'nom': 'New Name',
        'email': 'new@example.com',
        'telephone': '987654321',
        'checkin': '2023-01-03',
        'checkout': '2023-01-04',
        'cb': '5678'
    }

    response = modify(client_id)

    assert response == "Client modified successfully"

    # Check db
    row = test_db.clients[client_id]
    assert row.nom == 'New Name'
    assert row.active == False  # Modified sets active to False
    assert row.signed == False

def test_list(test_db):
    # Insert some clients
    test_db.clients.insert(nom='Client1', signed=False)
    test_db.clients.insert(nom='Client2', signed=True)
    test_db.commit()

    response = list()

    assert 'data' in response
    assert len(response['data']) == 1  # Only unsigned
    assert response['data'][0]['nom'] == 'Client1'

def test_client(test_db):
    client_id = test_db.clients.insert(nom='Test Client')
    test_db.commit()

    response = client(client_id)

    assert 'data' in response
    assert response['data']['nom'] == 'Test Client'

def test_client_not_found(test_db):
    with pytest.raises(HTTP):
        client(999)

def test_active_client(test_db):
    test_db.clients.insert(nom='Active Client', active=True)
    test_db.clients.insert(nom='Inactive Client', active=False)
    test_db.commit()

    response = active_client()

    assert 'data' in response
    assert len(response['data']) == 1
    assert response['data'][0]['nom'] == 'Active Client'

"""