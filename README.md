# Onyango Family Website Documentation

## Overview
This project is a Flask-based family website for the Onyango family. Its purpose is to preserve family heritage, connect relatives, and let approved members contribute stories, photos, and other memories to a shared online community.

## What the website is about
The website acts as a digital family hub where:
- family members can introduce themselves and build public profiles
- relatives can share stories and memories
- photos and videos can be uploaded for the family to enjoy
- the family tree can be visualized and managed
- an admin can review and approve content before it becomes visible

## Main goals
1. Preserve family history and traditions
2. Create a welcoming online space for family connection
3. Encourage storytelling across generations
4. Allow members to contribute content safely and respectfully
5. Give admins moderation and management control

## Main features

### Public website experience
Visitors can browse:
- the home page
- an about page describing the family values and history
- the family tree page
- the stories page
- the gallery page

These pages are designed to present the family as a close-knit, heritage-centered community.

### Member features
Registered family members can:
- create accounts and log in
- view a personal dashboard
- update their profile information
- upload a profile photo
- upload photos and videos
- organize uploads into albums
- submit stories for review
- comment on family stories
- view their own contributions
- share birthdays on their profile

Members are not automatically visible to the public. Their accounts must be approved by an admin first.

### Admin features
Administrators can:
- log in to the admin panel
- manage family members
- approve or reject member registrations
- approve or reject stories, photos, and videos
- manage the family tree
- reset member passwords
- create and manage family events

## User roles

### 1. Visitor
A person who browses the public pages without logging in.

### 2. Family Member
A registered family member who can contribute content and access member-only pages.

### 3. Admin
The site administrator who moderates activity and manages the family platform.

## Key pages and routes
- / — Home page
- /about — About the family
- /family-tree — Family tree view
- /gallery — Gallery of approved photos and videos
- /stories — Public stories feed
- /submit-story — Story submission form
- /register — Member registration
- /member/login — Member login
- /member/dashboard — Member dashboard
- /member/<id> — Member profile page
- /admin/login — Admin login
- /admin/dashboard — Admin dashboard

## Core data models
The app stores information in a SQLite database using Flask-SQLAlchemy. The main entities are:
- Admin — site administrator account
- FamilyMember — registered family member profile
- FamilyPost — stories/posts submitted by members
- FamilyPhoto — photo uploads
- FamilyVideo — video uploads
- FamilyTreeNode — nodes in the family tree

## Technology stack
The website is built with:
- Flask — web framework
- Flask-SQLAlchemy — database ORM
- Flask-Login — user session management
- Flask-Mail — email notifications
- SQLite — local database
- Bootstrap and Font Awesome — frontend styling and icons

## Project structure
- app.py — main Flask application with routes, models, and logic
- templates/ — HTML templates for every page
- static/ — CSS, JavaScript, and uploaded media
- instance/ — app data folder
- requirements.txt — Python dependencies

## How to run the project
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the application:
   ```bash
   python app.py
   ```
3. Open the site in your browser at:
   ```text
   http://localhost:5000
   ```

## Homepage "Live" Background Slider (7 Pictures)

The homepage hero is a full-screen, auto-rotating background slider that slowly
zooms/pans each photo (Ken Burns effect) so the site always feels alive.

### How to add your own 7 pictures

1. Drop your 7 photos into **`static/images/`** (e.g. `family_banner.jpg`,
   `family_banner2.jpg`, … `family_banner7.jpg`). JPG / PNG / WebP all work.
2. In **`app.py`**, set:
   ```python
   USE_LOCAL_HERO_IMAGES = True
   ```
3. List your filenames in the `HERO_SLIDES` list (top of `app.py`) — add or
   remove entries freely; the slider auto-adapts (dots + arrows + text).

Until you add photos, the homepage uses 7 free Unsplash family photos so the
site looks polished out of the box. Swap them at any time by following the steps
above. Full instructions are also in `static/images/README.txt`.

## Important notes
- The app creates a primary admin account with the username `MarkOuma` and password `P%ssw2rd2` on startup if it does not already exist.
- Any insecure default admin account with username `admin` is removed automatically.
- Email sending is configured but may fail in a local/demo environment; in that case the app may fall back to showing the generated password in the browser.
- For production use, the secret key, admin credentials, and mail settings should be changed.

