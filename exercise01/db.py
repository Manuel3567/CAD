import psycopg2
import click
from flask import current_app, g
from psycopg2.extras import RealDictCursor

def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(
            current_app.config['DATABASE'],
            cursor_factory=RealDictCursor
        )

    return g.db

def execute(sql, params=None):
    db = get_db()
    
    # Use RealDictCursor to get dictionary-like row results
    with db.cursor(cursor_factory=RealDictCursor) as cursor:

        cursor.execute(sql, params)  # Using params helps prevent SQL injection
        db.commit()


        # Try fetching data, if not a SELECT statement, it'll just return None
        try:
            data = cursor.fetchall()
            return data
        except psycopg2.ProgrammingError:
            return None

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('createschema.sql') as f:
        sql = f.read()
        with db.cursor() as cursor:
            cursor.execute(sql)
        db.commit()

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(del_db_command)


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Created the tables.')

def del_db():
    db = get_db()

    with current_app.open_resource('dropschema.sql') as f:
        sql = f.read()
        with db.cursor() as cursor:
            cursor.execute(sql)
        db.commit()

@click.command('del-db')
def del_db_command():
    del_db()
    click.echo('Deleted tables.')
