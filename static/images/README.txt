HOW TO USE YOUR OWN HOMEPAGE BACKGROUND IMAGES
================================================

The homepage has a rotating "live" background slider (crossfade + Ken Burns
zoom effect) that is currently using 7 images from the existing static/uploads
folder (member/photo images already in the project).

To use your OWN 7 pictures:

1. Drop your images into THIS folder:  static/images/
   (e.g.  family_1.jpg, family_2.jpg, family_3.jpg, ... family_7.jpg)

2. Open  app.py  and find the  HERO_BACKGROUNDS  list near the top.

3. For each slide, change the "image" value to your local file, for example:

       {'image': 'images/family_1.jpg', 'title': '...', ...}

   The path is relative to the static/ folder, so use  images/<your-file>.

4. You can also use a full web URL (e.g. an Unsplash link) for any slide —
   the slider automatically handles both local static paths and full URLs.

5. Save app.py and restart the Flask server.

Recommended image size: 1920 x 1080 (or wider) for a crisp full-screen look.
