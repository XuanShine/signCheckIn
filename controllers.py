"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

from py4web import URL, abort, redirect, request  # noqa: F401
from py4web.core import action as real_action
import sys

def action(*args, **kwargs):
    """To avoid executing actions during pytest collection."""
    if 'pytest' in sys.modules:
        return lambda f: f
    else:
        return real_action(*args, **kwargs)

from .models import db  # noqa: E402
from loguru import logger  # noqa: E402

def disable_all_other_clients():
    """Désactive tous les autres clients actifs"""
    db(db.clients.active).update(active=False)
    db.commit()

@action("insert", method=["POST"])
def insert():
    """Insère un nouveau client, l’active et désactive les autres clients actifs"""
    data = request.json
    
    # Désactiver tous les autres clients
    disable_all_other_clients()
    
    db.clients.insert(
        nom = data.get("nom", ""),
        email = data.get("email", ""),
        telephone = data.get("telephone", ""),
        checkin = data.get("checkin", ""),
        checkout = data.get("checkout", ""),
        cb = data.get("cb", ""),
        active = True,
        signed = False
    )
    
    db.commit()
    logger.info(f"Client {data.get('nom')} inserted and set as active")
    return "Client inserted successfully"

@action("modify/<client_id>", method=["POST"])
def modify(client_id):
    """Modifie un client existant, le désactive et désactive les autres clients actifs"""
    data = request.json

    client = db(db.clients.id == client_id).select().first()
    if not client:
        abort(404, "Client not found")
    
    # Désactiver tous les autres clients
    disable_all_other_clients()

    db(db.clients.id == client_id).update(
        nom = data.get("nom", ""),
        email = data.get("email", ""),
        telephone = data.get("telephone", ""),
        checkin = data.get("checkin", ""),
        checkout = data.get("checkout", ""),
        cb = data.get("cb", ""),
        active = False,
        signed = False
    )
    db.commit()
    logger.info(f"Client {client_id} modified and set as not active")
    return "Client modified successfully"


@action("active_client", method=["GET"])
def active_client():
    rows = db(db.clients.active == True).select(orderby=~db.clients.created_on)  # noqa: E712
    # Convert Rows to plain dicts for JSON serialization
    rows_list = [r.as_dict() for r in rows]
    return dict(data=rows_list)


@action("list", method=["GET"])
def list_clients():
    rows = db(not db.clients.signed).select(orderby=~db.clients.created_on)
    # Convert Rows to plain dicts for JSON serialization
    rows_list = [r.as_dict() for r in rows]
    return dict(data=rows_list)


"""
@action("client/<client_id>", method=["GET"])
def client(client_id: int):
    row = db.clients[client_id]
    if not row:
        abort(404, "Client not found")
    return dict(data=row.as_dict())
"""

