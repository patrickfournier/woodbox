=======
Woodbox
=======

Woodbox is a boilerplate project that you can use to quicky build a
web service delivering JSONAPI data from a SQL database over a REST
API. It is based on Flask and uses SQLAlchemy to abstract the database
away. It was written with emberjs in mind.

It is quite basic for now and should evolve as I get deeper into
emberjs.

Installation
============

1. Download the code with git
2. Install the required packages: ``pip install -r REQUIREMENTS.txt``

Running
=======

Woodbox comes with a ``manage.py`` script. Use ``manage.py runserver -d -r``
to run the Woodbox server in debug mode with automatic reloading.

Once it is running, you can go to http://localhost:5000/init to add
some data to the database. Then go to
http://localhost:5000/example-notes to see the content of your
database.

Adding data types
=================

To add new data types:

1. In ``app/models``, create a new file named ``YOUR_TYPE_model.py`` (replace
   YOUR_TYPE by the name of your new data type, in lower case) and
   define your model (have a look at ``example_note_model.py``).
2. in ``app/api_v1``, create a new file name ``YOUR_TYPE.py`` (again, replace
   YOUR_TYPE by the name of your new data type, in lower case) and
   create three classes:

   - ``YourTypeSchema``, used to map database fields to JSON API fields;
   - ``YourTypeAPI``, to link your database model class to your JSON API
     schema for the GET, PATCH and DELETE operations;
   - ``YourTypeListAPI``, to link your database model class to your JSON API
     schema for the POST and LIST operations.

3. In ``app/api_v1/__init__.py``, using ``api.add_resource()``, publish the
   API classes ``YourTypeAPI`` and ``YourTypeListAPI`` on the URLs
   ``/your-types/<item_id>`` and ``/your-types``, respectively. Note the
   plural.

That's it: you now have a REST API to create, read, update and delete
your new type, and your data will be persisted to a SQL database.
