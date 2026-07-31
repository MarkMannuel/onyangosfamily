from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import text
import random
import string
import os
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///family_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['ALLOWED_VIDEO_EXTENSIONS'] = {'mp4', 'webm', 'ogg', 'avi', 'mov', 'mkv'}

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')     # set MAIL_USERNAME env var
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-app-password')        # set MAIL_PASSWORD env var
app.config['MAIL_DEFAULT_SENDER'] = ('Onyango Family', os.environ.get('MAIL_USERNAME', 'your-email@gmail.com'))

mail = Mail(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
login_manager.login_message_category = 'info'

# Database Models
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class FamilyMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(200))
    role = db.Column(db.String(100))
    summary = db.Column(db.Text)
    relationship = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    profile_picture = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')
    must_change_password = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('admin.id'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

    def generate_token(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=64))

    def is_valid(self):
        return not self.used and self.expires_at > datetime.utcnow()


class FamilyTreeNode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    relation = db.Column(db.String(100))
    parent_id = db.Column(db.Integer, db.ForeignKey('family_tree_node.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    children = db.relationship('FamilyTreeNode', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

class FamilyPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100))
    category = db.Column(db.String(50), default='story')
    image_url = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('admin.id'))
    views = db.Column(db.Integer, default=0)

class FamilyPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('admin.id'))

class FamilyVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('admin.id'))

class GuestInvitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120))
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id'))
    
    def generate_code(self):
        prefix = 'FAM'
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
        return f"{prefix}-{random_part}-{suffix}"

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    invitation_code = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_VIDEO_EXTENSIONS']

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# ===== AUTO INVITATION CODE GENERATOR =====
# This runs every 5 minutes to generate a fresh invitation code
def auto_generate_invitation():
    """Background thread that generates a new invitation code every 5 minutes"""
    with app.app_context():
        while True:
            try:
                # Mark old unused codes as expired (older than 5 minutes)
                cutoff = datetime.utcnow() - timedelta(minutes=5)
                old_codes = GuestInvitation.query.filter(
                    GuestInvitation.used == False,
                    GuestInvitation.created_at < cutoff
                ).all()
                for old in old_codes:
                    old.used = True  # Mark as used so they can't be used
                db.session.commit()
                
                # Generate a fresh invitation code
                admin = Admin.query.first()
                if admin:
                    invitation = GuestInvitation()
                    invitation.code = invitation.generate_code()
                    invitation.expires_at = datetime.utcnow() + timedelta(hours=24)
                    invitation.created_by = admin.id
                    db.session.add(invitation)
                    db.session.commit()
                    print(f"[Auto-Generator] New invitation code created: {invitation.code}")
            except Exception as e:
                print(f"[Auto-Generator] Error: {e}")
            
            # Wait 5 minutes before generating the next one
            time.sleep(300)

def get_current_invitation_code():
    """Get the most recent unused invitation code (less than 5 min old)"""
    cutoff = datetime.utcnow() - timedelta(minutes=5)
    invitation = GuestInvitation.query.filter(
        GuestInvitation.used == False,
        GuestInvitation.created_at >= cutoff
    ).order_by(GuestInvitation.created_at.desc()).first()
    return invitation

# Create admin user if not exists
def create_admin():
    db.create_all()
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin', email='admin@family.com')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: username='admin', password='admin123'")
    
    if not GuestInvitation.query.first():
        invitation = GuestInvitation()
        invitation.code = invitation.generate_code()
        invitation.email = "guest@example.com"
        invitation.expires_at = datetime.utcnow().replace(year=datetime.utcnow().year + 1)
        invitation.created_by = 1
        db.session.add(invitation)
        db.session.commit()
        print(f"Test invitation code created: {invitation.code}")

# Routes
@app.route('/')
def home():
    family_members = FamilyMember.query.filter_by(status='approved').all()
    stories = FamilyPost.query.filter_by(status='approved').order_by(FamilyPost.created_at.desc()).limit(3).all()
    photos = FamilyPhoto.query.filter_by(status='approved').order_by(FamilyPhoto.created_at.desc()).limit(6).all()
    videos = FamilyVideo.query.filter_by(status='approved').order_by(FamilyVideo.created_at.desc()).limit(6).all()
    return render_template('index.html', family_members=family_members, stories=stories, photos=photos, videos=videos)

