# Family Website - Remaining Tasks

## Task: Hide List View on Family Tree Page
- [x] Wrap the List View block in a `.tree-list-view` container in `templates/family_tree.html`
- [x] Add `.tree-list-view { display: none; }` CSS rule to `static/css/style.css`
- [x] Verify the page renders with only the visual tree diagram visible

## Task: Overall Goals (from approved plan)
1. [x] Remove ALL guest references from the app
   - [x] app.py `home()` fixed (indentation corrected)
   - [x] templates/index.html guest conditional removed
   - [x] templates/member_profile.html 3 guest conditionals removed
   - [x] reset_db.py GuestInvitation import/block removed
   - [x] Verified: no guest refs in app.py, reset_db.py, index.html; no guest URL rules
2. [x] Add "Upcoming Events" section to homepage
   - [x] app.py `home()` queries upcoming_events and passes to template
   - [x] templates/index.html Upcoming Events section added
   - [x] Verified: events_page route exists
3. [x] Add "Family Best Moments" highlights section to homepage
   - [x] app.py `home()` queries past_media (PastEventMedia) and passes to template
   - [x] templates/index.html Family Best Moments section added

## Verification
- [x] app.py parses OK
- [x] App module imports successfully
- [x] No guest-related URL rules
- [x] events_page route exists
- [x] Homepage has both new sections, Photo Lightbox preserved

