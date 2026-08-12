# Background Images Folder

This folder is for the pictures you want to be displayed as **background images**
on the website.

## Placeholder
There is a `placeholder.txt` file in this folder so the images directory exists
in the project. **Delete it before adding your real images.**

## How to use
1. Delete `placeholder.txt`.
2. Drop your image file(s) here, e.g. `background_1.jpg`.
3. Reference them in your CSS using the `/images/` path:
   ```css
   background-image: url('/images/background_1.jpg');
   ```
   Or in an inline style:
   ```html
   <div style="background-image: url('/images/background_1.jpg')">...</div>
   ```

The Flask server already serves this folder at `/images/<filename>`, so any
image you place here is immediately available to the website.

Supported formats: JPG, PNG, WebP, GIF.

