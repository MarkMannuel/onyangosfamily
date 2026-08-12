# Onyango Family Website – Full Project Documentation

## 1. Project Overview

This project is a Flask-based family website designed to serve as a digital home for the Onyango family. It combines public storytelling, member accounts, media sharing, family-tree organization, event management, and an admin moderation system.

The application is built around one central idea: allow family members to preserve heritage, share memories, communicate with each other, and contribute content in a structured and moderated environment.

### Primary goals
- Preserve family history and traditions
- Connect relatives through a shared web platform
- Allow approved members to contribute stories, photos, and videos
- Provide a visible family tree and public family pages
- Give administrators moderation and management power

### Core user types
1. Visitor
   - Can browse public pages without logging in.
2. Family member
   - Can register, log in, upload content, and access member-specific features.
3. Admin
   - Can review submissions, manage members, manage events, and oversee family content.

---

## 2. Technology Stack

The application uses the following core technologies:

- Python 3
- Flask – main web framework
- Flask-SQLAlchemy – ORM and database management
- Flask-Login – user session and authentication management
- Flask-Mail – email support for password reset and notifications
- SQLite – local relational database
- Jinja2 – server-side HTML templating
- Werkzeug – password hashing and file upload handling
- Bootstrap / Font Awesome – styling and UI components

### Dependency versions
The project dependencies are listed in [requirements.txt](requirements.txt).

Key packages include:
- Flask==2.3.3
- Flask-SQLAlchemy==3.1.1
- Flask-Login==0.6.2
- Werkzeug==2.3.7
- python-dotenv==1.0.0

---

## 3. Project Structure

The repository is organized as follows:

- [app.py](app.py) – main Flask application containing routes, models, and app logic
- [requirements.txt](requirements.txt) – Python dependencies
- [templates/](templates) – HTML pages for public, member, and admin areas
- [static/](static) – CSS, JavaScript, images, and uploaded files
- [instance/](instance) – runtime data folder for the SQLite database and app artifacts
- [tests/](tests) – test files for app behavior
- [test_*.py](test_family_tree.py) – additional standalone test files at the project root

### Important folders
- templates/
  - Contains all page templates for the site.
  - Includes public pages, member pages, and admin pages in separate subfolders.
- static/
  - Stores CSS, JavaScript, images, and uploaded media like profile pictures, gallery photos, and videos.
- instance/
  - Stores the database file and generated runtime data.

---

## 4. Application Architecture

The app follows a classic Flask MVC-style structure with:

- Models defined in [app.py](app.py) using Flask-SQLAlchemy
- Routes defined in [app.py](app.py) for each page and action
- Templates in [templates/](templates) for presentation
- Static assets in [static/](static) for styling and file uploads

### Runtime flow
1. The Flask app starts from [app.py](app.py).
2. The database is created or initialized.
3. A default admin account is created if it does not already exist.
4. Incoming HTTP requests are handled by route functions.
5. Data is queried from the SQLite database.
6. The relevant template is rendered and returned to the browser.

### Request lifecycle example
When a user visits the homepage:
- The route `/` queries the database for approved members, approved stories, approved photos, approved videos, upcoming events, announcements, and past media.
- The data is passed into the template.
- The template renders the page with the right content and layout.

---

## 5. Configuration and Initialization

The app is created in [app.py](app.py) with the following main configuration:

- Secret key
- SQLite database URI
- Upload folder location
- Allowed file extensions for photos, videos, audio, and documents
- Mail configuration for email sending

### Important configuration values
- Database: `sqlite:///family_database.db`
- Upload folder: `static/uploads`
- Primary admin login:
  - username: `MarkOuma`
  - password: `P%ssw2rd2`

> The application creates this admin account automatically if it is missing, and removes any insecure default admin account with username `admin`.

### Startup behavior
When the application starts:
- the database is created
- the upload directory is ensured to exist
- the primary admin account is created if missing
- any insecure default admin account with username `admin` is removed
- required database columns are added if they do not exist

The app runs with:
- host: `0.0.0.0`
- port: `5000`
- debug mode: enabled

---

## 6. Data Models

The project uses a relational SQLite database with multiple models. Each model represents a different content or user type.

### 6.1 Admin
Represents system administrators.

Fields:
- id
- username
- password_hash
- email
- created_at

Purpose:
- Authenticated admins can manage content and users.

### 6.2 FamilyMember
Represents a registered family member.

Fields include:
- name
- username
- email
- password_hash
- role
- summary
- relationship
- phone
- birthday
- anniversary_date
- profile_picture
- status
- must_change_password
- submitted_at
- approved_at
- approved_by

Purpose:
- Stores member profiles and account state.
- Members must be approved before they can fully use the site.

### 6.3 PasswordResetToken
Represents password reset attempts.