@app.route('/about')
def about():
    family_values = [
        'Respect for elders',
        'Faith, unity, and togetherness',
        'Hard work and discipline',
        'Preserving stories for the next generation',
    ]
    family_history = [
        'The Onyango family has long valued education, hospitality, and strong community bonds.',
        'Gatherings have always been a sacred time to remember ancestors and welcome younger relatives.',
    ]
    return render_template('about.html', family_values=family_values, family_history=family_history)

@app.route('/family-tree')
def family_tree():
    tree_nodes = FamilyTreeNode.query.order_by(FamilyTreeNode.created_at).all()
    return render_template('family_tree.html', tree_nodes=tree_nodes)

@app.route('/gallery')
def gallery():
    photos = FamilyPhoto.query.filter_by(status='approved').order_by(FamilyPhoto.created_at.desc()).all()
    videos = FamilyVideo.query.filter_by(status='approved').order_by(FamilyVideo.created_at.desc()).all()
    return render_template('gallery.html', photos=photos, videos=videos)

@app.route('/member/<int:member_id>')
def member_profile(member_id):
    member = FamilyMember.query.get_or_404(member_id)
    photos = FamilyPhoto.query.filter_by(member_id=member.id, status='approved').order_by(FamilyPhoto.created_at.desc()).all()
    videos = FamilyVideo.query.filter_by(member_id=member.id, status='approved').order_by(FamilyVideo.created_at.desc()).all()
    return render_template('member_profile.html', member=member, photos=photos, videos=videos)

@app.route('/register', methods=['GET', 'POST'])
def register_member():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        summary = request.form.get('summary')
        relationship = request.form.get('relationship')
        phone = request.form.get('phone')
        
        if FamilyMember.query.filter_by(email=email).first():
            flash('A member with this email already exists.', 'warning')
            return redirect(url_for('register_member'))
        
        if FamilyMember.query.filter_by(username=username).first():
            flash('That username is already taken. Please choose another.', 'warning')
            return redirect(url_for('register_member'))
        
        member = FamilyMember(
            name=name,
            username=username,
            email=email,
            role=role,
            summary=summary,
            relationship=relationship,
            phone=phone,
            status='pending'
        )
        if password:
            member.set_password(password)
        
        db.session.add(member)
        db.session.commit()
        
        flash('Registration submitted successfully! You can now log in once an admin approves your account.', 'success')
        return redirect(url_for('member_login'))
    
    return render_template('register.html')


