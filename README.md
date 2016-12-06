# crw-server
Server software for crw Rowing

# Dependencies

 * A running PostgreSQL database
 * psycopg2 for accessing the PostgreSQL database
 * passlib for hashing and salting
 * fastpbkdf2 to speed up hashing and salting

# Testing

Run the (python) unittests by running:

```python -m unittest discover -v```