Fields:
- member_id
- token
- created_at
- expires_at
- used

Purpose:
- Used for secure password reset workflows.

### 6.4 FamilyTreeNode
Represents a node in the family tree.

Fields include:
- name
- relation
- gender
- birth_date
- parent_id
- father_id
- mother_id
- spouse_id
- created_at

Purpose:
- Stores genealogy nodes and family relationships.
- Supports spouse, parent, and child relationships.

### 6.5 FamilyPost
Represents a story or post submitted by a family member.

Fields include:
- title
- body
- author
- category
- image_url
- status
- created_at
- approved_at
- approved_by
- views

Purpose:
- Stores stories that are reviewed before publication.

### 6.6 StoryComment
Represents comments left on a story.

Fields:
- post_id
- name
- body
- created_at

### 6.7 PhotoAlbum
Represents an album for organizing photos.

### 6.8 FamilyPhoto
Represents a photo upload.

Fields include:
- member_id
- album_id
- filename
- caption
- status
- created_at
- approved_at
- approved_by

### 6.9 FamilyVideo
Represents a video upload.

### 6.10 FamilyEvent
Represents a family event.

Fields include:
- title
- description
- event_date
- location
- event_type
- created_at
- created_by
- is_public

### 6.11 Announcement
Represents announcements posted by admins.

### 6.12 MessageThread
Represents private messages sent between members.

### 6.13 MemberPreference
Stores privacy preferences for a member.

### 6.14 EventRSVP
Tracks RSVPs submitted for events.

### 6.15 PastEventMedia
Stores photos or videos from past events for the public gallery.

### 6.16 FamilyTask
Represents a collaborative checklist item for planning and coordination.

### 6.17 ForumCategory, ForumThread, ForumReply
Support a forum-like feature structure for family discussions.

### 6.18 WelfareFund and WelfareContribution
Support fundraising or welfare tracking.

### 6.19 FamilyDocument
Stores shared documents such as certificates or records.

### 6.20 FamilyTimelineEvent
Stores timeline milestones for the heritage section.

### 6.21 FamilyAudio
Stores audio/oral history uploads.

---

## 7. Authentication and Authorization

The app uses Flask-Login and session-based authentication.

### Member authentication
Members log in through `/member/login`.

The workflow:
- the username is normalized to lowercase
- the member is looked up in the database
- the password is checked with Werkzeug hash verification
- approval status is checked
- if the member is approved, a session is created

### Admin authentication
Admins log in through `/admin/login`.

The workflow:
- admin credentials are checked against the database
- a login session is created with Flask-Login
- protected admin routes require login

### Protected routes
Most admin routes require `@login_required`.

### Password reset flow
Members can request a password reset through `/member/forgot-password`.

The app:
- generates a temporary password
- hashes and stores it
- forces the user to change it on next login
- tries to send an email using Flask-Mail
- falls back to showing the generated password in the browser when SMTP is unavailable

---

## 8. Public Website Features

### 8.1 Home page
Route: `/`

The homepage displays:
- approved members
- recent approved stories
- approved photos and videos
- upcoming events
- recent announcements
- past events media highlights

It also includes a hero background slider controlled by `HERO_BACKGROUNDS` in [app.py](app.py).

### 8.2 About page
Route: `/about`

Shows the family story, values, and heritage messaging.

### 8.3 Family tree page
Route: `/family-tree`

Displays the family tree using data from `FamilyTreeNode`.

The logic uses `build_family_tree()` to create a nested structure where:
- each couple is grouped together
- children appear under their parents
- spouses are rendered in a couple unit

### 8.4 Gallery page
Route: `/gallery`

Shows approved photos and videos from the gallery.

### 8.5 Directory page
Route: `/directory`

Lists approved family members in an alphabetical directory.

### 8.6 Members profile page
Route: `/member/<member_id>`

Shows a member’s profile, approved photos, and approved videos.

### 8.7 Events page
Route: `/events`

Displays upcoming family events and allows visitors to RSVP.

### 8.8 Search page
Route: `/search`

Searches across:
- members
- stories
- events
- albums

### 8.9 Albums page
Route: `/albums`

Shows photo albums and allows browsing by album.

### 8.10 Announcements page
Route: `/announcements`

Displays public announcements.

### 8.11 Heritage / FAQ / Support pages
Routes:
- `/heritage`
- `/faq`
- `/support`

These are informational pages.

---

## 9. Member Features

### 9.1 Registration
Route: `/register`

Members fill in:
- name
- username
- email
- password
- confirmation password
- optional profile details

After registration:
- the member account is created with status `pending`
- an admin must approve it before the account becomes active

### 9.2 Login
Route: `/member/login`

Members log in and are redirected to their dashboard after successful approval.

### 9.3 Dashboard
Route: `/member/dashboard`

