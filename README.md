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

# License

The source code of crw is distributed under the GNU Affero General
Public License, either version 3 of the License, or (at your option)
any later version. For the full license see the COPYING file.
