"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, datetime

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

with app.app_context():
    db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        with app.app_context():
            User.query.delete()
            Message.query.delete()
            Follows.query.delete()
            db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """rollback session after tests."""

        with app.app_context():
            db.session.rollback()
            User.query.delete()
            Message.query.delete()
            Follows.query.delete()
            db.session.commit()

    def test_user_model(self):
        """Does basic message model work?"""

        with app.app_context():
            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )

            db.session.add(u)
            db.session.commit()

            # User should have no messages
            self.assertEqual(len(u.messages), 0)

            msg = Message(text = "Hello", user_id = u.id)

            db.session.add(msg)
            db.session.commit()

            self.assertEqual(len(u.messages), 1)
            self.assertEqual(u.messages[0].text, "Hello")

    def test_on_user_delete_cascade(self):
        """Does msg get deleted on user deletion?"""

        with app.app_context():
            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )

            db.session.add(u)
            db.session.commit()

            self.assertEqual(Message.query.count(), 0)

            msg = Message(text = "Hello", user_id = u.id)

            db.session.add(msg)
            db.session.commit()

            self.assertEqual(Message.query.count(), 1)

            db.session.delete(u)
            db.session.commit()

            self.assertEqual(Message.query.count(), 0)

    def test_add_message_for_user_non_existant(self):
        """Can you add a message for a non-existant user?"""

        with app.app_context():
            self.assertEqual(Message.query.count(), 0)
            try:
                msg = Message(text = "Hello", user_id = 9999)
                db.session.add(msg)
                db.session.commit()
            except:
                db.session.rollback()
            finally:
                self.assertEqual(Message.query.count(), 0)

    def test_add_timestamp(self):
        """Does the model automatically add a time stamp"""

        with app.app_context():
            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )

            db.session.add(u)
            db.session.commit()

            msg = Message(text = "Hello", user_id = u.id)

            db.session.add(msg)
            db.session.commit()

            self.assertTrue(isinstance(msg.timestamp, datetime))

    def test_not_nullable_columns(self):
        """Does a message get created when not nullable columns are null?"""

        with app.app_context():
            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )

            db.session.add(u)
            db.session.commit()

            self.assertEqual(Message.query.count(), 0)

            try:
                msg = Message(user_id = u.id)
                db.session.add(msg)
                db.session.commit()
            except:
                db.session.rollback()
            finally:
                self.assertEqual(Message.query.count(), 0)

            try:
                msg = Message(text = "Oh boy!")
                db.session.add(msg)
                db.session.commit()
            except:
                db.session.rollback()
            finally:
                self.assertEqual(Message.query.count(), 0)
