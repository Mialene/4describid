from cs50 import SQL
from flask_session import Session
from flask import Flask, render_template, request, redirect, flash, session, jsonify, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

from helpers import login_required, is_username_taken, generate_keyword, validate_word, get_random_noun, check_forbidden_words, has_keyword
from datetime import datetime

import os
import resend

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///4describid.db")

@app.context_processor
def inject_points():
    if session.get("user_id"):
        points = db.execute("SELECT desc_point, forbid_point, guess_point FROM users_point WHERE user_id = ?", session["user_id"])
        return dict(points=points[0] if points else dict(desc_point=0, forbid_point=0, guess_point=0))

    return dict(points=None)

@app.route('/')
def index():
    print(session)
    if session.get("user_id"):
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]['username']
        # Fetch user's active describids
        my_describids = db.execute("SELECT * FROM plays WHERE owner = ? AND " \
        "status != 'concluded' ORDER BY status", session["user_id"])
        active_plays = db.execute(
            """
            SELECT plays.*, users.username AS owner_username, pp.role AS id_role
            FROM plays
            JOIN users ON plays.owner = users.id
            JOIN play_participants pp ON plays.id = pp.play_id
            WHERE pp.user_id = ?
            AND pp.role != 'describer'
            ORDER BY pp.role
            """, 
            session["user_id"]
        )

        return render_template('index.html', username=username, my_describids=my_describids, active_plays=active_plays)
    
    return render_template('index.html')

'''
experimental

'''
app.secret_key = 'this_is_a_secret_key'
# 
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'chu.straight@gmail.com'  # your Gmail
# app.config['MAIL_PASSWORD'] = 'cauv eagz wiwf ewl' # เยี่ยมเรย เพื่อนชื่ออะไรพูด? เติมไปท้ายสุด 
# mail = Mail(app)
resend.api_key = os.getenv("RESEND_API_KEY")
s = URLSafeTimedSerializer(app.secret_key)

def generate_confirmation_token(email):
    return s.dumps(email, salt='email-confirm')

def confirm_token(token, expiration=3600):
    try:
        email = s.loads(
            token,
            salt='email-confirm', #
            max_age=expiration
        )
    except:
        return False
    return email


# this is for resend
resend.api_key = "re_KNCc8nu7_29JNiDxwJGdP2vctcXWaAHLy"

def send_verification_email(email):
    token = generate_confirmation_token(email)
    verify_url = url_for('verify_email', token=token, _external=True)
    html = render_template('activate.html', verify_url=verify_url)

    # here goes nothing
    try:
        params: resend.Emails.SendParams = {
            "from": "4Describid <onboarding@resend.dev>",
            "to": [email],
            "subject": '4Describid | Please confirm your email',
            "html": html
        }

        email_sent = resend.Emails.send(params)
        print(f"Email sent: {email_sent.id}")

    except Exception as e:
        print(f"Error sending email: {e}")
    """
    subject = "4Describid | Please confirm your email"
    msg = Message(subject, 
                  sender="chu.straight@gmail.com", 
                  recipients=[email], 
                  html=html)
        
    mail.send(msg)
    """


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # User did not fill all fields, warns them
        username = request.form.get("username").strip()
        if not username or not request.form.get("password") or not request.form.get("confirmation") or not request.form.get("email"):
            flash("Please enter all fields.")
            return redirect("register")

        # Apology if the username is already taken
        if is_username_taken(username, db):
            flash("This username is already taken.")
            return redirect("register")
        
        # Apology if the email is already taken
        email = request.form.get("email").strip()
        rows = db.execute("SELECT email FROM users WHERE LOWER(email) = LOWER(?)", email)
        if len(rows) > 0:
            flash("This email is already registered.")
            return redirect("register")

        # Passwords do not match
        if request.form.get("password") != request.form.get("confirmation"):
            flash("Passwords do not match")
            return redirect("register")
        
        # record user infos into database for verification
        hash = generate_password_hash(request.form.get("password")) # generate password hash
        db.execute("INSERT INTO users (username, email, hash, verified) VALUES (?,?,?,?)", username, email, hash, False)
        
        send_verification_email(email)
        flash("A confirmation email has been sent via email. Please check your inbox.")
        return redirect("login")
    
    # default access via GET
    return render_template('register.html')

