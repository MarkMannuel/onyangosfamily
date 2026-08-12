from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import text
import random
import re
import string
import os
import json

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret-key')

# Serve background images from the root "images/" folder so they can be used
# as CSS background-image sources. Access them at /images/<filename>.
@app.route('/images/<path:filename>')
def serve_background_image(filename):
    return send_from_directory('images', filename)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///family_database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['ALLOWED_VIDEO_EXTENSIONS'] = {'mp4', 'webm', 'ogg', 'avi', 'mov', 'mkv'}
app.config['ALLOWED_AUDIO_EXTENSIONS'] = {'mp3', 'wav', 'ogg', 'm4a', 'aac', 'flac'}
app.config['ALLOWED_DOCUMENT_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'rtf'}

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')     # set MAIL_USERNAME env var
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-app-password')        # set MAIL_PASSWORD env var
app.config['MAIL_DEFAULT_SENDER'] = ('Onyango Family', os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME']))

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
    birthday = db.Column(db.String(20))
    anniversary_date = db.Column(db.String(20))
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
    gender = db.Column(db.String(10), default='male')
    birth_date = db.Column(db.String(20))
    parent_id = db.Column(db.Integer, db.ForeignKey('family_tree_node.id'), nullable=True)
    father_id = db.Column(db.Integer, db.ForeignKey('family_tree_node.id'), nullable=True)
    mother_id = db.Column(db.Integer, db.ForeignKey('family_tree_node.id'), nullable=True)
    spouse_id = db.Column(db.Integer, db.ForeignKey('family_tree_node.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    children = db.relationship('FamilyTreeNode',
                               foreign_keys=[parent_id],
                               backref=db.backref('parent', remote_side=[id]),
                               lazy='dynamic')
    
    def get_spouse(self):
        """Return the spouse node if one exists."""
        if self.spouse_id:
            return FamilyTreeNode.query.get(self.spouse_id)
        return None
    
    def get_father(self):
        """Return the father node if one exists."""
        if self.father_id:
            return FamilyTreeNode.query.get(self.father_id)
        return None
    
    def get_mother(self):
        """Return the mother node if one exists."""
        if self.mother_id:
            return FamilyTreeNode.query.get(self.mother_id)
        return None
    
    def get_children(self):
        """Return all children linked to this node (via father_id, mother_id, or parent_id)."""
        children = []
        seen = set()
        # Children linked via father_id
        for c in FamilyTreeNode.query.filter_by(father_id=self.id).all():
            if c.id not in seen:
                seen.add(c.id)
                children.append(c)
        # Children linked via mother_id
        for c in FamilyTreeNode.query.filter_by(mother_id=self.id).all():
            if c.id not in seen:
                seen.add(c.id)
                children.append(c)
        # Children linked via parent_id (fallback)
        for c in FamilyTreeNode.query.filter_by(parent_id=self.id).all():
            if c.id not in seen:
                seen.add(c.id)
                children.append(c)
        return children

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

class StoryComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('family_post.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PhotoAlbum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('family_member.id'))

class FamilyPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('photo_album.id'))
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

class FamilyEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    event_type = db.Column(db.String(50), default='gathering')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id'))
    is_public = db.Column(db.Boolean, default=True)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id'))

class MessageThread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class MemberPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=False)
    privacy_level = db.Column(db.String(20), default='family')
    allow_messages = db.Column(db.Boolean, default=True)

class EventRSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('family_event.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default='going')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PastEventMedia(db.Model):
    """Photos/videos of past events uploaded by admins, shown in the public gallery."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.Text)
    media_type = db.Column(db.String(10), default='photo')  # 'photo' or 'video'
    filename = db.Column(db.String(500), nullable=False)
    event_date = db.Column(db.String(20))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('admin.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ===== FAMILYWALL-STYLE FEATURE MODELS =====

class FamilyTask(db.Model):
    """Collaborative to-do / checklist item for event planning & daily family coordination."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assigned_to = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=False)
    due_date = db.Column(db.String(20))
    priority = db.Column(db.String(20), default='normal')  # low / normal / high
    category = db.Column(db.String(50), default='general')  # general / event / welfare
    status = db.Column(db.String(20), default='pending')    # pending / in_progress / completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ForumCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), default='fa-comments')
    sort_order = db.Column(db.Integer, default=0)

class ForumThread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('forum_category.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_reply_at = db.Column(db.DateTime, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)

class ForumReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('forum_thread.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WelfareFund(db.Model):
    """A welfare / fund-raising target with a live progress bar."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    target_amount = db.Column(db.Float, default=0)
    raised_amount = db.Column(db.Float, default=0)
    currency = db.Column(db.String(10), default='KES')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WelfareContribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fund_id = db.Column(db.Integer, db.ForeignKey('welfare_fund.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=True)
    contributor_name = db.Column(db.String(100))
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FamilyDocument(db.Model):
    """Shared document vault for land records, certificates, minutes, constitution, etc."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default='general')  # general / land / certificate / minutes / constitution
    filename = db.Column(db.String(500), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FamilyTimelineEvent(db.Model):
    """Major milestone in family history for the interactive heritage timeline."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.String(20), nullable=False)  # e.g. '1950' or '2024-03-15'
    icon = db.Column(db.String(50), default='fa-star')
    color = db.Column(db.String(20), default='#667eea')
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FamilyAudio(db.Model):
    """Audio / oral history recordings from elders."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    speaker = db.Column(db.String(100))
    filename = db.Column(db.String(500), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MemberEditNotification(db.Model):
    """Tracks when a member edits their own profile so admins are notified."""
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=False)
    changes = db.Column(db.Text, nullable=False)  # JSON string describing what changed
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_member(self):
        return FamilyMember.query.get(self.member_id)

class FamilyTeam(db.Model):
    """A team/committee within the family for organizing activities."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    leader_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_leader(self):
        return FamilyMember.query.get(self.leader_id) if self.leader_id else None

class FamilyTeamMember(db.Model):
    """Membership of a member in a team."""
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('family_team.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class FamilyMeeting(db.Model):
    """A scheduled online meeting for the family."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    meeting_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    meeting_link = db.Column(db.String(500))
    team_id = db.Column(db.Integer, db.ForeignKey('family_team.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_team(self):
        return FamilyTeam.query.get(self.team_id) if self.team_id else None

class MeetingNotification(db.Model):
    """Tracks which members have been notified about a meeting."""
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('family_meeting.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_meeting(self):
        return FamilyMeeting.query.get(self.meeting_id)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ===== HOMEPAGE LIVE BACKGROUND SLIDER CONFIG =====
# This list drives the rotating "live" background slider on the homepage.
# Each entry = one slide.
#
# HOW TO CHANGE THE BACKGROUND IMAGE:
#   The "image" value is just the filename of a picture that lives in the
#   images/ folder (e.g. images/myphoto.jpg). To swap a background, put your
#   picture into the images/ folder and edit ONLY the 'image':'yourfile.jpg'
#   value below. Then restart the app.
#
#   Example:  {'image': 'family_1.jpg', ...}  ->  uses images/family_1.jpg
#
# The slider will crossfade + Ken Burns zoom through all listed slides.
HERO_BACKGROUNDS = [
    {'image': 'family1.JPG', 'title': 'Welcome to the Onyango Family', 'text': 'A community bound by love, tradition, and shared heritage. Explore the family tree, share stories, and preserve memories together.', 'badge': 'Building our legacy together', 'icon': 'fa-heart'},
    {'image': 'family2.jpg', 'title': 'Gather, Reconnect, Celebrate', 'text': 'From annual reunions to milestone celebrations, every gathering strengthens the bonds that keep the Onyango spirit alive.', 'badge': 'Annual Reunions & Milestones', 'icon': 'fa-people-arrows'},
    {'image': 'family3.JPG', 'title': 'Rooted in Heritage, Growing in Unity', 'text': 'Our elders carry the wisdom of generations. Walk with us as we preserve ancestral stories and pass them to the next generation.', 'badge': 'Honouring Our Elders', 'icon': 'fa-crown'},
    {'image': 'family4.jpg', 'title': 'Preserving Memories That Matter', 'text': 'Capture cherished moments, upload photos and videos, and keep our family album alive for generations to come.', 'badge': 'Family Photo & Video Archive', 'icon': 'fa-images'},
    {'image': 'family5.jpg', 'title': 'Stronger Together', 'text': 'Support one another through the welfare fund, mentorship, and community initiatives that uplift every branch of the family.', 'badge': 'Welfare & Community Support', 'icon': 'fa-hands-helping'},
    {'image': 'family6.JPG', 'title': 'Passing Down Our Traditions', 'text': 'Language, customs, and stories from the ancestors guide the next generation toward a proud and unified future.', 'badge': 'Ancestral Roots & Customs', 'icon': 'fa-tree'},
    {'image': 'family7.JPG', 'title': 'A Legacy of Faith & Family', 'text': 'Join us in celebrating faith, unity, and togetherness as we build a brighter future across all generations.', 'badge': 'Faith, Unity & Togetherness', 'icon': 'fa-dove'},
]

@app.context_processor
def inject_hero_backgrounds():
    """Make the homepage slider configuration available to all templates."""
    return {'hero_backgrounds': HERO_BACKGROUNDS, 'now': datetime.utcnow()}

@app.template_filter('fromjson')
def fromjson_filter(value):
    """Parse a JSON string into a Python object for use in templates."""
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_VIDEO_EXTENSIONS']

def allowed_audio_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_AUDIO_EXTENSIONS']

def allowed_document_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_DOCUMENT_EXTENSIONS']

def build_family_tree():
    """Build a nested family tree where each unit is a couple (father + mother, or a
    single person), and each couple contains its children (also grouped as couples).
    Children are linked to parents via father_id / mother_id (or parent_id as a
    fallback). This produces a top-level couple, then their children below, then
    grandchildren below each child couple, recursively."""
    nodes = FamilyTreeNode.query.all()
    node_map = {n.id: n for n in nodes}

    def parent_ids(n):
        """Return the set of possible parent ids for this node."""
        ids = set()
        if n.father_id:
            ids.add(n.father_id)
        if n.mother_id:
            ids.add(n.mother_id)
        if n.parent_id:
            ids.add(n.parent_id)
        return ids

    # Map each parent id to its children
    children_map = {}
    for n in nodes:
        for p in parent_ids(n):
            children_map.setdefault(p, []).append(n)

    used = set()

    def make_couple(node):
        """Return a dict representing a couple headed by `node` (and its spouse),
        with their own children nested underneath."""
        spouse = None
        if node.spouse_id and node.spouse_id in node_map:
            spouse = node_map[node.spouse_id]

        used.add(node.id)
        if spouse:
            used.add(spouse.id)

        # Collect the children of this couple. Children may be linked to either the
        # man or the woman (father_id / mother_id / parent_id), so check both.
        couple_child_nodes = []
        seen = set()
        for pid in ([node.id] + ([spouse.id] if spouse else [])):
            for cn in children_map.get(pid, []):
                if cn.id not in used and cn.id not in seen:
                    seen.add(cn.id)
                    couple_child_nodes.append(cn)

        # Group the children into couples: a married child and their spouse should
        # be combined into one couple unit under the same parents.
        child_couples = []
        grouped = set()
        for cn in couple_child_nodes:
            if cn.id in grouped:
                continue
            grouped.add(cn.id)
            # If this child is married to someone who is also a child of this couple,
            # mark the spouse as grouped so they are not rendered separately.
            if cn.spouse_id:
                sp = node_map.get(cn.spouse_id)
                if sp:
                    grouped.add(sp.id)
            child_couples.append(make_couple(cn))

        return {
            'id': node.id,
            'name': node.name,
            'relation': node.relation,
            'gender': getattr(node, 'gender', 'male'),
            'birth_date': getattr(node, 'birth_date', ''),
            'spouse': {
                'id': spouse.id,
                'name': spouse.name,
                'relation': spouse.relation,
                'gender': getattr(spouse, 'gender', 'female'),
                'birth_date': getattr(spouse, 'birth_date', ''),
            } if spouse else None,
            'children': child_couples,
        }

    # Roots are people with no parents. A married root couple should appear just once.
    root_ids = set()
    for n in nodes:
        if not parent_ids(n):
            if n.spouse_id and node_map.get(n.spouse_id) and not parent_ids(node_map[n.spouse_id]):
                spouse = node_map[n.spouse_id]
                if n.id > spouse.id:
                    continue
            root_ids.add(n.id)

    roots = [make_couple(node_map[rid]) for rid in sorted(root_ids)]
    return roots

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    family_members = FamilyMember.query.filter_by(status='approved').all()
    stories = FamilyPost.query.filter_by(status='approved').order_by(FamilyPost.created_at.desc()).limit(3).all()
    photos = PastEventMedia.query.filter_by(media_type='photo').order_by(PastEventMedia.created_at.desc()).limit(6).all()
    videos = PastEventMedia.query.filter_by(media_type='video').order_by(PastEventMedia.created_at.desc()).limit(6).all()
    upcoming_events = FamilyEvent.query.filter(FamilyEvent.event_date >= datetime.utcnow()).order_by(FamilyEvent.event_date.asc()).limit(4).all()
    recent_announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(4).all()
    # Admin-uploaded past event media for the public family gallery sections
    past_media = PastEventMedia.query.order_by(PastEventMedia.created_at.desc()).limit(8).all()
    return render_template('index.html', family_members=family_members, stories=stories, photos=photos, videos=videos,
                           events=upcoming_events, announcements=recent_announcements, past_media=past_media)

@app.route('/about')
def about():
    family_values = [
        'Respect for elders and ancestors',
        'Faith, unity, and togetherness',
        'Hard work, education, and service',
        'Preserving stories and traditions for the next generation',
        'Hospitality, generosity, and community support',
    ]
    family_history = [
        'The Onyango family traces its roots to Baratheng Village in Got-Osimbo Sublocation, East Uholo Location, Sigomere Ward, Ugunja Sub-County within Siaya County, Kenya.',
        'As proud members of the Luo community originating from <em>Joka Keny Ma Uwiny</em>, our heritage is grounded in resilience, unity, and respect for our ancestral lineage.',
        'Over generations, our forefathers settled in Baratheng and built a close-knit extended family anchored by education, hospitality, hard work, and strong cultural values.',
        'Today our family spans Kenya and the world, yet we remain connected through shared stories, celebrations, and a deep commitment to preserving our roots and traditions for future generations.',
    ]
    return render_template('about.html', family_values=family_values, family_history=family_history)

@app.route('/family-tree')
def family_tree():
    tree_nodes = FamilyTreeNode.query.order_by(FamilyTreeNode.created_at).all()
    tree = build_family_tree()
    return render_template('family_tree.html', tree_nodes=tree_nodes, tree=tree)

@app.route('/gallery')
def gallery():
    photos = PastEventMedia.query.filter_by(media_type='photo').order_by(PastEventMedia.created_at.desc()).all()
    videos = PastEventMedia.query.filter_by(media_type='video').order_by(PastEventMedia.created_at.desc()).all()
    return render_template('gallery.html', photos=photos, videos=videos)

@app.route('/directory')
def directory_page():
    members = FamilyMember.query.filter_by(status='approved').order_by(FamilyMember.name.asc()).all()
    return render_template('directory.html', members=members)

@app.route('/member/<int:member_id>')
def member_profile(member_id):
    member = FamilyMember.query.get_or_404(member_id)
    photos = FamilyPhoto.query.filter_by(member_id=member.id, status='approved').order_by(FamilyPhoto.created_at.desc()).all()
    videos = FamilyVideo.query.filter_by(member_id=member.id, status='approved').order_by(FamilyVideo.created_at.desc()).all()
    return render_template('member_profile.html', member=member, photos=photos, videos=videos)

@app.route('/events')
def events_page():
    # Public visitors only see public events
    if 'member_id' not in session:
        events = FamilyEvent.query.filter(
            FamilyEvent.event_date >= datetime.utcnow(),
            FamilyEvent.is_public == True
        ).order_by(FamilyEvent.event_date.asc()).all()
    else:
        # Logged-in members see all upcoming events (public + private)
        events = FamilyEvent.query.filter(FamilyEvent.event_date >= datetime.utcnow()).order_by(FamilyEvent.event_date.asc()).all()
    past_events = PastEventMedia.query.order_by((PastEventMedia.created_at).desc()).all()
    return render_template('events.html', events=events, past_events=past_events,
                         is_member_logged_in='member_id' in session)

@app.route('/events/<int:event_id>/rsvp', methods=['POST'])
def event_rsvp(event_id):
    event = FamilyEvent.query.get_or_404(event_id)
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    status = request.form.get('status', 'going').strip()
    if not name or not email:
        flash('Please provide your name and email to RSVP.', 'warning')
        return redirect(url_for('events_page'))
    rsvp = EventRSVP(event_id=event.id, name=name, email=email, status=status)
    db.session.add(rsvp)
    db.session.commit()
    flash(f'Thank you {name}! Your RSVP for {event.title} has been recorded.', 'success')
    return redirect(url_for('events_page'))

@app.route('/search')
def search_page():
    query = request.args.get('q', '').strip()
    if not query:
        return render_template('search_results.html', query=query, members=[], stories=[], events=[], albums=[])

    members = FamilyMember.query.filter(
        FamilyMember.status == 'approved',
        db.or_(FamilyMember.name.ilike(f'%{query}%'), FamilyMember.relationship.ilike(f'%{query}%'), FamilyMember.summary.ilike(f'%{query}%'))
    ).all()
    stories = FamilyPost.query.filter(
        FamilyPost.status == 'approved',
        db.or_(FamilyPost.title.ilike(f'%{query}%'), FamilyPost.body.ilike(f'%{query}%'), FamilyPost.author.ilike(f'%{query}%'))
    ).all()
    events = FamilyEvent.query.filter(
        FamilyEvent.is_public == True,
        db.or_(FamilyEvent.title.ilike(f'%{query}%'), FamilyEvent.description.ilike(f'%{query}%'), FamilyEvent.location.ilike(f'%{query}%'))
    ).all()
    albums = PhotoAlbum.query.filter(
        db.or_(PhotoAlbum.name.ilike(f'%{query}%'), PhotoAlbum.description.ilike(f'%{query}%'))
    ).all()
    return render_template('search_results.html', query=query, members=members, stories=stories, events=events, albums=albums)

@app.route('/albums')
def albums_page():
    albums = PhotoAlbum.query.order_by(PhotoAlbum.created_at.desc()).all()
    return render_template('albums.html', albums=albums)

@app.route('/albums/<int:album_id>')
def album_detail(album_id):
    album = PhotoAlbum.query.get_or_404(album_id)
    photos = FamilyPhoto.query.filter_by(album_id=album.id, status='approved').order_by(FamilyPhoto.created_at.desc()).all()
    return render_template('album_detail.html', album=album, photos=photos)

@app.route('/announcements')
def announcements_page():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('announcements.html', announcements=announcements)

@app.route('/messages', methods=['GET', 'POST'])
def messages_page():
    if 'member_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('member_login'))

    member = FamilyMember.query.get(session['member_id'])
    if request.method == 'POST':
        receiver_id = request.form.get('receiver_id', type=int)
        subject = request.form.get('subject', '').strip()
        body = request.form.get('body', '').strip()
        if not receiver_id or not subject or not body:
            flash('Please fill in all message fields.', 'warning')
            return redirect(url_for('messages_page'))
        message = MessageThread(sender_id=member.id, receiver_id=receiver_id, subject=subject, body=body)
        db.session.add(message)
        db.session.commit()
        flash('Your message has been sent.', 'success')
        return redirect(url_for('messages_page'))

    messages = MessageThread.query.filter((MessageThread.sender_id == member.id) | (MessageThread.receiver_id == member.id)).order_by(MessageThread.created_at.desc()).all()
    recipients = FamilyMember.query.filter(FamilyMember.id != member.id, FamilyMember.status == 'approved').all()
    return render_template('messages.html', member=member, messages=messages, recipients=recipients)

@app.route('/privacy')
def privacy_page():
    if 'member_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('member_login'))
    member = FamilyMember.query.get(session['member_id'])
    preference = MemberPreference.query.filter_by(member_id=member.id).first()
    if not preference:
        preference = MemberPreference(member_id=member.id)
        db.session.add(preference)
        db.session.commit()
    return render_template('privacy.html', member=member, preference=preference)

@app.route('/privacy/update', methods=['POST'])
def update_privacy():
    if 'member_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('member_login'))
    member = FamilyMember.query.get(session['member_id'])
    preference = MemberPreference.query.filter_by(member_id=member.id).first()
    if not preference:
        preference = MemberPreference(member_id=member.id)
        db.session.add(preference)
    preference.privacy_level = request.form.get('privacy_level', 'family')
    preference.allow_messages = request.form.get('allow_messages') == 'on'
    db.session.commit()
    flash('Your privacy settings have been updated.', 'success')
    return redirect(url_for('privacy_page'))

@app.route('/heritage')
def heritage_page():
    return render_template('heritage.html')

@app.route('/faq')
def faq_page():
    return render_template('faq.html')

@app.route('/support')
def support_page():
    return render_template('support.html')

@app.route('/register', methods=['GET', 'POST'])
def register_member():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        summary = request.form.get('summary')
        relationship = request.form.get('relationship')
        phone = request.form.get('phone')
        birthday = request.form.get('birthday', '').strip()
        
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('register_member'))
        
        if password and (len(password) < 6 or not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password)):
            flash('Password does not meet the required complexity. It must be at least 6 characters and contain letters, digits, and may include special characters.', 'danger')
            return redirect(url_for('register_member'))
        
        if not name or not email:
            flash('Name and email are required.', 'danger')
            return redirect(url_for('register_member'))
        
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
            summary=summary,
            relationship=relationship,
            phone=phone,
            birthday=birthday,
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
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Please enter both your username and password.', 'danger')
            return render_template('member_login.html')

        normalized_username = username.lower()
        member = FamilyMember.query.filter(db.func.lower(FamilyMember.username) == normalized_username).first()

        if member and member.check_password(password):
            if member.status != 'approved':
                flash('Your account has not been approved yet. Please wait for admin approval.', 'warning')
                return render_template('member_login.html')

            session['member_id'] = member.id
            session['member_name'] = member.name

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
    member_videos = FamilyVideo.query.filter_by(member_id=member.id, status='approved').order_by(FamilyVideo.created_at.desc()).all()
    # Teams and meetings
    all_teams = FamilyTeam.query.order_by(FamilyTeam.created_at.desc()).all()
    all_meetings = FamilyMeeting.query.filter(FamilyMeeting.meeting_date >= datetime.utcnow()).order_by(FamilyMeeting.meeting_date.asc()).all()
    my_team_ids = [tm.team_id for tm in FamilyTeamMember.query.filter_by(member_id=member.id).all()]
    my_teams = [t for t in all_teams if t.id in my_team_ids]
    # Meeting notifications
    my_notifications = MeetingNotification.query.filter_by(member_id=member.id, is_read=False).order_by(MeetingNotification.created_at.desc()).all()
    unread_meeting_count = len(my_notifications)
    
    return render_template('member_dashboard.html',
                         member=member,
                         members=approved_members[:8],
                         posts=approved_posts,
                         photos=member_photos,
                         videos=member_videos,
                         all_teams=all_teams,
                         all_meetings=all_meetings,
                         my_teams=my_teams,
                         my_notifications=my_notifications,
                         unread_meeting_count=unread_meeting_count)


@app.route('/member/photos/<int:photo_id>/edit', methods=['GET', 'POST'])
def edit_member_photo(photo_id):
    photo = FamilyPhoto.query.get_or_404(photo_id)
    if 'member_id' not in session or session['member_id'] != photo.member_id:
        flash('You can only edit your own photos.', 'warning')
        return redirect(url_for('member_dashboard'))

    if request.method == 'POST':
        photo.caption = request.form.get('caption', photo.caption)
        db.session.commit()
        flash('Photo caption updated.', 'success')
        return redirect(url_for('member_dashboard'))

    return render_template('edit_media.html', media=photo, media_type='photo')


@app.route('/member/photos/<int:photo_id>/delete')
def delete_member_photo(photo_id):
    photo = FamilyPhoto.query.get_or_404(photo_id)
    if 'member_id' not in session or session['member_id'] != photo.member_id:
        flash('You can only delete your own photos.', 'warning')
        return redirect(url_for('member_dashboard'))

    try:
        path = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

    db.session.delete(photo)
    db.session.commit()
    flash('Your photo has been deleted.', 'danger')
    return redirect(url_for('member_dashboard'))


@app.route('/member/videos/<int:video_id>/edit', methods=['GET', 'POST'])
def edit_member_video(video_id):
    video = FamilyVideo.query.get_or_404(video_id)
    if 'member_id' not in session or session['member_id'] != video.member_id:
        flash('You can only edit your own videos.', 'warning')
        return redirect(url_for('member_dashboard'))

    if request.method == 'POST':
        video.caption = request.form.get('caption', video.caption)
        db.session.commit()
        flash('Video caption updated.', 'success')
        return redirect(url_for('member_dashboard'))

    return render_template('edit_media.html', media=video, media_type='video')


@app.route('/member/videos/<int:video_id>/delete')
def delete_member_video(video_id):
    video = FamilyVideo.query.get_or_404(video_id)
    if 'member_id' not in session or session['member_id'] != video.member_id:
        flash('You can only delete your own videos.', 'warning')
        return redirect(url_for('member_dashboard'))

    try:
        path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

    db.session.delete(video)
    db.session.commit()
    flash('Your video has been deleted.', 'danger')
    return redirect(url_for('member_dashboard'))


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
        image_url = request.form.get('image_url', '').strip()

        story_image = request.files.get('story_image')
        if story_image and story_image.filename != '':
            if allowed_file(story_image.filename):
                filename = secure_filename(f"story_{datetime.utcnow().strftime('%Y%m%d%H%M%S_')}{story_image.filename}")
                story_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = url_for('static', filename=f'uploads/{filename}')
            else:
                flash('Story image file type not allowed. Use png, jpg, jpeg, or gif.', 'warning')
                return redirect(request.url)

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
    comments = StoryComment.query.filter_by(post_id=post.id).order_by(StoryComment.created_at.asc()).all()
    return render_template('story_detail.html', post=post, comments=comments)

@app.route('/story/<int:post_id>/comment', methods=['POST'])
def add_story_comment(post_id):
    post = FamilyPost.query.get_or_404(post_id)
    name = request.form.get('name', '').strip()
    body = request.form.get('body', '').strip()
    if not name or not body:
        flash('Please enter both your name and a comment.', 'warning')
        return redirect(url_for('story_detail', post_id=post.id))
    comment = StoryComment(post_id=post.id, name=name, body=body)
    db.session.add(comment)
    db.session.commit()
    flash('Your comment has been added.', 'success')
    return redirect(url_for('story_detail', post_id=post.id))

@app.route('/member/<int:member_id>/edit-profile-picture', methods=['POST'])
def edit_profile_picture(member_id):
    member = FamilyMember.query.get_or_404(member_id)
    # Check if a member or admin is logged in
    if 'member_id' not in session and not current_user.is_authenticated:
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


@app.route('/member/edit-profile', methods=['GET', 'POST'])
def member_edit_profile():
    """Allow a logged-in member to edit their own profile details."""
    if 'member_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('member_login'))
    
    member = FamilyMember.query.get(session['member_id'])
    if not member:
        session.pop('member_id', None)
        session.pop('member_name', None)
        flash('Member not found.', 'danger')
        return redirect(url_for('member_login'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        relationship = request.form.get('relationship', '').strip()
        role = request.form.get('role', '').strip()
        summary = request.form.get('summary', '').strip()
        birthday = request.form.get('birthday', '').strip()
        anniversary_date = request.form.get('anniversary_date', '').strip()
        
        if not name or not email:
            flash('Name and email are required.', 'danger')
            return render_template('member_edit_profile.html', member=member)
        
        # Track changes for admin notification
        changes = []
        if name != member.name:
            changes.append(f'Name: "{member.name}" → "{name}"')
        if email != member.email:
            changes.append(f'Email: "{member.email}" → "{email}"')
        if phone != (member.phone or ''):
            changes.append(f'Phone: "{member.phone or ""}" → "{phone}"')
        if relationship != (member.relationship or ''):
            changes.append(f'Relationship: "{member.relationship or ""}" → "{relationship}"')
        if role != (member.role or ''):
            changes.append(f'Role: "{member.role or ""}" → "{role}"')
        if summary != (member.summary or ''):
            changes.append('About/Summary updated')
        if birthday != (member.birthday or ''):
            changes.append(f'Birthday: "{member.birthday or ""}" → "{birthday}"')
        if anniversary_date != (member.anniversary_date or ''):
            changes.append(f'Anniversary: "{member.anniversary_date or ""}" → "{anniversary_date}"')
        
        # Update member
        member.name = name
        member.email = email
        member.phone = phone
        member.relationship = relationship
        member.role = role
        member.summary = summary
        member.birthday = birthday
        member.anniversary_date = anniversary_date
        db.session.commit()
        
        # Notify admin if changes were made
        if changes:
            notification = MemberEditNotification(
                member_id=member.id,
                changes=json.dumps(changes)
            )
            db.session.add(notification)
            db.session.commit()
            flash('Your profile has been updated. The admin has been notified of your changes.', 'success')
        else:
            flash('No changes were made to your profile.', 'info')
        
        return redirect(url_for('member_profile', member_id=member.id))
    
    return render_template('member_edit_profile.html', member=member)


@app.route('/member/<int:member_id>/upload-photo', methods=['GET', 'POST'])
def upload_photo(member_id):
    member = FamilyMember.query.get_or_404(member_id)
    if 'member_id' not in session or session['member_id'] != member.id:
        flash('You can only upload media to your own profile.', 'warning')
        return redirect(url_for('member_dashboard'))
    if request.method == 'POST':
        upload_type = request.form.get('upload_type', 'photo')
        caption = request.form.get('caption', '')
        album_name = request.form.get('album_name', '').strip()
        album_id = request.form.get('album_id', type=int)

        album = None
        if album_name:
            album = PhotoAlbum.query.filter_by(name=album_name).first()
            if not album:
                album = PhotoAlbum(name=album_name, description='Created from upload', created_by=member.id)
                db.session.add(album)
                db.session.flush()
        elif album_id:
            album = PhotoAlbum.query.get(album_id)

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
            photo = FamilyPhoto(member_id=member.id, album_id=album.id if album else None, filename=filename, caption=caption, status='pending')
            db.session.add(photo)
            db.session.commit()
            flash('Photo uploaded successfully! Awaiting admin approval.', 'success')

        return redirect(url_for('member_dashboard'))

    albums = PhotoAlbum.query.order_by(PhotoAlbum.created_at.desc()).all()
    return render_template('upload_photo.html', member=member, albums=albums)

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
    tree = build_family_tree()
    pending_members_count = FamilyMember.query.filter_by(status='pending').count()
    pending_posts_count = FamilyPost.query.filter_by(status='pending').count()
    pending_photos_count = FamilyPhoto.query.filter_by(status='pending').count()
    return render_template('admin/family_tree.html',
                         tree_nodes=tree_nodes,
                         tree=tree,
                         pending_members_count=pending_members_count,
                         pending_posts_count=pending_posts_count,
                         pending_photos_count=pending_photos_count)


@app.route('/admin/family-tree/add', methods=['POST'])
@login_required
def add_tree_node():
    name = request.form.get('name')
    relation = request.form.get('relation', '')
    gender = request.form.get('gender', 'male')
    birth_date = request.form.get('birth_date', '')
    parent_id = request.form.get('parent_id')
    father_id = request.form.get('father_id')
    mother_id = request.form.get('mother_id')
    spouse_id = request.form.get('spouse_id')
    
    if not name:
        flash('Name is required.', 'danger')
        return redirect(url_for('admin_family_tree'))
    
    node = FamilyTreeNode(
        name=name,
        relation=relation,
        gender=gender,
        birth_date=birth_date,
        parent_id=int(parent_id) if parent_id else None,
        father_id=int(father_id) if father_id else None,
        mother_id=int(mother_id) if mother_id else None,
        spouse_id=int(spouse_id) if spouse_id else None
    )
    db.session.add(node)
    db.session.flush()
    
    # Link spouse in both directions
    if node.spouse_id:
        spouse = FamilyTreeNode.query.get(node.spouse_id)
        if spouse and not spouse.spouse_id and spouse.id != node.id:
            spouse.spouse_id = node.id
            # Inherit parent links from the new node if the spouse has none
            if node.parent_id and not spouse.parent_id:
                spouse.parent_id = node.parent_id
            if node.father_id and not spouse.father_id:
                spouse.father_id = node.father_id
            if node.mother_id and not spouse.mother_id:
                spouse.mother_id = node.mother_id
    
    db.session.commit()
    
    flash(f'"{name}" has been added to the family tree.', 'success')
    return redirect(url_for('admin_family_tree'))


@app.route('/admin/family-tree/add-couple', methods=['POST'])
@login_required
def add_tree_couple():
    """Add a couple (husband + wife) together as a single unit."""
    husband_name = request.form.get('husband_name')
    wife_name = request.form.get('wife_name')
    husband_birth = request.form.get('husband_birth_date', '')
    wife_birth = request.form.get('wife_birth_date', '')
    parent_id = request.form.get('parent_id')
    
    if not husband_name or not wife_name:
        flash('Both husband and wife names are required.', 'danger')
        return redirect(url_for('admin_family_tree'))
    
    # Create husband
    husband = FamilyTreeNode(
        name=husband_name,
        relation='Husband',
        gender='male',
        birth_date=husband_birth,
        parent_id=int(parent_id) if parent_id else None,
        father_id=int(parent_id) if parent_id else None,
        mother_id=None
    )
    db.session.add(husband)
    db.session.flush()
    
    # Create wife
    wife = FamilyTreeNode(
        name=wife_name,
        relation='Wife',
        gender='female',
        birth_date=wife_birth,
        parent_id=int(parent_id) if parent_id else None,
        father_id=int(parent_id) if parent_id else None,
        mother_id=None
    )
    db.session.add(wife)
    db.session.flush()
    
    # Link them as spouses
    husband.spouse_id = wife.id
    wife.spouse_id = husband.id
    
    db.session.commit()
    
    flash(f'Couple "{husband_name}" & "{wife_name}" has been added to the family tree.', 'success')
    return redirect(url_for('admin_family_tree'))


@app.route('/admin/family-tree/<int:parent_id>/add-child', methods=['POST'])
@login_required
def add_tree_child(parent_id):
    parent = FamilyTreeNode.query.get_or_404(parent_id)
    name = request.form.get('name')
    gender = request.form.get('gender', 'male')
    birth_date = request.form.get('birth_date', '')
    
    if not name:
        flash('Name is required.', 'danger')
        return redirect(url_for('admin_family_tree'))
    
    relation = 'Son' if gender == 'male' else 'Daughter'
    
    # If parent has a spouse, link the child to both parents
    spouse = parent.get_spouse()
    child = FamilyTreeNode(
        name=name,
        relation=relation,
        gender=gender,
        birth_date=birth_date,
        parent_id=parent.id,
        father_id=parent.id if parent.gender == 'male' else (spouse.id if spouse and spouse.gender == 'male' else None),
        mother_id=parent.id if parent.gender == 'female' else (spouse.id if spouse and spouse.gender == 'female' else None)
    )
    db.session.add(child)
    db.session.commit()
    
    flash(f'"{name}" has been added as a {relation} of {parent.name}.', 'success')
    return redirect(url_for('admin_family_tree'))

@app.route('/admin/family-tree/<int:node_id>/add-spouse', methods=['POST'])
@login_required
def add_tree_spouse(node_id):
    person = FamilyTreeNode.query.get_or_404(node_id)
    name = request.form.get('name')
    birth_date = request.form.get('birth_date', '')
    gender = 'female' if (person.gender or 'male') != 'female' else 'male'
    
    if not name:
        flash('Name is required.', 'danger')
        return redirect(url_for('admin_family_tree'))
    
    relation = 'Wife' if gender == 'female' else 'Husband'
    # A spouse belongs to the same generation and household as the person, but is
    # NOT linked as a child of the person's parents (so they render as a couple, not
    # as two separate children). We copy the parent links so the couple stays nested
    # correctly under the same parents.
    spouse = FamilyTreeNode(
        name=name,
        relation=relation,
        gender=gender,
        birth_date=birth_date,
        parent_id=person.parent_id,
        father_id=person.father_id,
        mother_id=person.mother_id
    )
    db.session.add(spouse)
    db.session.flush()
    
    person.spouse_id = spouse.id
    spouse.spouse_id = person.id
    db.session.commit()
    
    flash(f'"{name}" has been added as the {relation} of {person.name}.', 'success')
    return redirect(url_for('admin_family_tree'))


@app.route('/admin/family-tree/<int:node_id>/edit', methods=['POST'])
@login_required
def edit_tree_node(node_id):
    node = FamilyTreeNode.query.get_or_404(node_id)
    name = request.form.get('name')
    relation = request.form.get('relation', '')
    gender = request.form.get('gender', node.gender or 'male')
    birth_date = request.form.get('birth_date', '')
    parent_id = request.form.get('parent_id')
    father_id = request.form.get('father_id')
    mother_id = request.form.get('mother_id')
    spouse_id = request.form.get('spouse_id')
    
    if not name:
        flash('Name is required.', 'danger')
        return redirect(url_for('admin_family_tree'))
    
    node.name = name
    node.relation = relation
    node.gender = gender
    node.birth_date = birth_date
    node.parent_id = int(parent_id) if parent_id else None
    node.father_id = int(father_id) if father_id else None
    node.mother_id = int(mother_id) if mother_id else None
    node.spouse_id = int(spouse_id) if spouse_id else None
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
    pending_photos = FamilyPhoto.query.filter_by(status='pending').count()
    recent_pending_members = FamilyMember.query.filter_by(status='pending').order_by(FamilyMember.submitted_at.desc()).limit(5).all()
    recent_pending_posts = FamilyPost.query.filter_by(status='pending').order_by(FamilyPost.created_at.desc()).limit(5).all()
    recent_pending_photos = FamilyPhoto.query.filter_by(status='pending').order_by(FamilyPhoto.created_at.desc()).limit(5).all()
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    events = FamilyEvent.query.order_by(FamilyEvent.event_date.asc()).all()
    upcoming_events = FamilyEvent.query.filter(FamilyEvent.event_date >= datetime.utcnow()).order_by(FamilyEvent.event_date.asc()).all()
    past_media = PastEventMedia.query.order_by(PastEventMedia.created_at.desc()).limit(8).all()
    # Family tree data for dashboard management
    tree_nodes = FamilyTreeNode.query.order_by(FamilyTreeNode.created_at).all()
    tree = build_family_tree()
    tree_stats = {
        'total_nodes': FamilyTreeNode.query.count(),
        'total_roots': len(tree) if tree else 0,
        'total_males': FamilyTreeNode.query.filter_by(gender='male').count(),
        'total_females': FamilyTreeNode.query.filter_by(gender='female').count(),
    }
    # Member edit notifications
    member_edit_notifications = MemberEditNotification.query.order_by(MemberEditNotification.created_at.desc()).limit(10).all()
    unread_notifications_count = MemberEditNotification.query.filter_by(is_read=False).count()
    # Teams and meetings
    all_teams = FamilyTeam.query.order_by(FamilyTeam.created_at.desc()).all()
    all_meetings = FamilyMeeting.query.order_by(FamilyMeeting.meeting_date.asc()).all()
    approved_members_list = FamilyMember.query.filter_by(status='approved').all()
    # RSVP records
    all_rsvps = EventRSVP.query.order_by(EventRSVP.created_at.desc()).all()
    rsvp_list = []
    for rsvp in all_rsvps:
        event = FamilyEvent.query.get(rsvp.event_id)
        rsvp_list.append({
            'rsvp': rsvp,
            'event_title': event.title if event else 'Unknown Event'
        })
    
    return render_template('admin/dashboard.html',
                         pending_members_count=pending_members,
                         pending_posts_count=pending_posts,
                         pending_photos_count=pending_photos,
                         total_members=total_members,
                         total_posts=total_posts,
                         approved_members=approved_members,
                         approved_posts=approved_posts,
                         pending_members=recent_pending_members,
                         pending_posts=recent_pending_posts,
                         pending_photos=recent_pending_photos,
                         announcements=announcements,
                         events=events,
                         upcoming_events=upcoming_events,
                         past_media=past_media,
                         tree_nodes=tree_nodes,
                         tree=tree,
                         tree_stats=tree_stats,
                         member_edit_notifications=member_edit_notifications,
                         unread_notifications_count=unread_notifications_count,
                         all_teams=all_teams,
                         all_meetings=all_meetings,
                         approved_members_list=approved_members_list,
                         rsvp_list=rsvp_list)

@app.route('/admin/teams/create', methods=['POST'])
@login_required
def create_team():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    leader_id = request.form.get('leader_id', type=int)
    member_ids = request.form.getlist('member_ids')
    
    if not name:
        flash('Team name is required.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    team = FamilyTeam(name=name, description=description, leader_id=leader_id, created_by=current_user.id)
    db.session.add(team)
    db.session.flush()
    
    # Add members to the team
    for mid in member_ids:
        if mid:
            membership = FamilyTeamMember(team_id=team.id, member_id=int(mid))
            db.session.add(membership)
    
    db.session.commit()
    flash(f'Team "{name}" has been created.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/teams/<int:team_id>/delete')
@login_required
def delete_team(team_id):
    team = FamilyTeam.query.get_or_404(team_id)
    name = team.name
    # Delete memberships
    FamilyTeamMember.query.filter_by(team_id=team.id).delete()
    db.session.delete(team)
    db.session.commit()
    flash(f'Team "{name}" has been deleted.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/meetings/create', methods=['POST'])
@login_required
def create_meeting():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    meeting_date = request.form.get('meeting_date', '').strip()
    duration_minutes = request.form.get('duration_minutes', type=int, default=60)
    meeting_link = request.form.get('meeting_link', '').strip()
    team_id = request.form.get('team_id', type=int)
    is_public = request.form.get('is_public') == 'on'
    
    if not title or not meeting_date:
        flash('Title and meeting date are required.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    meeting = FamilyMeeting(
        title=title,
        description=description,
        meeting_date=datetime.strptime(meeting_date, '%Y-%m-%dT%H:%M'),
        duration_minutes=duration_minutes or 60,
        meeting_link=meeting_link,
        team_id=team_id,
        created_by=current_user.id,
        is_public=is_public
    )
    db.session.add(meeting)
    db.session.flush()
    
    # Notify all approved members about the meeting
    all_approved = FamilyMember.query.filter_by(status='approved').all()
    for m in all_approved:
        notification = MeetingNotification(meeting_id=meeting.id, member_id=m.id)
        db.session.add(notification)
    
    db.session.commit()
    flash(f'Meeting "{title}" has been scheduled. All members have been notified.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/meetings/<int:meeting_id>/send-reminder')
@login_required
def send_meeting_reminder(meeting_id):
    """Resend meeting notifications to all approved members."""
    meeting = FamilyMeeting.query.get_or_404(meeting_id)
    all_approved = FamilyMember.query.filter_by(status='approved').all()
    for m in all_approved:
        existing = MeetingNotification.query.filter_by(meeting_id=meeting.id, member_id=m.id).first()
        if not existing:
            notification = MeetingNotification(meeting_id=meeting.id, member_id=m.id)
            db.session.add(notification)
    db.session.commit()
    flash(f'Reminders sent for "{meeting.title}" to all members.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/member/meetings/read', methods=['POST'])
def mark_meetings_read():
    """Mark all meeting notifications as read for the logged-in member."""
    if 'member_id' not in session:
        return redirect(url_for('member_login'))
    MeetingNotification.query.filter_by(member_id=session['member_id'], is_read=False).update({'is_read': True})
    db.session.commit()
    return redirect(url_for('member_dashboard'))

@app.route('/admin/meetings/<int:meeting_id>/delete')
@login_required
def delete_meeting(meeting_id):
    meeting = FamilyMeeting.query.get_or_404(meeting_id)
    title = meeting.title
    db.session.delete(meeting)
    db.session.commit()
    flash(f'Meeting "{title}" has been deleted.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/rsvps/<int:rsvp_id>/delete', methods=['POST'])
@login_required
def admin_delete_rsvp(rsvp_id):
    rsvp = EventRSVP.query.get_or_404(rsvp_id)
    db.session.delete(rsvp)
    db.session.commit()
    flash('RSVP deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/member/teams/<int:team_id>/join')
def join_team(team_id):
    if 'member_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('member_login'))
    member_id = session['member_id']
    existing = FamilyTeamMember.query.filter_by(team_id=team_id, member_id=member_id).first()
    if not existing:
        membership = FamilyTeamMember(team_id=team_id, member_id=member_id)
        db.session.add(membership)
        db.session.commit()
        flash('You have joined the team!', 'success')
    else:
        flash('You are already a member of this team.', 'info')
    return redirect(url_for('member_dashboard'))

@app.route('/member/teams/<int:team_id>/leave')
def leave_team(team_id):
    if 'member_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('member_login'))
    member_id = session['member_id']
    membership = FamilyTeamMember.query.filter_by(team_id=team_id, member_id=member_id).first()
    if membership:
        db.session.delete(membership)
        db.session.commit()
        flash('You have left the team.', 'info')
    return redirect(url_for('member_dashboard'))

@app.route('/admin/events')
@login_required
def admin_events():
    events = FamilyEvent.query.order_by(FamilyEvent.event_date.asc()).all()
    past_events = PastEventMedia.query.order_by(PastEventMedia.created_at.desc()).all()
    pending_members_count = FamilyMember.query.filter_by(status='pending').count()
    pending_posts_count = FamilyPost.query.filter_by(status='pending').count()
    pending_photos_count = FamilyPhoto.query.filter_by(status='pending').count()
    return render_template('admin/events.html', events=events, past_events=past_events,
                         pending_members_count=pending_members_count,
                         pending_posts_count=pending_posts_count,
                         pending_photos_count=pending_photos_count)

@app.route('/admin/announcements', methods=['GET', 'POST'])
@login_required
def admin_announcements():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        body = request.form.get('body', '').strip()
        if not title or not body:
            flash('Title and body are required.', 'warning')
            return redirect(url_for('admin_dashboard'))
        announcement = Announcement(title=title, body=body, created_by=current_user.id)
        db.session.add(announcement)
        db.session.commit()
        flash('Announcement created successfully.', 'success')
        return redirect(url_for('admin_dashboard'))
    # Announcements are managed directly on the admin dashboard
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/announcements/<int:announcement_id>/delete', methods=['POST'])
@login_required
def delete_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    title = announcement.title
    db.session.delete(announcement)
    db.session.commit()
    flash(f'Announcement "{title}" has been deleted.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/events/create', methods=['POST'])
@login_required
def create_event():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    event_date = request.form.get('event_date', '').strip()
    location = request.form.get('location', '').strip()
    event_type = request.form.get('event_type', 'gathering').strip()
    # Visibility: 'public' = visible to everyone on the website, 'private' = members portal only
    visibility = request.form.get('visibility', 'public').strip()
    is_public = True if visibility == 'public' else False
    if not title or not event_date:
        flash('Title and date are required for an event.', 'warning')
        return redirect(url_for('admin_events'))
    event = FamilyEvent(title=title, description=description, event_date=datetime.strptime(event_date, '%Y-%m-%dT%H:%M'), location=location, event_type=event_type, created_by=current_user.id, is_public=is_public)
    db.session.add(event)
    db.session.commit()
    if is_public:
        flash(f'Event "{title}" has been created and posted on the public website.', 'success')
    else:
        flash(f'Event "{title}" has been created and shared with registered members only.', 'success')
    return redirect(url_for('admin_events'))

@app.route('/admin/events/<int:event_id>/edit', methods=['POST'])
@login_required
def edit_event(event_id):
    event = FamilyEvent.query.get_or_404(event_id)
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    event_date = request.form.get('event_date', '').strip()
    location = request.form.get('location', '').strip()
    event_type = request.form.get('event_type', 'gathering').strip()
    is_public = request.form.get('is_public') == 'on'
    
    if not title or not event_date:
        flash('Title and date are required for an event.', 'warning')
        return redirect(url_for('admin_events'))
    
    event.title = title
    event.description = description
    event.event_date = datetime.strptime(event_date, '%Y-%m-%dT%H:%M')
    event.location = location
    event.event_type = event_type
    event.is_public = is_public
    db.session.commit()
    
    flash(f'Event "{title}" has been updated.', 'success')
    return redirect(url_for('admin_events'))

@app.route('/admin/events/<int:event_id>/delete')
@login_required
def delete_event(event_id):
    event = FamilyEvent.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully.', 'danger')
    return redirect(url_for('admin_events'))

@app.route('/admin/past-events/upload', methods=['POST'])
@login_required
def upload_past_event():
    """Admin uploads a photo or video with a caption for the past events gallery."""
    title = request.form.get('title', '').strip()
    caption = request.form.get('caption', '').strip()
    media_type = request.form.get('media_type', 'photo').strip()
    event_date = request.form.get('event_date', '').strip()
    file = request.files.get('media')

    if not title or not file or file.filename == '':
        flash('A title and a media file are required.', 'warning')
        return redirect(url_for('admin_events'))

    if media_type == 'video':
        if not allowed_video_file(file.filename):
            flash('File type not allowed for video. Use mp4, webm, ogg, avi, mov, or mkv.', 'warning')
            return redirect(url_for('admin_events'))
        filename = secure_filename(f"pastevent_video_{datetime.utcnow().strftime('%Y%m%d%H%M%S_')}" + file.filename)
    else:
        if not allowed_file(file.filename):
            flash('File type not allowed for photo. Use png, jpg, jpeg, or gif.', 'warning')
            return redirect(url_for('admin_events'))
        media_type = 'photo'
        filename = secure_filename(f"pastevent_photo_{datetime.utcnow().strftime('%Y%m%d%H%M%S_')}" + file.filename)

    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    record = PastEventMedia(
        title=title,
        caption=caption,
        media_type=media_type,
        filename=filename,
        event_date=event_date,
        uploaded_by=current_user.id
    )
    db.session.add(record)
    db.session.commit()

    flash(f'"{title}" has been added to the past events gallery.', 'success')
    return redirect(url_for('admin_events'))

@app.route('/admin/past-events/<int:event_id>/delete')
@login_required
def delete_past_event(event_id):
    record = PastEventMedia.query.get_or_404(event_id)
    try:
        path = os.path.join(app.config['UPLOAD_FOLDER'], record.filename)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
    db.session.delete(record)
    db.session.commit()
    flash('Past event media has been deleted.', 'danger')
    return redirect(url_for('admin_events'))

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

@app.route('/admin/members/<int:member_id>')
@login_required
def admin_member_detail(member_id):
    member = FamilyMember.query.get_or_404(member_id)
    pending_members_count = FamilyMember.query.filter_by(status='pending').count()
    pending_posts_count = FamilyPost.query.filter_by(status='pending').count()
    pending_photos_count = FamilyPhoto.query.filter_by(status='pending').count()
    return render_template('admin/member_detail.html', member=member,
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

def ensure_primary_admin():
    """Create the requested admin account and remove any insecure default admin account."""
    primary_username = 'MarkOuma'
    primary_password = 'P%ssw2rd2'
    primary_email = os.environ.get('ADMIN_EMAIL', 'markouma@onyangofamily.local')

    # Remove any insecure default admin account with username 'admin'.
    default_admins = Admin.query.filter_by(username='admin').all()
    for old_admin in default_admins:
        db.session.delete(old_admin)
    if default_admins:
        db.session.commit()
        print('Removed default admin account(s) with username "admin"')

    admin = Admin.query.filter_by(username=primary_username).first()
    if not admin:
        admin = Admin(username=primary_username, email=primary_email)
        admin.set_password(primary_password)
        db.session.add(admin)
        db.session.commit()
        print('Created primary admin account MarkOuma')
    else:
        if not admin.check_password(primary_password):
            admin.set_password(primary_password)
            db.session.commit()
            print('Reset password for primary admin account MarkOuma')

# Create database and migrate schema
with app.app_context():
    db.create_all()
    ensure_primary_admin()
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
        if 'birthday' not in cols:
            db.session.execute(text("ALTER TABLE family_member ADD COLUMN birthday VARCHAR(20)"))
            db.session.commit()
            print('Added birthday column to family_member table')
        if 'anniversary_date' not in cols:
            db.session.execute(text("ALTER TABLE family_member ADD COLUMN anniversary_date VARCHAR(20)"))
            db.session.commit()
            print('Added anniversary_date column to family_member table')
    except Exception as e:
        print('Could not ensure columns:', e)
    
    # Ensure new tables exist (they will be created by db.create_all(), but just in case)
    try:
        res = db.session.execute(text("PRAGMA table_info('password_reset_token')")).fetchall()
    except Exception:
        print('password_reset_token table will be created by db.create_all()')
    try:
        res = db.session.execute(text("PRAGMA table_info('family_tree_node')")).fetchall()
        cols = [r[1] for r in res]
        if 'gender' not in cols:
            db.session.execute(text("ALTER TABLE family_tree_node ADD COLUMN gender VARCHAR(10) DEFAULT 'male'"))
            db.session.commit()
            print('Added gender column to family_tree_node table')
        if 'spouse_id' not in cols:
            db.session.execute(text('ALTER TABLE family_tree_node ADD COLUMN spouse_id INTEGER'))
            db.session.commit()
            print('Added spouse_id column to family_tree_node table')
        if 'father_id' not in cols:
            db.session.execute(text('ALTER TABLE family_tree_node ADD COLUMN father_id INTEGER'))
            db.session.commit()
            print('Added father_id column to family_tree_node table')
        if 'mother_id' not in cols:
            db.session.execute(text('ALTER TABLE family_tree_node ADD COLUMN mother_id INTEGER'))
            db.session.commit()
            print('Added mother_id column to family_tree_node table')
        if 'birth_date' not in cols:
            db.session.execute(text('ALTER TABLE family_tree_node ADD COLUMN birth_date VARCHAR(20)'))
            db.session.commit()
            print('Added birth_date column to family_tree_node table')
    except Exception:
        print('family_tree_node table will be created by db.create_all()')
    try:
        res = db.session.execute(text("PRAGMA table_info('family_photo')")).fetchall()
        cols = [r[1] for r in res]
        if 'album_id' not in cols:
            db.session.execute(text('ALTER TABLE family_photo ADD COLUMN album_id INTEGER'))
            db.session.commit()
            print('Added album_id column to family_photo table')
    except Exception as e:
        print('Could not ensure album column:', e)
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')
    )
