.. image:: https://travis-ci.org/patrickfournier/woodbox.svg?branch=master
   :target: https://travis-ci.org/patrickfournier/woodbox
   :alt: Travis CI

.. image:: https://codeclimate.com/github/patrickfournier/woodbox/badges/gpa.svg
   :target: https://codeclimate.com/github/patrickfournier/woodbox
   :alt: Code Climate

.. image:: https://codeclimate.com/github/patrickfournier/woodbox/badges/issue_count.svg
   :target: https://codeclimate.com/github/patrickfournier/woodbox
   :alt: Issue Count

.. image:: https://codecov.io/github/patrickfournier/woodbox/coverage.svg?branch=master
   :target: https://codecov.io/github/patrickfournier/woodbox?branch=master
   :alt: Coverage

=======
Woodbox
=======

Woodbox is a framework to quicky build a web service delivering
JSONAPI data from a SQL database over a REST API. It is based on Flask
and uses SQLAlchemy to abstract the database away. It was written with
emberjs in mind.

It is quite basic for now and should evolve as I get deeper into
emberjs.

Installation
============

1. Download the code with git
2. Install the required packages: ``pip install -r REQUIREMENTS.txt``

Features
========

- Use Marshmallow schemas to expose SQL models through a REST API.
- Request authentication using HMAC-256 signatures.
- Use ACL (with Miracle) to restrict access to API URLs.
- Fine grained access control on database records: you decide who can
  access what.

Usage
=====

See Woodbox Example
(https://github.com/patrickfournier/woodbox_example.git) for an
example of how to build an application using Woodbox.