Shows:
- the member’s profile summary
- approved family members
- approved stories
- the member’s approved photos

### 9.4 Upload profile picture
Route: `/member/<member_id>/edit-profile-picture`

Members can upload a profile image. The file is saved into the upload folder and linked to their profile.

### 9.5 Upload photos/videos
Route: `/member/<member_id>/upload-photo`

Members can upload:
- a photo
- a video
- optionally choose or create an album

Uploads are stored as pending until an admin approves them.

### 9.6 Submit story
Route: `/submit-story`

Members can submit stories for review. The story is stored with status `pending`.

### 9.7 Comment on stories
Route: `/story/<post_id>/comment`

Visitors and members can add comments to a story.

### 9.8 Messages
Route: `/messages`

Members can send messages to approved members.

### 9.9 Privacy preferences
Routes:
- `/privacy`
- `/privacy/update`

Members can set privacy settings and message permissions.

### 9.10 Password management
Routes:
- `/member/forgot-password`
- `/member/reset-password/<token>`
- `/member/force-change-password`

These support password reset and forced password change after reset.

---

## 10. Admin Features

The admin area is one of the most important parts of the project. Admins can manage nearly every aspect of the site.

### 10.1 Admin login
Route: `/admin/login`

Admins authenticate with their username and password.

### 10.2 Admin dashboard
Route: `/admin/dashboard`

Shows:
- pending member approvals
- pending stories
- pending photos
- total member and post counts
- recent announcements
- upcoming events

### 10.3 Manage family members
Routes:
- `/admin/members`
- `/admin/members/<member_id>`
- `/admin/members/<member_id>/approve`
- `/admin/members/<member_id>/reject`
- `/admin/members/<member_id>/reset-password`
- `/admin/members/<member_id>/delete`

Admins can:
- review new member registrations
- approve or reject members
- reset passwords
- delete members

### 10.4 Manage stories/posts
Routes:
- `/admin/posts`
- `/admin/posts/<post_id>/approve`
- `/admin/posts/<post_id>/reject`
- `/admin/posts/<post_id>/delete`

Admins can approve, reject, or delete submitted stories.

### 10.5 Manage photos and videos
Routes:
- `/admin/photos`
- `/admin/photos/<photo_id>/approve`
- `/admin/photos/<photo_id>/reject`
- `/admin/photos/<photo_id>/delete`
- `/admin/videos/<video_id>/approve`
- `/admin/videos/<video_id>/reject`
- `/admin/videos/<video_id>/delete`

Admins review uploaded media and decide whether it should appear publicly.

### 10.6 Manage events
Routes:
- `/admin/events`
- `/admin/events/create`
- `/admin/events/<event_id>/delete`
- `/admin/past-events/upload`
- `/admin/past-events/<event_id>/delete`

Admins can:
- create public family events
- upload past-event photos or videos
- delete events or media

### 10.7 Manage announcements
Routes:
- `/admin/announcements`
- `/admin/announcements/<announcement_id>/delete`

Admins can create and remove site-wide announcements.

### 10.8 Manage family tree
Routes:
- `/admin/family-tree`
- `/admin/family-tree/add`
- `/admin/family-tree/add-couple`
- `/admin/family-tree/<parent_id>/add-child`
- `/admin/family-tree/<node_id>/add-spouse`
- `/admin/family-tree/<node_id>/edit`
- `/admin/family-tree/<node_id>/delete`

Admins can add and edit family tree nodes, couples, children, and spouses.

---

## 11. How Media Uploads Work

The application uses the `static/uploads` directory for all uploaded media.

### Upload handling principles
- Uploaded files are saved to the filesystem using a generated filename.
- The filename is sanitized using `secure_filename()`.
- File types are validated by extension.
- Images, videos, audio, and documents each have their own allowed-extension lists.

### Upload flow
1. A user submits a file through a form.
2. The server checks that the file exists and is allowed.
3. A unique file name is created with timestamp information.
4. The file is saved to the upload directory.
5. A database record is created for the file.
6. The content stays pending until reviewed by an admin.

### Media types supported
- Images: png, jpg, jpeg, gif
- Videos: mp4, webm, ogg, avi, mov, mkv
- Audio: mp3, wav, ogg, m4a, aac, flac
- Documents: pdf, doc, docx, txt, xls, xlsx, ppt, pptx, odt, rtf

---

## 12. How the Family Tree Works

The family tree is more than a flat list of names. It is built into a nested structure for display.

### Data model approach
Each `FamilyTreeNode` can have:
- a parent
- a father
- a mother
- a spouse
- children via relationship fields

### Rendering approach
The function `build_family_tree()` walks the tree and groups nodes into a nested structure shaped like:
- a couple unit
- the couple’s children as nested child couples

