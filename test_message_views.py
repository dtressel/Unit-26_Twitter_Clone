"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

with app.app_context():
    db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        with app.app_context():
            User.query.delete()
            Message.query.delete()

            self.client = app.test_client()

            self.testuser = User.signup(username="testuser",
                                            email="test@test.com",
                                            password="testuser",
                                            image_url=None)

            User.signup(username="testuser2",
                        email="test2@test.com",
                        password="testuser2pass",
                        image_url=None)

            db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with app.app_context():
            user = User.query.filter_by(username="testuser").first()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_message_no_login(self):
        """Can a user add a message when not logged in?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with app.app_context():
            self.assertEqual(Message.query.count(), 0)

            with self.client as c:

                # Now, that session setting is saved, so we can have
                # the rest of ours test

                resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects = True)
                html = resp.get_data(as_text=True)

                # Make sure it redirects
                self.assertEqual(resp.status_code, 200)
                self.assertIn('<h4>New to Warbler?</h4>', html)
                self.assertEqual(Message.query.count(), 0)
                
    def test_add_message_for_another_user(self):
        """Can a user add a message for another user?"""

        with app.app_context():
            user1 = User.query.filter_by(username="testuser").first()
            user2 = User.query.filter_by(username="testuser2").first()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello", "user_id": user2.id})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
            self.assertEqual(msg.user.id, user1.id)

    def test_show_messages(self):
        """Does the message page get rendered and show the message?"""

        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            msg = Message(text = 'Squishy', user_id = user.id)
            db.session.add(msg)
            db.session.commit()

            with self.client as c:
                resp = c.get(f'/messages/{msg.id}')
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('Squishy', html)
                self.assertIn('testuser', html)

    def test_delete_message(self):
        """Does a message get deleted?"""

        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            msg = Message(text = 'Please delete me', user_id = user.id)
            db.session.add(msg)
            db.session.commit()

            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = user.id

                self.assertEqual(Message.query.count(), 1)

                resp = c.post(f'/messages/{msg.id}/delete')

                self.assertEqual(resp.status_code, 302)
                self.assertEqual(Message.query.count(), 0)

    def test_delete_message_no_login(self):
        """Can a user delete a message when not logged in?"""

        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            msg = Message(text = 'Please delete me', user_id = user.id)
            db.session.add(msg)
            db.session.commit()

            with self.client as c:
                self.assertEqual(Message.query.count(), 1)

                resp = c.post(f'/messages/{msg.id}/delete', follow_redirects = True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('<h4>New to Warbler?</h4>', html)
                self.assertEqual(Message.query.count(), 1)

    def test_delete_message_for_another_user(self):
        """Can a user delete another user's message?"""

        with app.app_context():
            user1 = User.query.filter_by(username="testuser").first()
            user2 = User.query.filter_by(username="testuser2").first()
            msg = Message(text = 'Please delete me', user_id = user2.id)
            db.session.add(msg)
            db.session.commit()

            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = user1.id

                self.assertEqual(Message.query.count(), 1)

                resp = c.post(f'/messages/{msg.id}/delete', follow_redirects = True)
                html = resp.get_data(as_text=True)

                self.assertEqual(Message.query.count(), 1)
                self.assertEqual(resp.status_code, 200)
                self.assertIn('<aside class="col-md-4 col-lg-3 col-sm-12" id="home-aside">', html)
                self.assertIn('Access unauthorized.', html)






