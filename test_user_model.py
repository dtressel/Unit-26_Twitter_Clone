"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, bcrypt

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
        """Does basic model work?"""

        with app.app_context():
            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )

            db.session.add(u)
            db.session.commit()

            # User should have no messages & no followers
            self.assertEqual(len(u.messages), 0)
            self.assertEqual(len(u.followers), 0)

    def test_repr_method(self):
        """Does the repr method work?"""

        with app.app_context():
            user = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )

            db.session.add(user)
            db.session.commit()

            self.assertIn(str(user.id), str(user.__repr__))
            self.assertIn(user.username, str(user.__repr__))
            self.assertIn(user.email, str(user.__repr__))


    def test_is_followed_by(self):
        """Does is_followed_by successfully detect when user1 is following user2?"""

        with app.app_context():
            user1 =  User(
                email="test1@test.com",
                username="testuser1",
                password="HASHED_PASSWORD1"
            )
            user2 =  User(
                email="test2@test.com",
                username="testuser2",
                password="HASHED_PASSWORD2"
            )
            db.session.add_all([user1, user2])
            db.session.commit()
            follow = Follows(user_being_followed_id = user2.id, user_following_id = user1.id)
            db.session.add(follow)
            db.session.commit()

            self.assertEqual(user2.is_followed_by(user1), 1)
            self.assertEqual(user1.is_followed_by(user2), 0)

    def test_is_following(self):
        """Does is_following successfully detect when user1 is following user2?"""

        with app.app_context():
            user1 =  User(
                email="test1@test.com",
                username="testuser1",
                password="HASHED_PASSWORD1"
            )
            user2 =  User(
                email="test2@test.com",
                username="testuser2",
                password="HASHED_PASSWORD2"
            )
            db.session.add_all([user1, user2])
            db.session.commit()
            follow = Follows(user_being_followed_id = user2.id, user_following_id = user1.id)
            db.session.add(follow)
            db.session.commit()

            self.assertEqual(user2.is_following(user1), 0)
            self.assertEqual(user1.is_following(user2), 1)

    def test_user_signup(self):
        """Does User.signup successfully create a new user given valid credentials?"""

        with app.app_context():
            self.assertEqual(User.query.count(), 0)
        
            User.signup(username="testuser", email="test@test.com", password="coolpass", image_url=None)

            self.assertEqual(User.query.count(), 1)

    def test_user_signup(self):
        """Does User.create fail to create a new user if any of the validations fail?"""

        with app.app_context():
            self.assertEqual(User.query.count(), 0)
        
            User.signup(username="testuser", email="test@test.com", password="coolpass", image_url="http://cookie.com/pic")
            db.session.commit()
            self.assertEqual(User.query.count(), 1)

            try:
                User.signup(username="testuser", email="test2@test.com", password="coolpass2", image_url="http://cookie.com/pic2")
                db.session.commit()
            except:
                db.session.rollback()
            finally:
                self.assertEqual(User.query.count(), 1)

            try:
                User.signup(username=None, email="test3@test.com", password="coolpass3", image_url="http://cookie.com/pic3")
                db.session.commit()
            except:
                db.session.rollback()
            finally:
                self.assertEqual(User.query.count(), 1)

            try:
                User.signup(username="testuser4", email="test4@test.com", password="coolpass4", image_url=None)
                db.session.commit()
            except:
                db.session.rollback()
            finally:
                self.assertEqual(User.query.count(), 2)
            
    def test_user_authenticate_success(self):
        """Does User.authenticate successfully return a user when given a valid username and password?"""

        with app.app_context():
            password = "gea42qga"
            hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')
            user1 =  User(
                email="test1@test.com",
                username="testuser1",
                password=hashed_pwd
            )
            db.session.add(user1)
            db.session.commit()
            self.assertEqual(User.authenticate("testuser1", "gea42qga"), user1)

    def test_user_authenticate_success_fail_username(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""

        with app.app_context():
            password = "gea42qga"
            hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')
            user1 =  User(
                email="test1@test.com",
                username="testuser1",
                password=hashed_pwd
            )
            db.session.add(user1)
            db.session.commit()
            self.assertFalse(User.authenticate("testuser1a", "gea42qga"))

    def test_user_authenticate_success_fail_password(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""

        with app.app_context():
            password = "gea42qga"
            hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')
            user1 =  User(
                email="test1@test.com",
                username="testuser1",
                password=hashed_pwd
            )
            db.session.add(user1)
            db.session.commit()
            self.assertFalse(User.authenticate("testuser1", "gea42qgb"))