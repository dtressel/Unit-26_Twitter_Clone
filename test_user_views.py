"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows

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


class UserViewTestCase(TestCase):
    """Test views for user."""

    def setUp(self):
        """Create test client, add sample data."""

        with app.app_context():
            User.query.delete()
            Message.query.delete()

            self.client = app.test_client()

            self.testuser = User.signup(username="testuser",
                                        email="test@test.com",
                                        password="testuserpass",
                                        image_url=None)

            User.signup(username="testuser2",
                        email="test2@test.com",
                        password="testuser2pass",
                        image_url=None)

            db.session.commit()

    def test_render_signup_form(self):
        """Does the signup page render the singup form?"""

        with self.client as c:
            resp = c.get("/signup")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Join Warbler today.</h2>', html)
            self.assertIn('email', html)
            self.assertIn('username', html)
            self.assertIn('image_url', html)
            self.assertIn('password', html)

    def test_register_user(self):
        """Does the singup form register a user?"""

        with app.app_context():
            self.assertEqual(User.query.count(), 2)

            with self.client as c:
                resp = c.post("/signup", data = {
                    'username': 'testuser3',
                    'email': 'test3@test.com',
                    'password': 'testuser3pass'
                    })

                self.assertEqual(resp.status_code, 302)
                self.assertEqual(User.query.count(), 3)

    def test_no_duplicate_username(self):
        """Does the signup form not allow duplicate usernames?
           Does it send you back to the signup page with a flash message?"""

        with app.app_context():
            self.assertEqual(User.query.count(), 2)

            with self.client as c:
                resp = c.post("/signup", data = {
                    'username': 'testuser',
                    'email': 'duplicate@duplicate.com',
                    'password': 'duplicate'
                    })
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('Join Warbler today.</h2>', html)
                self.assertIn('email', html)
                self.assertIn('username', html)
                self.assertIn('image_url', html)
                self.assertIn('password', html)
                self.assertIn('Username already taken', html)
                db.session.rollback()
                self.assertEqual(User.query.count(), 2)

    def test_display_login_page(self):
        """Tests that the login page gets displayed."""

        with self.client as c:
            resp = c.get('/login')
            html = resp.get_data(as_text = True)
    
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Welcome back.</h2>', html)
            self.assertIn('username', html)
            self.assertIn('password', html)

    def test_login_user(self):
        """Tests user successfully logging in from the login form."""

        with self.client as c:
            resp = c.post('login', data = {
                'username': 'testuser',
                'password': 'testuserpass'
            }, follow_redirects = True)
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Hello, testuser!', html)
            self.assertIn('<aside class="col-md-4 col-lg-3 col-sm-12" id="home-aside">', html)

    def test_login_user_failed(self):
        """Tests user failing logging in user because of bad password."""

        with self.client as c:
            resp = c.post('login', data = {
                'username': 'testuser',
                'password': 'testuserpass1'
            })
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Invalid credentials.', html)
            self.assertIn('Welcome back.</h2>', html)
            self.assertIn('username', html)
            self.assertIn('password', html)

    def test_logout_user(self):
        """Tests logging out a user."""

        with self.client as c:
            resp = c.get('/logout', follow_redirects = True)
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('You have successfully logged out.', html)
            self.assertIn('Welcome back.</h2>', html)
            self.assertIn('username', html)
            self.assertIn('password', html)
            
    def test_following_page_login(self):
        """Tests whether you can view the following page when there is a logged in user."""

        with app.app_context():
            user1 = User.query.filter_by(username="testuser").first()
            user2 = User.query.filter_by(username="testuser2").first()
            follow = Follows(user_being_followed_id = user1.id, user_following_id = user2.id)
            db.session.add(follow)
            db.session.commit()
            user1 = User.query.filter_by(username="testuser").first()
            user2 = User.query.filter_by(username="testuser2").first()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id

            resp = c.get(f'/users/{user2.id}/following')
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>@testuser</p>', html)

    def test_following_page_no_log(self):
        """Tests whether you can view the following page when there is NO logged in user."""

        with app.app_context():
            user1 = User.query.filter_by(username="testuser").first()
            user2 = User.query.filter_by(username="testuser2").first()
            follow = Follows(user_being_followed_id = user1.id, user_following_id = user2.id)
            db.session.add(follow)
            db.session.commit()
            user2 = User.query.filter_by(username="testuser2").first()

        with self.client as c:
            resp = c.get(f'/users/{user2.id}/following', follow_redirects = True)
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('<p>@testuser</p>', html)
            self.assertIn('<h4>New to Warbler?</h4>', html)