## Future enhancement roadmap
The current version provides a strong foundation for a family heritage platform. The following features can be added to make it more engaging, scalable, and comprehensive.

### 1. Event management
- Add a family events calendar for reunions, birthdays, anniversaries, and gatherings
- Allow members to RSVP to events
- Send reminders for upcoming events
- Attach event-specific photo albums

### 2. Communication tools
- Add a family forum or discussion board
- Support private messaging between family members
- Publish announcements from admins to all members
- Add comments on stories, photos, and posts

### 3. Enhanced family tree features
- Build an interactive, zoomable family tree view
- Add relationship types such as biological, adoptive, marriage, and guardian
- Store details such as birth and death dates, locations, and occupations
- Attach photos to family tree nodes
- Add search by name, location, or date

### 4. Privacy and access control
- Let members control who can see their profile and content
- Introduce visibility levels such as public, family-only, and admin-only
- Add data export for personal contributions
- Provide self-service account deletion with confirmation

### 5. Media enhancements
- Organize photos into albums and collections
- Add slideshow support for galleries
- Improve video experience with streaming and enhanced playback
- Support audio memory uploads
- Allow document uploads such as letters, certificates, and family records

### 6. Collaborative features
- Let multiple members contribute to a single story
- Add version history for stories and posts
- Support mentions and tagging of other family members
- Add like and reaction systems for stories and photos

### 7. Mobile and accessibility
- Improve full mobile responsiveness
- Add a Progressive Web App or mobile-friendly experience
- Support screen reader accessibility and keyboard navigation
- Include high-contrast mode and adjustable font size

### 8. Advanced admin tools
- Add analytics for site usage and member activity
- Support bulk approval and rejection of content
- Improve content moderation with priority queues
- Track admin actions through an audit log
- Add automated backup and restore functionality

### 9. Search and discovery
- Add a global search across members, stories, photos, and family tree data
- Provide advanced filters by date, category, author, and content type
- Introduce tags for better organization and discovery

### 10. Legacy and memorial features
- Add a digital time capsule for future content release
- Create memorial pages for deceased relatives
- Build a family timeline for major historical milestones
- Add birthday and anniversary notifications

### 11. Member engagement
- Introduce gamification such as badges and contribution milestones
- Highlight active members through a member-of-the-month feature
- Recommend content based on user interests
- Send weekly or daily digests of new family activity

### 12. Technical improvements
- Add RESTful API endpoints for future integrations
- Support sharing content to social media platforms
- Provide RSS feeds for family updates
- Add multi-language support
- Improve performance with caching and CDN integration

### 13. Security enhancements
- Add optional two-factor authentication for sensitive accounts
- Enforce stronger password policies
- Introduce rate limiting to reduce abuse and brute-force attacks
- Improve session management with visible active sessions and remote logout

### 14. Family directory
- Create a digital address book with privacy controls
- Map family relationship connections more clearly
- Add a skills and profession directory
- Include emergency contact information where appropriate

### 15. Documentation and help
- Add an interactive user guide
- Create a FAQ section for common questions
- Provide video tutorials for major features
- Add a support contact form for reporting issues

### 16. Database enhancements
- Introduce automated cloud backups
- Archive older content to reduce database size
- Add migration tools that support smooth schema updates

### 17. Monitoring and maintenance
- Add comprehensive error logging and alerts
- Track performance metrics and response times
- Schedule automated maintenance tasks such as cleanup and notifications

### 18. Content scheduling
- Support scheduled posts and content publishing
- Add a draft system for unfinished submissions
- Introduce multi-step approval workflows for sensitive content

### Suggested implementation priority
High priority:
1. Comment system on stories
2. Event calendar with RSVP support
3. Advanced search functionality
4. Photo album organization
5. Birthday and anniversary notifications

Medium priority:
6. Private messaging
7. Interactive family tree
8. Content scheduling
9. Privacy settings
10. Mobile app or Progressive Web App

Low priority:
11. Gamification
12. API development
13. Multi-language support
14. Social media integration
15. Digital time capsule

## Short summary
This website is a modern family heritage platform that brings the Onyango family together online. It combines storytelling, profile sharing, media uploads, family tree management, and moderation tools into one connected experience.