@app.route('/member/login', methods=['GET', 'POST'])
def member_login():
    if 'member_id' in session:
        return redirect(url_for('member_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        member = FamilyMember.query.filter_by(username=username).first()
        
        if member and member.check_password(password):
            if member.status != 'approved':
                flash('Your account has not been approved yet. Please wait for admin approval.', 'warning')
                return render_template('member_login.html')
            
            session['member_id'] = member.id
            session['member_name'] = member.name
            
            # Check if member needs to change password on first login
            if member.must_change_password:
                flash('Please change your password before continuing.', 'warning')
                return redirect(url_for('force_change_password'))
            
            flash(f'Welcome back, {member.name}!', 'success')
            return redirect(url_for('member_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('member_login.html')


@app.route('/member/dashboard')
def member_dashboard():
    if 'member_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('member_login'))
    
    member = FamilyMember.query.get(session['member_id'])
    if not member:
        session.pop('member_id', None)
        session.pop('member_name', None)
        flash('Member not found.', 'danger')
        return redirect(url_for('member_login'))
    
    approved_members = FamilyMember.query.filter_by(status='approved').all()
    approved_posts = FamilyPost.query.filter_by(status='approved').order_by(FamilyPost.created_at.desc()).limit(6).all()
    member_photos = FamilyPhoto.query.filter_by(member_id=member.id, status='approved').order_by(FamilyPhoto.created_at.desc()).all()
    
    return render_template('member_dashboard.html',
                         member=member,
                         members=approved_members[:8],
                         posts=approved_posts,
                         photos=member_photos)


@app.route('/member/logout')
def member_logout():
    session.pop('member_id', None)
    session.pop('member_name', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/submit-story', methods=['GET', 'POST'])
def submit_story():
    if request.method == 'POST':
        title = request.form.get('title')
        body = request.form.get('body')
        author = request.form.get('author')
        category = request.form.get('category', 'story')
        image_url = request.form.get('image_url', '')
        
        post = FamilyPost(
            title=title,
            body=body,
            author=author,
            category=category,
            image_url=image_url,
            status='pending'
        )
        db.session.add(post)
        db.session.commit()
        
        flash('Story submitted successfully! It will be reviewed by an admin.', 'success')
        return redirect(url_for('home'))
    
    return render_template('submit_story.html')

@app.route('/stories')
def stories():
    posts = FamilyPost.query.filter_by(status='approved').order_by(FamilyPost.created_at.desc()).all()
    return render_template('stories.html', posts=posts)

@app.route('/story/<int:post_id>')
def story_detail(post_id):
    post = FamilyPost.query.get_or_404(post_id)
    if post.status != 'approved':
        flash('This story is not available.', 'warning')
        return redirect(url_for('stories'))
    post.views += 1
    db.session.commit()
    return render_template('story_detail.html', post=post)

@app.route('/guest/login', methods=['GET', 'POST'])
def guest_login():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        invitation_code = request.form.get('invitation_code', '').upper().strip()
        
        invitation = GuestInvitation.query.filter_by(
            code=invitation_code, 
            used=False
        ).first()
        
        if not invitation:
            flash('Invalid or expired invitation code. Please contact the family admin.', 'danger')
            return render_template('guest_login.html')
        
        if invitation.expires_at and invitation.expires_at < datetime.utcnow():
            flash('This invitation code has expired. Please request a new one.', 'danger')
            return render_template('guest_login.html')
        
        guest = Guest.query.filter_by(email=email).first()
        if guest:
            guest.name = name
            guest.invitation_code = invitation_code
            guest.last_login = datetime.utcnow()
        else:
            guest = Guest(
                name=name, 
                email=email, 
                invitation_code=invitation_code,
                last_login=datetime.utcnow()
            )
            db.session.add(guest)
        
        invitation.used = True
        db.session.commit()
        
        session['guest_id'] = guest.id
        session['guest_name'] = guest.name
        session['guest_invitation'] = invitation_code
        
        flash('Welcome! You are now viewing as a guest.', 'success')
        return redirect(url_for('guest_dashboard'))
    
    return render_template('guest_login.html')

@app.route('/guest/dashboard')
def guest_dashboard():
    if 'guest_id' not in session:
        flash('Please login as a guest first.', 'warning')
        return redirect(url_for('guest_login'))
    
    posts = FamilyPost.query.filter_by(status='approved').order_by(FamilyPost.created_at.desc()).all()
    members = FamilyMember.query.filter_by(status='approved').all()
    
    return render_template('guest_dashboard.html', 
                         posts=posts[:6], 
                         members=members[:8],
                         guest_name=session.get('guest_name'))

@app.route('/member/<int:member_id>/edit-profile-picture', methods=['POST'])
def edit_profile_picture(member_id):
    member = FamilyMember.query.get_or_404(member_id)
    # Check if member, guest, or admin is logged in
    if 'member_id' not in session and 'guest_id' not in session and not current_user.is_authenticated:
        flash('Please login first.', 'warning')
        return redirect(url_for('member_login'))
    
    file = request.files.get('profile_picture')
    if not file or file.filename == '':
        flash('No file selected.', 'warning')
        return redirect(url_for('member_profile', member_id=member_id))
    if not allowed_file(file.filename):
        flash('File type not allowed. Use png, jpg, jpeg, or gif.', 'warning')
        return redirect(url_for('member_profile', member_id=member_id))

    # If member already has a profile picture, delete the old one
    if member.profile_picture:
        try:
            old_path = os.path.join(app.config['UPLOAD_FOLDER'], member.profile_picture)
            if os.path.exists(old_path):
                os.remove(old_path)
        except Exception:
            pass

    filename = secure_filename(f"profile_{member.id}_" + datetime.utcnow().strftime('%Y%m%d%H%M%S_') + file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)

    member.profile_picture = filename
    db.session.commit()

    flash('Profile picture updated successfully!', 'success')
    return redirect(url_for('member_profile', member_id=member_id))


@app.route('/member/<int:member_id>/upload-photo', methods=['GET', 'POST'])
def upload_photo(member_id):
    member = FamilyMember.query.get_or_404(member_id)
    if request.method == 'POST':
        upload_type = request.form.get('upload_type', 'photo')
        caption = request.form.get('caption', '')

        if upload_type == 'video':
            file = request.files.get('video')
            if not file or file.filename == '':
                flash('No video file selected.', 'warning')
                return redirect(request.url)
            if not allowed_video_file(file.filename):
                flash('File type not allowed. Use mp4, webm, ogg, avi, or mov.', 'warning')
                return redirect(request.url)
            filename = secure_filename(f"video_{member.id}_" + datetime.utcnow().strftime('%Y%m%d%H%M%S_') + file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            video = FamilyVideo(member_id=member.id, filename=filename, caption=caption, status='pending')
            db.session.add(video)
            db.session.commit()
            flash('Video uploaded successfully! Awaiting admin approval.', 'success')
        else:
            file = request.files.get('photo')
            if not file or file.filename == '':
                flash('No file selected.', 'warning')
                return redirect(request.url)
            if not allowed_file(file.filename):
                flash('File type not allowed. Use png, jpg, jpeg, or gif.', 'warning')
                return redirect(request.url)
            filename = secure_filename(f"member_{member.id}_" + datetime.utcnow().strftime('%Y%m%d%H%M%S_') + file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo = FamilyPhoto(member_id=member.id, filename=filename, caption=caption, status='pending')
            db.session.add(photo)
            db.session.commit()
            flash('Photo uploaded successfully! Awaiting admin approval.', 'success')

        return redirect(url_for('member_dashboard'))

    return render_template('upload_photo.html', member=member)

@app.route('/guest/logout')
def guest_logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# ===== PASSWORD RESET ROUTES =====
def generate_random_password(length=10):
    """Generate a random password with letters and digits"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


@app.route('/member/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        member = FamilyMember.query.filter_by(username=username).first()
        
        if member:
            # Auto-generate a new password
            new_password = generate_random_password()
            member.set_password(new_password)
            member.must_change_password = True
            db.session.commit()
            
            # Try to send email via SMTP. If fails (no email server), show password in flash.
            email_sent = False
            try:
                msg = Message(
                    subject='Your Password Has Been Reset - Onyango Family',
                    recipients=[member.email],
                    body=f"""Dear {member.name},

Your password for the Onyango Family portal has been reset.

Your new temporary password is: {new_password}

Please login at the family portal and change your password on first login.

Best regards,
Onyango Family Admin
"""
                )
                mail.send(msg)
                email_sent = True
                print(f"[EMAIL SENT SUCCESS] New password sent to {member.email}")
            except Exception as e:
                print(f"[EMAIL SEND FAILED] Could not send email to {member.email}: {e}")
                print(f"[FALLBACK] New password for {member.name} ({member.email}): {new_password}")
            
            if email_sent:
                flash('A new password has been sent to your email address. Please check your inbox and change it on first login.', 'success')
            else:
                flash(f'A new password has been generated. (Demo mode - email sending not configured. Your temporary password is: <strong>{new_password}</strong>. Please change it on first login.)', 'warning')
        else:
            flash('If that username is registered, a new password has been sent to the registered email.', 'info')
        
        return redirect(url_for('member_login'))
    
    return render_template('member/forgot_password.html')


@app.route('/member/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    
    if not reset_token or not reset_token.is_valid():
        flash('This reset link is invalid or has expired.', 'danger')
        return redirect(url_for('member_login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('member/reset_password.html', token=token)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('member/reset_password.html', token=token)
        
        member = FamilyMember.query.get(reset_token.member_id)
        if not member:
            flash('Member not found.', 'danger')
            return redirect(url_for('member_login'))
        
        member.set_password(password)
        member.must_change_password = True
        reset_token.used = True
        db.session.commit()
        
        flash('Password has been reset successfully! Please log in with your new password. You will be required to change your password on first login.', 'success')
        return redirect(url_for('member_login'))
    
    return render_template('member/reset_password.html', token=token)


@app.route('/member/force-change-password', methods=['GET', 'POST'])
def force_change_password():
    if 'member_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('member_login'))
    
    member = FamilyMember.query.get(session['member_id'])
    if not member:
        session.clear()
        flash('Member not found.', 'danger')
        return redirect(url_for('member_login'))
    
    if not member.must_change_password:
        return redirect(url_for('member_dashboard'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not member.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('member/force_change_password.html', member=member)
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('member/force_change_password.html', member=member)
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('member/force_change_password.html', member=member)
        
        member.set_password(new_password)
        member.must_change_password = False
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('member_dashboard'))
    
    return render_template('member/force_change_password.html', member=member)


# ===== FAMILY TREE ADMIN ROUTES =====
@app.route('/admin/family-tree')
@login_required
def admin_family_tree():
    tree_nodes = FamilyTreeNode.query.order_by(FamilyTreeNode.created_at).all()
    pending_members_count = FamilyMember.query.filter_by(status='pending').count()
    pending_posts_count = FamilyPost.query.filter_by(status='pending').count()
    pending_photos_count = FamilyPhoto.query.filter_by(status='pending').count()
    return render_template('admin/family_tree.html',
                         tree_nodes=tree_nodes,
                         pending_members_count=pending_members_count,
                         pending_posts_count=pending_posts_count,
                         pending_photos_count=pending_photos_count)


@app.route('/admin/family-tree/add', methods=['POST'])
@login_required
def add_tree_node():
    name = request.form.get('name')
    relation = request.form.get('relation', '')
    parent_id = request.form.get('parent_id')
    
    if not name:
        flash('Name is required.', 'danger')
        return redirect(url_for('admin_family_tree'))
    
    node = FamilyTreeNode(
        name=name,
        relation=relation,
        parent_id=int(parent_id) if parent_id else None
    )
    db.session.add(node)
    db.session.commit()
    
    flash(f'"{name}" has been added to the family tree.', 'success')
    return redirect(url_for('admin_family_tree'))


@app.route('/admin/family-tree/<int:node_id>/edit', methods=['POST'])
@login_required
def edit_tree_node(node_id):
    node = FamilyTreeNode.query.get_or_404(node_id)
    name = request.form.get('name')
    relation = request.form.get('relation', '')
    parent_id = request.form.get('parent_id')
    
    if not name:
        flash('Name is required.', 'danger')
        return redirect(url_for('admin_family_tree'))
    
    node.name = name
    node.relation = relation
    node.parent_id = int(parent_id) if parent_id else None
    db.session.commit()
    
    flash(f'"{name}" has been updated.', 'success')
    return redirect(url_for('admin_family_tree'))


@app.route('/admin/family-tree/<int:node_id>/delete')
@login_required
def delete_tree_node(node_id):
    node = FamilyTreeNode.query.get_or_404(node_id)
    name = node.name
    
    # Re-assign children to the parent of the deleted node
    for child in node.children.all():
        child.parent_id = node.parent_id
    
    db.session.delete(node)
    db.session.commit()
    
    flash(f'"{name}" has been removed from the family tree.', 'success')
    return redirect(url_for('admin_family_tree'))


# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            login_user(admin)
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    pending_members = FamilyMember.query.filter_by(status='pending').count()
    pending_posts = FamilyPost.query.filter_by(status='pending').count()
    total_members = FamilyMember.query.count()
    total_posts = FamilyPost.query.count()
    approved_members = FamilyMember.query.filter_by(status='approved').count()
    approved_posts = FamilyPost.query.filter_by(status='approved').count()
    total_guests = Guest.query.count()
    total_invitations = GuestInvitation.query.count()
    used_invitations = GuestInvitation.query.filter_by(used=True).count()
    
    recent_pending_members = FamilyMember.query.filter_by(status='pending').order_by(FamilyMember.submitted_at.desc()).limit(5).all()
    recent_pending_posts = FamilyPost.query.filter_by(status='pending').order_by(FamilyPost.created_at.desc()).limit(5).all()
    recent_invitations = GuestInvitation.query.order_by(GuestInvitation.created_at.desc()).limit(5).all()
    pending_photos = FamilyPhoto.query.filter_by(status='pending').count()
    recent_pending_photos = FamilyPhoto.query.filter_by(status='pending').order_by(FamilyPhoto.created_at.desc()).limit(5).all()
    
    # Get the current active invitation code
    current_invitation = get_current_invitation_code()
    
    return render_template('admin/dashboard.html',
                         pending_members_count=pending_members,
                         pending_posts_count=pending_posts,
                         pending_photos_count=pending_photos,
                         total_members=total_members,
                         total_posts=total_posts,
                         approved_members=approved_members,
                         approved_posts=approved_posts,
                         total_guests=total_guests,
                         total_invitations=total_invitations,
                         used_invitations=used_invitations,
                         pending_members=recent_pending_members,
                         pending_posts=recent_pending_posts,
                         pending_photos=recent_pending_photos,
                         recent_invitations=recent_invitations,
                         current_invitation=current_invitation)

@app.route('/admin/members')
@login_required
def admin_members():
    members = FamilyMember.query.order_by(FamilyMember.submitted_at.desc()).all()
    pending_members_count = FamilyMember.query.filter_by(status='pending').count()
    pending_posts_count = FamilyPost.query.filter_by(status='pending').count()
    pending_photos_count = FamilyPhoto.query.filter_by(status='pending').count()
    return render_template('admin/members.html', members=members,
                         pending_members_count=pending_members_count,
                         pending_posts_count=pending_posts_count,
                         pending_photos_count=pending_photos_count)

@app.route('/admin/members/<int:member_id>/approve')
@login_required
def approve_member(member_id):
    member = FamilyMember.query.get_or_404(member_id)
    member.status = 'approved'
    member.approved_at = datetime.utcnow()
    member.approved_by = current_user.id
    db.session.commit()
    flash(f'Member {member.name} has been approved.', 'success')
    return redirect(url_for('admin_members'))

@app.route('/admin/members/<int:member_id>/reject')
@login_required
def reject_member(member_id):
    member = FamilyMember.query.get_or_404(member_id)
    member.status = 'rejected'
    db.session.commit()
    flash(f'Member {member.name} has been rejected.', 'warning')
    return redirect(url_for('admin_members'))

@app.route('/admin/members/<int:member_id>/reset-password', methods=['GET', 'POST'])
@login_required
def admin_reset_member_password(member_id):
    member = FamilyMember.query.get_or_404(member_id)
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        if not new_password or len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('admin/reset_password.html', member=member)
        
        member.set_password(new_password)
        member.must_change_password = True
        db.session.commit()
        
        email_sent = False
        try:
            msg = Message(
                subject='Your Password Has Been Reset - Onyango Family',
                recipients=[member.email],
                body=f"""Dear {member.name},

An admin has reset your password for the Onyango Family portal.

Your new temporary password is: {new_password}

Please login and change your password immediately.

Best regards,
Onyango Family Admin
"""
            )
            mail.send(msg)
            email_sent = True
            print(f"[ADMIN PASSWORD RESET] Email sent to {member.email}")
        except Exception as e:
            print(f"[ADMIN PASSWORD RESET] Email failed for {member.email}: {e}")
            print(f"[FALLBACK] New password for {member.name} ({member.email}): {new_password}")
        
        if email_sent:
            flash(f'Password for <strong>{member.name}</strong> has been reset and emailed to {member.email}.', 'success')
        else:
            flash(f'Password for <strong>{member.name}</strong> reset. (Email not configured — temporary password: <strong>{new_password}</strong>)', 'warning')
        return redirect(url_for('admin_members'))
    
    return render_template('admin/reset_password.html', member=member)


@app.route('/admin/members/<int:member_id>/delete')
@login_required
def delete_member(member_id):
    member = FamilyMember.query.get_or_404(member_id)
    db.session.delete(member)
    db.session.commit()
    flash(f'Member {member.name} has been deleted.', 'danger')
    return redirect(url_for('admin_members'))

@app.route('/admin/posts')
@login_required
def admin_posts():
    posts = FamilyPost.query.order_by(FamilyPost.created_at.desc()).all()
    pending_members_count = FamilyMember.query.filter_by(status='pending').count()
    pending_posts_count = FamilyPost.query.filter_by(status='pending').count()
    pending_photos_count = FamilyPhoto.query.filter_by(status='pending').count()
    return render_template('admin/posts.html', posts=posts,
                         pending_members_count=pending_members_count,
                         pending_posts_count=pending_posts_count,
                         pending_photos_count=pending_photos_count)

@app.route('/admin/photos')
@login_required
def admin_photos():
    photos = FamilyPhoto.query.order_by(FamilyPhoto.created_at.desc()).all()
    enriched_photos = []
    for p in photos:
        member = FamilyMember.query.get(p.member_id)
        enriched_photos.append({'photo': p, 'member_name': member.name if member else 'Unknown'})

    videos = FamilyVideo.query.order_by(FamilyVideo.created_at.desc()).all()
    enriched_videos = []
    for v in videos:
        member = FamilyMember.query.get(v.member_id)
        enriched_videos.append({'video': v, 'member_name': member.name if member else 'Unknown'})

    pending_members_count = FamilyMember.query.filter_by(status='pending').count()
    pending_posts_count = FamilyPost.query.filter_by(status='pending').count()
    pending_photos_count = FamilyPhoto.query.filter_by(status='pending').count()
    pending_videos_count = FamilyVideo.query.filter_by(status='pending').count()

    return render_template('admin/photos.html',
                           photos=enriched_photos,
                           videos=enriched_videos,
                           pending_members_count=pending_members_count,
                           pending_posts_count=pending_posts_count,
                           pending_photos_count=pending_photos_count,
                           pending_videos_count=pending_videos_count)

@app.route('/admin/photos/<int:photo_id>/approve', methods=['GET', 'POST'])
@login_required
def approve_photo(photo_id):
    set_profile = request.args.get('set_profile', '0') == '1'
    photo = FamilyPhoto.query.get_or_404(photo_id)
    photo.status = 'approved'
    photo.approved_at = datetime.utcnow()
    photo.approved_by = current_user.id
    db.session.commit()

    if set_profile:
        member = FamilyMember.query.get(photo.member_id)
        if member:
            # Remove old profile picture if exists (optional)
            if member.profile_picture:
                try:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], member.profile_picture)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                except:
                    pass
            
            member.profile_picture = photo.filename
            db.session.commit()

    flash('Photo has been approved.', 'success')
    return redirect(url_for('admin_photos'))

@app.route('/admin/photos/<int:photo_id>/reject', methods=['GET', 'POST'])
@login_required
def reject_photo(photo_id):
    photo = FamilyPhoto.query.get_or_404(photo_id)
    photo.status = 'rejected'
    db.session.commit()
    flash('Photo has been rejected.', 'warning')
    return redirect(url_for('admin_photos'))

@app.route('/admin/photos/<int:photo_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_photo(photo_id):
    photo = FamilyPhoto.query.get_or_404(photo_id)
    try:
        path = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
    db.session.delete(photo)
    db.session.commit()
    flash('Photo has been deleted.', 'danger')
    return redirect(url_for('admin_photos'))

@app.route('/admin/videos/<int:video_id>/approve')
@login_required
def approve_video(video_id):
    video = FamilyVideo.query.get_or_404(video_id)
    video.status = 'approved'
    video.approved_at = datetime.utcnow()
    video.approved_by = current_user.id
    db.session.commit()
    flash('Video has been approved.', 'success')
    return redirect(url_for('admin_photos'))

@app.route('/admin/videos/<int:video_id>/reject')
@login_required
def reject_video(video_id):
    video = FamilyVideo.query.get_or_404(video_id)
    video.status = 'rejected'
    db.session.commit()
    flash('Video has been rejected.', 'warning')
    return redirect(url_for('admin_photos'))

@app.route('/admin/videos/<int:video_id>/delete')
@login_required
def delete_video(video_id):
    video = FamilyVideo.query.get_or_404(video_id)
    try:
        path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
    db.session.delete(video)
    db.session.commit()
    flash('Video has been deleted.', 'danger')
    return redirect(url_for('admin_photos'))

@app.route('/admin/posts/<int:post_id>/approve', methods=['POST'])
@login_required
def approve_post(post_id):
    post = FamilyPost.query.get_or_404(post_id)
    post.status = 'approved'
    post.approved_at = datetime.utcnow()
    post.approved_by = current_user.id
    db.session.commit()
    flash(f'Post "{post.title}" has been approved.', 'success')
    return redirect(url_for('admin_posts'))

@app.route('/admin/posts/<int:post_id>/reject', methods=['POST'])
@login_required
def reject_post(post_id):
    post = FamilyPost.query.get_or_404(post_id)
    post.status = 'rejected'
    db.session.commit()
    flash(f'Post "{post.title}" has been rejected.', 'warning')
    return redirect(url_for('admin_posts'))

@app.route('/admin/posts/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = FamilyPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash(f'Post "{post.title}" has been deleted.', 'danger')
    return redirect(url_for('admin_posts'))

# Invitation Management
@app.route('/admin/invitations')
@login_required
def admin_invitations():
    invitations = GuestInvitation.query.order_by(GuestInvitation.created_at.desc()).all()
    return render_template('admin/invitations.html', invitations=invitations, datetime=datetime)

@app.route('/admin/invitations/create', methods=['POST'])
@login_required
def create_invitation():
    email = request.form.get('email', '').strip()
    
    invitation = GuestInvitation()
    invitation.code = invitation.generate_code()
    invitation.email = email if email else None
    invitation.expires_at = datetime.utcnow().replace(year=datetime.utcnow().year + 1)
    invitation.created_by = current_user.id
    
    db.session.add(invitation)
    db.session.commit()
    
    flash(f'Invitation code created: {invitation.code}', 'success')
    return redirect(url_for('admin_invitations'))

@app.route('/admin/invitations/<int:invitation_id>/delete')
@login_required
def delete_invitation(invitation_id):
    invitation = GuestInvitation.query.get_or_404(invitation_id)
    if invitation.used:
        flash('Cannot delete a used invitation.', 'warning')
    else:
        db.session.delete(invitation)
        db.session.commit()
        flash('Invitation deleted successfully.', 'success')
    return redirect(url_for('admin_invitations'))

# Create database and admin user
with app.app_context():
    db.create_all()
    create_admin()
    # Ensure existing SQLite DB has the new columns for family_member
    try:
        res = db.session.execute(text("PRAGMA table_info('family_member')")).fetchall()
        cols = [r[1] for r in res]
        if 'username' not in cols:
            db.session.execute(text('ALTER TABLE family_member ADD COLUMN username VARCHAR(80)'))
            db.session.commit()
            print('Added username column to family_member table')
        if 'profile_picture' not in cols:
            db.session.execute(text('ALTER TABLE family_member ADD COLUMN profile_picture VARCHAR(500)'))
            db.session.commit()
            print('Added profile_picture column to family_member table')
        if 'password_hash' not in cols:
            db.session.execute(text('ALTER TABLE family_member ADD COLUMN password_hash VARCHAR(200)'))
            db.session.commit()
            print('Added password_hash column to family_member table')
        if 'must_change_password' not in cols:
            db.session.execute(text("ALTER TABLE family_member ADD COLUMN must_change_password BOOLEAN DEFAULT 0"))
            db.session.commit()
            print('Added must_change_password column to family_member table')
    except Exception as e:
        print('Could not ensure columns:', e)
    
    # Ensure new tables exist (they will be created by db.create_all(), but just in case)
    try:
        res = db.session.execute(text("PRAGMA table_info('password_reset_token')")).fetchall()
    except Exception:
        print('password_reset_token table will be created by db.create_all()')
    try:
        res = db.session.execute(text("PRAGMA table_info('family_tree_node')")).fetchall()
    except Exception:
        print('family_tree_node table will be created by db.create_all()')
# Start the auto-invitation generator in a background thread
def start_auto_generator():
    """Start the background thread for auto-generating invitation codes"""
    thread = threading.Thread(target=auto_generate_invitation, daemon=True)
    thread.start()
    print("[Auto-Generator] Started - generating new invitation code every 5 minutes")

if __name__ == '__main__':
    start_auto_generator()
    app.run(debug=True, host='0.0.0.0', port=5000)