### Relationship logic
- `spouse_id` links two nodes as partners
- `father_id` and `mother_id` help link children to specific parents
- `parent_id` is used as a fallback relationship field

This makes the family tree presentation more meaningful than a simple list.

---

## 13. How the Homepage Slider Works

The homepage hero section uses a rotating background slider.

### Implementation details
- The slider configuration is stored in `HERO_BACKGROUNDS` inside [app.py](app.py).
- A Flask context processor makes this data available to templates.
- The template uses the data to render the hero slider.

### What it does
- Displays a series of full-screen background images
- Shows a title, description, text badge, and icon for each slide
- Rotates through the configured slides automatically

---

## 14. Template Structure

The project uses Jinja2 templates under [templates/](templates).

### Public templates
- `index.html` – homepage
- `about.html` – about page
- `family_tree.html` – family tree page
- `gallery.html` – gallery page
- `directory.html` – member directory
- `events.html` – events page
- `stories.html` – story feed
- `story_detail.html` – story detail page
- `submit_story.html` – submission form
- `announcements.html` – announcements page
- `register.html` – member registration
- `member_login.html` – member login
- `search_results.html` – search output page

### Member templates
- `member_dashboard.html`
- `member_profile.html`
- `upload_photo.html`
- `member/forgot_password.html`
- `member/reset_password.html`
- `member/force_change_password.html`

### Admin templates
- `admin/dashboard.html`
- `admin/login.html`
- `admin/members.html`
- `admin/member_detail.html`
- `admin/posts.html`
- `admin/photos.html`
- `admin/events.html`
- `admin/family_tree.html`
- `admin/reset_password.html`

---

## 15. How the Site Supports Content Moderation

One of the main strengths of the app is its moderation workflow.

### Content approval workflow
- Members submit content.
- Content is inserted into the database with status `pending`.
- Admins review the content in the admin panel.
- Admins approve, reject, or delete it.

### Status values used
- `pending` – waiting for review
- `approved` – visible to the public
- `rejected` – not accepted

### Why this matters
This protects the site from inappropriate or incomplete submissions and keeps the family website polished and meaningful.

---

## 16. How the Database Is Initialized

The database initialization happens in the bottom of [app.py](app.py) inside an application context.

The process:
1. `db.create_all()` creates tables for all models.
2. `create_admin()` creates the default admin if missing.
3. Extra schema checks are performed to add new columns if the database was created earlier.

This helps the app remain backward-compatible as the schema evolves.

---

## 17. Running the Project Locally

### Prerequisites
- Python 3.x
- pip

### Install dependencies
```bash
pip install -r requirements.txt
```

### Start the app
```bash
python app.py
```

### Open in browser
```text
http://localhost:5000
```

---

## 18. Common Operational Notes

### Default credentials
The app includes a default admin account on first launch:
- username: `admin`
- password: `admin123`

### Email configuration
The app uses Flask-Mail, but email sending may fail in a local or demo environment.

If SMTP is unavailable:
- the app falls back to printing the reset password in the terminal
- the password may instead be shown in the browser flash message

### Upload directory
The app expects the upload folder to exist. It creates it automatically on startup.

### Production concerns
Before deploying to production, the following should be changed:
- `SECRET_KEY`
- admin credentials
- mail credentials
- database setup
- file permissions and hosting configuration

---

## 19. Testing and Verification

The repository includes several test files such as:
- [test_family_tree.py](test_family_tree.py)
- [test_home.py](test_home.py)
- [test_final_verify.py](test_final_verify.py)
- [test_tree_fixes.py](test_tree_fixes.py)
- [tests/test_app_features.py](tests/test_app_features.py)

These tests focus on the application’s core behaviors, including family-tree logic, home page behavior, and feature flows.

---

## 20. Summary of How the Project Works

In short, this project works as a full-stack Flask web application that:
- serves public pages for visitors
- allows members to register and login
- supports member-generated content with moderation
- stores content in an SQLite database
- saves uploaded media to the server filesystem
- provides admin tools for managing people, stories, media, events, and family-tree content

It is essentially a combination of:
- a family website
- a content moderation system
- a member portal
- an admin control panel
- a media gallery and family archive

---

## 21. Recommended Next Improvements

The project already provides a solid foundation, but it could be improved with:
- stronger security practices
- better deployment configuration
- a proper production database
- a real email service setup
- API endpoints
- improved access controls and audit logging
- richer family-tree visualization

---

## 22. Final Takeaway

The Onyango Family Website is a Flask application that brings family storytelling, heritage preservation, member interaction, and moderation together in one platform. Its architecture is straightforward but flexible: the main logic lives in [app.py](app.py), the user experience is provided by templates, and the data is stored in a SQLite database with multiple interconnected models.

This makes it easy to understand, modify, and extend as the family’s digital needs grow.
