#!/bin/sh

#gunicorn wsgi:application -b unix:/tmp/gunicorn.sock -k gevent -w 4

gunicorn wsgi:application -b unix:/tmp/gunicorn.sock
