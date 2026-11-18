# Radi's World

Stories, world history, audiobooks and comics by **Radi the Storyteller**, in one app.
It works on phones and laptops, can be installed like an app, and speaks 8 languages (English is the default).

| Section | What's inside | How you add content |
|---|---|---|
| **Radi Stories** | Your YouTube videos (stories, features, shorts) | Automatic from your channel, or paste a link in Admin |
| **History** | World history from the pyramids to today, by era, region, topic and date | Admin → History entries |
| **Audiobooks** | Books with chapters; listeners resume where they stopped | Admin → Audiobooks (upload MP3 per chapter) |
| **Comics** | Picture books read page by page with the book-flip effect | Admin → Comics (upload page images) |

Every history story can be **read as a book** (with page-flip sounds), **watched** (9:16 or 16:9), **downloaded** as an MP4 for YouTube,
and **listened to** with a female, male or child voice. Your own recordings play first; if none exists for that language,
the phone's built-in AI voice reads it.

---

## 1. Put the code on GitHub (one time)

1. On github.com, create a **new empty repository** named `radis-world` (no README).
2. On your laptop, unzip `radis-world.zip`, open the folder in VS Code, and in the terminal run:

```bash
git remote add origin https://github.com/RadiibrahimNuhu1207/radis-world.git
git branch -M main
git push -u origin main
```

## 2. Host it on PythonAnywhere (new account `radisworld`)

Sign up at pythonanywhere.com with the username **radisworld** (free "Beginner" account).
Your app will be at **https://radisworld.pythonanywhere.com**.

### 2a. Bash console (Consoles → Bash)

Run these one block at a time:

```bash
git clone https://github.com/RadiibrahimNuhu1207/radis-world.git
cd radis-world
mkvirtualenv radi --python=python3.10
pip install -r requirements.txt
cp .env.example .env
nano .env
```

In nano, set `DJANGO_SECRET_KEY` to any long random text and `YOUTUBE_CHANNEL` to your channel link
(e.g. `https://www.youtube.com/@yourhandle`). Save with **Ctrl+O, Enter**, exit with **Ctrl+X**.

```bash
python manage.py vapid_keys
```

It prints a line starting `VAPID_PUBLIC_KEY=`. Open `nano .env` again and paste it over the empty `VAPID_PUBLIC_KEY=` line.

```bash
python manage.py migrate
python manage.py import_history seed/history.json
python manage.py sync_youtube
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Run `createsuperuser` **on its own** — it asks questions (username, email, password).

### 2b. Web tab

1. **Add a new web app → Manual configuration → Python 3.10**.
2. **Virtualenv:** `/home/radisworld/.virtualenvs/radi`
3. **Source code:** `/home/radisworld/radis-world`
4. Click the **WSGI configuration file** link, delete everything, paste this, and save:

```python
import os, sys
path = "/home/radisworld/radis-world"
if path not in sys.path:
    sys.path.insert(0, path)
os.environ["DJANGO_SETTINGS_MODULE"] = "radisworld.settings"
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

5. **Static files** — add two rows:

| URL | Directory |
|---|---|
| `/static/` | `/home/radisworld/radis-world/staticfiles` |
| `/media/` | `/home/radisworld/radis-world/media` |

6. Turn on **Force HTTPS**, then press the green **Reload** button.

### 2c. Daily task (Tasks tab)

Free accounts get one daily task. Set it to run every morning (e.g. 05:00 UTC = 08:00 in Tanzania):

```bash
cd /home/radisworld/radis-world && /home/radisworld/.virtualenvs/radi/bin/python manage.py sync_youtube && /home/radisworld/.virtualenvs/radi/bin/python manage.py send_daily
```

This pulls in your newest YouTube uploads and sends the daily notification.

---

## 3. Adding content (Admin)

Go to **https://radisworld.pythonanywhere.com/admin/** and log in.

- **Videos** — paste any YouTube link (normal, youtu.be or Shorts). The title fills in by itself. Tick *Featured* to show it big on Home.
- **History entries** — write the English title, place and text. Year can be negative for BCE (e.g. `-2560`) with *circa* ticked.
  Day and month are optional; with them, the story appears in "On this day".
  - *Translations* (bottom of the page): add the same story in Kiswahili, French, Arabic, etc.
  - *Narrations*: upload an MP3 for a language and a voice (female / male / child). Your recordings go here; AI voice files (for English or other languages) go here too.
  - *Videos*: upload the 9:16 and 16:9 MP4s plus their poster images. Visitors can download them.
- **Audiobooks** — title, cover, language, then one chapter per MP3.
- **Comics** — title, cover, then one image per page in order.

Set **Status → Published** for anything you want visitors to see. Drafts stay hidden.

## 4. Updating the app later

When you receive an update, on your laptop: put the new files in the folder, then

```bash
git add -A && git commit -m "Update" && git push
```

On PythonAnywhere (Bash console):

```bash
cd ~/radis-world && git pull && workon radi && python manage.py migrate && python manage.py collectstatic --noinput
```

Then press **Reload** on the Web tab.

## 5. Making history videos

`tools/video/` holds the scripts that make the vintage map videos and the calm music
(`pip install -r tools/requirements-video.txt`). Upload the finished MP4s to a history entry in Admin.

## Notes

- **Languages:** the whole interface switches between English, Kiswahili, French, Arabic (right-to-left), Korean, Japanese, Chinese and Spanish.
  History stories show in the chosen language when a translation exists, otherwise in English.
- **Device voices:** the phone's AI voice depends on the phone. Most phones have English, French, Spanish, Arabic, Chinese, Japanese and Korean; Kiswahili is less common, so upload your recordings for Kiswahili.
- **YouTube on the free plan:** if `sync_youtube` is ever blocked by PythonAnywhere's internet whitelist, just paste video links in Admin → Videos.
- **iPhone notifications:** visitors must first add the app to their Home Screen (Share → Add to Home Screen).