# route for email verification (late or not late)
@app.route('/verify_email') 
def verify_email():  # No argument
    token = request.args.get('token')  # Get it from query string
    try:
        email = confirm_token(token)
    except Exception:
        flash("The confirmation link is invalid or has expired.", "danger")
        return redirect('/login')
    
    user = db.execute("SELECT * FROM users WHERE email = ?", email)
    if user and not user[0]['verified']:
        db.execute("UPDATE users SET verified = ? WHERE email = ?", True, email)
        flash("You have confirmed your account. Please log in.", "success")
    elif user and user[0]['verified']:
        flash("Account already verified. Please log in.", "success")
    else:
        flash("Invalid email address. Try registering again", "danger")
    
    return redirect('/login')

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # User did not fill all fields, warns them
        if not request.form.get("username") or not request.form.get("password"):
            flash("Please enter all fields.")
            return redirect("login")

        # Query database for username
        username = request.form.get("username").strip();
        rows = db.execute(
            "SELECT * FROM users WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)", 
            username, username
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid username, email and/or password")
            return redirect("login")
        
        # Ensure user uses a verified email
        email = rows[0]["email"]
        if not rows[0]["verified"]:
            # prompt user to resend verification email
            flash(f"Please verify your email before logging in. Didn't get it? <a href='/resend_verification?email={email}'>Resend</a>")
            return redirect("login")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        print(session)
        return redirect("/")

    # default access via GET
    return render_template('login.html')

@app.route('/resend_verification')
def resend_verification():
    email = request.args.get('email')
    send_verification_email(email)
    if not email:
        flash("Invalid request.")
        return redirect("login")
    flash("A confirmation email has been sent via email. Please check your inbox.")
    return redirect("login")


"""New Describid page"""
@app.route('/new_describid', methods=['GET', 'POST'])
@login_required
def new_describid():
    if request.method == 'POST':
        action = request.form.get("action")
        if action == "generate":
            existing_keyword = db.execute("SELECT keyword FROM plays WHERE owner = ? AND status = 'creating'", session["user_id"])
            if existing_keyword:   
                # if there's a keyword generated already (user is creating but have been out of the page and returned)
                new_keyword = get_random_noun()

                
                db.execute("UPDATE plays SET keyword = ? WHERE owner = ? AND status = 'creating'", new_keyword, session["user_id"]) 
                return jsonify({
                    'success': True,
                    'keyword': new_keyword
                })
            else:
                # If generate keyword for the first time
                keyword = get_random_noun()
                print(keyword)
                # stay in the same page
                db.execute("INSERT INTO plays (owner, status, keyword) VALUES (?, ?, ?)", int(session["user_id"]), "creating", keyword)
                play_id = db.execute("SELECT id FROM plays WHERE owner = ? AND status = 'creating'", session["user_id"])[0]['id']
                db.execute("INSERT INTO play_participants (play_id, user_id, role) VALUES (?, ?, ?)", play_id, session["user_id"], "describer")

                return jsonify({
                    'success': True,
                    'keyword': keyword
                })
            # reduce token
        elif action == "submit":
            # Handle submission logic here
            # can be hacked
            if len(db.execute("SELECT * FROM plays WHERE owner = ? AND status = 'creating'", session["user_id"])) == 1:
                db.execute("UPDATE plays SET status = 'forbiddable' WHERE owner = ? AND status = 'creating'", session["user_id"])
                flash("Describid submitted!")
                return redirect("/")
            else:
                flash("Hacker detected. You can only submit exactly one word.")
                return redirect("/new_describid")
        
    # default access via GET
    existing_play = db.execute("SELECT keyword FROM plays WHERE owner = ? AND status = 'creating'", session["user_id"])
    if existing_play:   
        return render_template('new_describid.html', keyword=existing_play[0]['keyword'])
    else:
        return render_template('new_describid.html', keyword="")


"""Explore page"""
@app.route('/explore')
@login_required
def explore():
    forbid_plays = db.execute(
        """
        SELECT plays.*, users.username AS owner_username
        FROM plays
        JOIN users ON plays.owner = users.id
        WHERE plays.status = 'forbiddable'
          AND plays.owner != ?
        """,
        session["user_id"],
    )

    guess_plays = db.execute(
    """
    SELECT plays.*, users.username AS owner_username
    FROM plays
    JOIN users ON plays.owner = users.id
    WHERE plays.status = 'guessable'
    AND plays.owner != ?
    AND plays.id NOT IN (
        SELECT play_id 
        FROM play_participants 
        WHERE user_id = ? 
        AND role IN ('forbidder1', 'forbidder2', 'forbidder3', 'guesser')
    )
    """,
    session["user_id"],
    session["user_id"],
    )

    return render_template('explore.html', forbid_plays=forbid_plays, guess_plays=guess_plays)


"""play page"""
@app.route('/play/<int:id>', methods=['GET', 'POST'])
@login_required
def play(id):

    if request.method == 'POST':
        """ Viewing the keyword """
        if request.form.get("action") == "view":
            # no-role user becomes viewer
            db.execute("INSERT INTO play_participants (play_id, user_id, role) VALUES (?, ?, ?)",
                        id, session['user_id'], "viewer")
            return redirect(f'/play/{id}') # this time, user will access via get and have a role now
        
        """ Submitting forbidden words """
        if request.form.get("action") == "submit-fwords":
            # check if another user has already submitted forbidden words
            row = db.execute("SELECT user_id FROM play_participants WHERE play_id = ? AND role LIKE 'forbidder%'", id)
            print(row)

            # if more than 2 forbidders already
            if len(row) >= 2:
                flash(f"Two users have already submitted forbidden words for play id {id}. You cannot submit anymore.")
                return redirect("/explore")

            # check duplication
            new_words = [request.form.get("word1").strip().lower(),
                          request.form.get("word2").strip().lower(),
                            request.form.get("word3").strip().lower()]
            
            if not validate_word(new_words):
                flash("Don't hack me bro. Just input normal words.")
                return redirect(f'/play/{id}')
            
            elif new_words[0] == new_words[1] or new_words[0] == new_words[2] or new_words[1] == new_words[2]:
                flash("Your forbidden words must be different from each other. Please try again.")
                return redirect(f'/play/{id}')
            
            # if there's already one forbidder, check if it's the same user
            if len(row) == 1:  
                print("1 forbidder has exist")
                if row[0]['user_id'] == session['user_id']:
                    flash("You have already submitted forbidden words for this play. " \
                    "You cannot submit twice for the same play.")
                    return redirect(f'/play/{id}')

                existing_words = db.execute("SELECT forbidden_words " \
                "FROM plays WHERE id = ? AND status = 'forbiddable'",
                  id)[0]['forbidden_words'].split(',')
                if any(word in existing_words for word in new_words):
                    print("detect dupes")
                    flash("One of your forbidden words was already submitted by another user. " \
                    "Please choose different words.")
                    return redirect(f'/play/{id}')
                else:
                    # insert the second set of forbidden words and change its status to !!!!describable!!!!
                    combined_words = existing_words + new_words
                    combined_words_str = ','.join(combined_words)
                    db.execute("UPDATE plays SET forbidden_words = ?, status = 'describable' WHERE id = ?", combined_words_str, id)
                    # change role from viewer to forbidder2
                    db.execute("UPDATE play_participants SET role = 'forbidder2' WHERE play_id = ? AND user_id = ?", id, session['user_id'])
                    
            # no row, he's the first forbidder
            else:
                
                db.execute("UPDATE plays SET forbidden_words = ? WHERE id = ?", ','.join(new_words), id)
                db.execute("UPDATE play_participants SET role = 'forbidder1' WHERE play_id = ? AND user_id = ?", id, session['user_id'])

            flash("Forbidden words submitted!")
            return redirect("/") # submit success, back to profile
        
        """ Submitting description """
        if request.form.get("action") == "submit-desc":
            # check if there's a special char
            description = request.form.get("description").strip()
            description_no_spaces = description.replace(" ", "")  # Remove spaces for this check
            if not description_no_spaces.isalpha():
                flash("Description must contain alphabets and spaces only. Please try again.")
                return redirect(f'/play/{id}')

            # check if there're between 10 and 40 chars
            if len(description) < 10 or len(description) > 40:
                flash("Description must be between 10 and 40 characters long. Please try again.")
                return redirect(f'/play/{id}')

            # check if there's no forbidden words
            fwords_result = db.execute("SELECT forbidden_words FROM plays WHERE id = ?", id)
            fwords_string = fwords_result[0]['forbidden_words'] if fwords_result else ""
            fwords_list = fwords_string.split(',') if fwords_string else []

            if check_forbidden_words(description, fwords_list):
                flash("Your description contains one of the forbidden words. Please try again.")
                return redirect(f'/play/{id}')
            
            # check if it contains the keyword
            keyword = db.execute("SELECT keyword FROM plays WHERE id = ?", id)[0]['keyword'].lower()
            if has_keyword(description, keyword):
                flash("Your description contains the keyword. Please try again.")
                return redirect(f'/play/{id}')

            """ All checks passed. Allow user to submit description """
            # insert description into db
            # change status to guessable
            db.execute("UPDATE plays SET description = ?, status = 'guessable' WHERE id = ?", description, id)
                    
            flash("Description submitted!")
            return redirect("/")
        
        """ submitting guess """
        if request.form.get("action") == "submit-guess":
            guess = request.form.get("guess").strip().lower()
            keyword = db.execute("SELECT keyword FROM plays WHERE id = ?", id)[0]['keyword'].lower()
            is_correct = (guess == keyword)

            # record as a participant
            db.execute("INSERT INTO play_participants (play_id, user_id, role, guess_answer, is_correct) VALUES (?, ?, ?, ?, ?)",
                        id, session['user_id'], "guesser", guess, is_correct)
            
            # add points
            if is_correct:
                # add a point to the guesser
                row = db.execute("SELECT * FROM users_point WHERE user_id = ?", session['user_id'])
                if len(row) == 0:
                    db.execute("INSERT INTO users_point (user_id, guess_point) VALUES (?, ?)", session['user_id'], 1)
                else:
                    db.execute("UPDATE users_point SET guess_point = guess_point + 1 WHERE user_id = ?", session['user_id'])

                # add a point to describer
                describer_id = db.execute("SELECT user_id FROM play_participants WHERE play_id = ? AND role = 'describer'", id)[0]['user_id']
                desc_row = db.execute(
                    "SELECT * FROM users_point WHERE user_id  = ?", describer_id
                )
                if len(desc_row) == 0:
                    db.execute("INSERT INTO users_point (user_id, desc_point) VALUES (?, ?)", describer_id, 1)
                else:
                    db.execute("UPDATE users_point SET desc_point = desc_point + 1 WHERE user_id = ?", describer_id)

            else: # (wrong guess)
                # add points to forbidders
                forb1_id = db.execute("SELECT user_id FROM play_participants WHERE play_id = ? AND role = 'forbidder1'", id)[0]['user_id']
                forb1_row = db.execute("SELECT * FROM users_point WHERE user_id = ?", forb1_id)
                forb2_id = db.execute("SELECT user_id FROM play_participants WHERE play_id = ? AND role = 'forbidder2'", id)[0]['user_id']
                forb2_row = db.execute("SELECT * FROM users_point WHERE user_id = ?", forb2_id)

                if len(forb1_row) == 0:
                    db.execute("INSERT INTO users_point (user_id, forbid_point) VALUES (?, ?)", forb1_id, 1)
                else:
                    db.execute("UPDATE users_point SET forbid_point = forbid_point + 1 WHERE user_id = ?", forb1_id)

                if len(forb2_row) == 0:
                    db.execute("INSERT INTO users_point (user_id, forbid_point) VALUES (?, ?)", forb2_id, 1)
                else:
                    db.execute("UPDATE users_point SET forbid_point = forbid_point + 1 WHERE user_id = ?", forb2_id)


            # conclude the play if guessers > 5
            pp_limit = 5
            if len(db.execute("SELECT * FROM play_participants WHERE play_id = ? AND role = 'guesser'", id)) >= pp_limit:
                db.execute("UPDATE plays SET status = 'concluded', end_time = ? WHERE id = ?", datetime.now(), id)
                flash(f"This describid has concluded as it has reached {pp_limit} guessers. Thank you for your participation!")

            return redirect(f'/play/{id}')

    # default access via GET 
    row = db.execute("SELECT role FROM play_participants WHERE play_id = ? AND user_id = ?", 
                    id, session['user_id'])
    role = row[0]['role'] if row else None

    play_info = db.execute("SELECT * FROM plays WHERE id = ?", id)
    status = play_info[0]['status']
    owner_name = db.execute("SELECT username FROM users WHERE id = ?", play_info[0]['owner'])[0]['username']
    desc_info = play_info[0]['description']
    description = desc_info if desc_info else "Not yet provided."
    
    if role:
        # user viewed or participated before
        match (status, role):
            case ('creating', 'describer'):
                return redirect('/new_describid')
            case ('creating', _):
                flash("Still being created. Owner only.")
                return redirect('/explore')
            case ('guessable', 'viewer'):
                flash("You've seen the keyword of this play, thus cannot participate in the guess.")
                return redirect('/explore')
            case _:  # All roles are allowed on other status
                keyword = play_info[0]['keyword']

                f1_info = db.execute("SELECT username FROM users WHERE id IN "
                "(SELECT user_id FROM play_participants WHERE play_id = ? AND role = 'forbidder1')", id)
                f1_username = f1_info[0]['username'] if f1_info else None

                f2_info = db.execute("SELECT username FROM users WHERE id IN "
                "(SELECT user_id FROM play_participants WHERE play_id = ? AND role = 'forbidder2')", id)
                f2_username = f2_info[0]['username'] if f2_info else None

                

                if f1_username:
                    fwords_result = db.execute("SELECT forbidden_words FROM plays WHERE id = ?", id)
                    fwords_string = fwords_result[0]['forbidden_words'] if fwords_result else ""
                    fwords_list = fwords_string.split(',') if fwords_string else []
                else:
                    fwords_list = []

                # guessers' past attempts
                guesses = db.execute("SELECT users.username, pp.guess_answer, pp.is_correct "
                "FROM play_participants pp "
                "JOIN users ON pp.user_id = users.id "
                "WHERE pp.play_id = ? AND pp.role = 'guesser'", id)

                return render_template('play.html', 
                                       play_id=id,
                                       owner_name=owner_name,
                                       status=status, 
                                       role=role,
                                       f1_username=f1_username,
                                       f2_username=f2_username, 
                                       viewed=True, 
                                       keyword=keyword,
                                       fwords_list=fwords_list,
                                       description=description,
                                       guesses=guesses)

    # if role not exist
    else:
        if status == 'creating':
            flash("Still being created. Owner only.")
            return redirect('/explore')
        elif status == 'forbiddable':
            return render_template('play.html',
                                    play_id=id,
                                    owner_name=owner_name,
                                    status=status,
                                    f1_username=None,
                                    f2_username=None,
                                    viewed=False)
        # concluded
        elif status == 'concluded':
            # no-role user becomes viewer
            db.execute("INSERT INTO play_participants (play_id, user_id, role) VALUES (?, ?, 'viewer')", id, session['user_id'])
            return redirect(f'/play/{id}')

        # describable, guessable, 
        return render_template('play.html',
                               play_id=id,
                               owner_name=owner_name, 
                               status=status, 
                               description=description,
                               viewed=False)
    
"""History page"""
@app.route('/history')
@login_required
def history():
    me_played_plays = db.execute(
        """
        SELECT plays.*, users.username AS owner_username, 
        pp.role AS id_role, 
        (
            SELECT COUNT(*) 
            FROM play_participants 
            WHERE play_id = plays.id AND is_correct = 1
        ) AS correct_guess_count,
        (
            SELECT COUNT(*) 
            FROM play_participants 
            WHERE play_id = plays.id AND is_correct = 0
        ) AS incorrect_guess_count
        FROM plays
        JOIN users ON plays.owner = users.id
        JOIN play_participants pp ON plays.id = pp.play_id
        WHERE plays.status = 'concluded'
        AND pp.user_id = ?
        ORDER BY plays.status, pp.role
        """, 
        session["user_id"]
    )

    all_played_plays = db.execute(
        """
        SELECT plays.*, users.username AS owner_username,
        (
            SELECT COUNT(*) 
            FROM play_participants 
            WHERE play_id = plays.id AND is_correct = 1
        ) AS correct_guess_count,
        (
            SELECT COUNT(*)
            FROM play_participants 
            WHERE play_id = plays.id AND is_correct = 0
        ) AS incorrect_guess_count
        FROM plays 
        JOIN users ON plays.owner = users.id
        WHERE plays.status = 'concluded'
        """
    )

    return render_template('history.html', me_played_plays=me_played_plays, all_played_plays=all_played_plays)


"""turn debug on"""
'''
if __name__ == "__main__":
    app.run(debug=True)
'''

if __name__ == "__main__":
    app.run()



