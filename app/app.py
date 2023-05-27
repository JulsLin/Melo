from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from models import User, Artist, Album, Listener, Song, Playlist, PlaylistSong, Event, UserEvent, Notification
from forms import RegistrationForm, EventForm
from datetime import datetime
from database import db
from werkzeug.utils import secure_filename
from biography_form import BiographyForm
import os
import mutagen
from AlbumForm import AlbumForm
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'users.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/audio')
ALLOWED_EXTENSIONS = {'mp3', 'jpeg'}    # only mp3 files accepted

STATIC_FOLDER = os.path.join(BASE_DIR,'static')
app.config['STATIC_FOLDER'] = STATIC_FOLDER

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db.init_app(app) 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Register a new user (listener or artist) in the system.
    """
    form = RegistrationForm()
    if form.validate_on_submit():

        existing_user = User.query.filter_by(username=form.username.data).first()

        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return render_template('register.html', form=form)

        user_name = form.username.data
        email = form.email.data
        password = form.password.data
        hashed_password = generate_password_hash(password, method='sha256')
        user_type = form.user_type.data
        date_join = datetime.utcnow()

        if user_type == 'listener':
            listener = Listener(username=user_name, password=hashed_password, user_type=user_type, user_email=email, date_join=date_join, first_name=form.first_name.data, last_name=form.last_name.data, followed_ids='')
            db.session.add(listener)
            db.session.commit()
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))

        else:
            artist_stagename = form.artist_stagename.data
            artist_city = form.artist_city.data
            artist_tags = form.artist_tags.data
            artist = Artist(username=user_name, password=hashed_password, user_type=user_type, user_email=email, date_join=date_join, first_name=form.first_name.data, last_name=form.last_name.data, artist_stagename=artist_stagename, artist_city=artist_city, artist_tags=artist_tags, artist_biography=None, followed_ids='')
            db.session.add(artist)
            db.session.commit()
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Log in a user.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = request.form.get('remember')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
          
            return redirect(url_for('dashboard'))
        else:
            flash('Unable to log in. Please check your credentials and try again.', 'danger')
    return render_template('login.html'), 200


def allowed_file(filename):
    """
    Check if the filename has an allowed file extension.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """
    Upload audio files and create new albums and songs.
    """
    form = AlbumForm()
    if request.method == 'POST':
        files = request.files.getlist('file')
        cover_art_file = request.files['cover'] 
        if not files:
            flash('No files part')
            return redirect(request.url)

        album_release_date = form.album_release_date.data
        artist_id = current_user.id
        album = form.album_title.data.strip()
        existing_album = Album.query.filter_by(album_title=album, artist_id=artist_id).first()
        if not existing_album:
            if not form.album_release_date.data:
                flash('New albums require a release dates!')
                return redirect(request.url)
            if form.validate_on_submit():
                new_album = Album(
                    album_title=album,
                    album_release_date=album_release_date,
                    artist_id=artist_id
                )
                artist = Artist.query.get(artist_id)
                artist.albums.append(new_album)
                db.session.add(new_album)
        else:
            new_album = existing_album
        album = album.strip().replace(' ', '_').lower()

        for file in files:
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(artist_id), album, filename.lower())
                if os.path.exists(file_path):
                    flash('Song already added in the album!')
                    return redirect(request.url)
                os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], str(artist_id), album), exist_ok=True)
                file.save(file_path)
                audio = mutagen.File(file_path)    
                length = int(audio.info.length)
                new_song = Song(song_title=os.path.splitext(filename)[0], file_path=file_path, length=length)
                new_album.songs.append(new_song)
                db.session.add(new_song)
        
        if cover_art_file and allowed_file(cover_art_file.filename):
            cover_art_filename = secure_filename(cover_art_file.filename)
            cover_art_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(artist_id), album, 'album_cover')
            os.makedirs(cover_art_folder, exist_ok=True)
            cover_art_path = os.path.join(cover_art_folder, cover_art_filename.lower())
            cover_art_file.save(cover_art_path)
            new_album.cover_art = os.path.relpath(cover_art_path, app.config['UPLOAD_FOLDER'])
            new_album.cover_name = cover_art_file.filename
        elif not cover_art_file and not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], str(artist_id), album, 'album_cover')):
            new_album.cover_art = os.path.join('album_placehoder', 'music-placeholder.jpeg')
        else:
            flash('Invalid cover art file format')
            return redirect(request.url)

        db.session.commit()
        flash('Files uploaded successfully')
        return redirect(url_for('upload_file'))
    notifications = get_notifications()
    return render_template('upload.html', form=form, notifications=notifications)


@app.route('/songs')
def songs():
    """
    Display all albums and songs.
    """
    all_albums = Album.query.all()
    notifications = get_notifications()
    return render_template('songs.html', albums=all_albums, notifications=notifications)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """
    Log out the user.
    """
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))


def get_notifications():
    """
    Get the notifications for the current user.
    """
    return Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()


@app.route('/dashboard')
@login_required
def dashboard():
    """
    Display the dashboard for the logged-in user.
    """
    user_id = current_user.id
    playlists = Playlist.query.filter_by(listener_id=user_id).all()
    if current_user.user_type == 'artist':
        artist_id = current_user.id 
        albums = Album.query.filter_by(artist_id=artist_id).all()
    else:
        albums = []
    notifications = get_notifications()
    return render_template('dashboard.html', playlists=playlists, albums=albums, notifications=notifications)


@app.route('/')
def homepage():
    """
    Display the homepage.
    """
    return render_template('homepage.html')


@app.route('/search', methods=['POST'])
def search():
    """
    Perform a search for artists based on the search query.
    """
    search_query = request.form['search_query']
    artists = Artist.query.filter((Artist.artist_stagename.ilike(f'%{search_query}%')) | (Artist.artist_tags.ilike(f'%{search_query}%'))).all()
    notifications = get_notifications()
    return render_template('search_results.html', artists=artists, notifications=notifications)


@app.route('/artist/<int:artist_id>', methods=['GET'])
def artist_page(artist_id):
    """
    Display the artist page for the given artist ID.
    """
    artist = Artist.query.get_or_404(artist_id)
    albums = Album.query.filter_by(artist_id=artist_id).all()
    playlists = Playlist.query.filter_by(listener_id=current_user.id).all() if current_user.is_authenticated else []
    notifications = get_notifications()
    return render_template('artist_page.html', artist=artist, albums=albums, playlists=playlists, notifications=notifications)


@app.route('/favorite_artists')
@login_required
def favorite_artists():
    """
    Display the favorite artists for the current user.
    """
    artist_ids = current_user.followed_ids.split(',')
    artists = Artist.query.filter(Artist.id.in_(artist_ids)).all()
    notifications = get_notifications()
    return render_template('favorite_artists.html', artists=artists, notifications=notifications)


@app.route('/artist/<int:artist_id>/biography', methods=['GET', 'POST'])
@login_required
def artist_biography(artist_id):
    """
    Display and update the biography for the given artist ID.
    """
    artist = Artist.query.get_or_404(artist_id)
    form = BiographyForm()
    if form.validate_on_submit():
        if 'delete' in request.form:
            
            artist.artist_biography = ''
        else:
            artist.artist_biography = form.biography.data

        db.session.commit()
        flash('Biography updated successfully.', 'success')
        return redirect(url_for('artist_page', artist_id=artist_id))
    elif artist.artist_biography:
        form.biography.data = artist.artist_biography
    notifications = get_notifications()
    return render_template('artist_biography.html', artist=artist, form=form, notifications=notifications)


@app.route('/follow/<int:artist_id>', methods=['POST'])
@login_required
def follow_artist(artist_id):
    """
    Follow an artist.
    """
    artist = Artist.query.get(artist_id)
    if artist is None:
        flash('Artist not found.')
        return redirect(url_for('homepage'))

    if current_user.is_following(artist):
        flash('You are already following this artist.')
        return redirect(url_for('artist_page', artist_id=artist_id))
    current_user.followed_ids += f',{artist_id}'
    db.session.commit()
    flash(f'You are now following {artist.artist_stagename}!')
    return redirect(url_for('artist_page', artist_id=artist_id))


@app.route('/unfollow/<int:artist_id>', methods=['POST'])
@login_required
def unfollow_artist(artist_id):
    """
    unfollow an artist.
    """
    artist = Artist.query.get(artist_id)
    if artist is None:
        flash('Artist not found.')
        return redirect(url_for('homepage'))
 
    if not current_user.is_following(artist):
        flash('You are not following this artist.')
        return redirect(url_for('artist_page', artist_id=artist_id))
    followed_ids = current_user.followed_ids.split(',')
    followed_ids.remove(str(artist_id))
    current_user.followed_ids = ','.join(followed_ids)
    db.session.commit()
    flash(f'You have unfollowed {artist.artist_stagename}.')
    return redirect(url_for('artist_page', artist_id=artist_id))


@app.route('/delete_song/<int:song_id>', methods=['POST'])
@login_required
def delete_song(song_id):
    """
    Delete a song.
    """
    song = Song.query.get(song_id)
    if song is None:
        flash('Song not found.')
        return redirect(url_for('songs'))
    album = song.album

    if current_user.user_type == 'artist' and song.album.artist_id == current_user.user_id:
        
        os.remove(song.file_path)
        artist_id = album.artist_id

        db.session.delete(song)
        db.session.commit()
        flash(f'Song {song.song_title} has been deleted.')
        if len(album.songs) == 0:
            db.session.delete(album)
            db.session.commit()
            flash(f'Album {album.album_title} has been deleted.')
    else:
        flash('You do not have permission to delete this song.')

    return redirect(url_for('artist_page', artist_id=artist_id))


@app.route('/delete_album_song/<int:song_id>', methods=['POST'])
@login_required
def delete_album_song(song_id):
    """
    Delete a song from an album.
    """
    song = Song.query.get(song_id)
    if song is None:
        flash('Song not found.')
        return redirect(url_for('songs'))
    album = song.album

    if current_user.user_type == 'artist' and song.album.artist_id == current_user.user_id:
        os.remove(song.file_path)
        artist_id = album.artist_id

        db.session.delete(song)
        db.session.commit()
        flash(f'Song {song.song_title} has been deleted.')
        if len(album.songs) == 0:
            db.session.delete(album)
            db.session.commit()
            flash(f'Album {album.album_title} has been deleted.')
            return redirect(url_for('dashboard'))  
    else:
        flash('You do not have permission to delete this song.')

    return redirect(url_for('album_songs', album_id=song.album_id))


@app.route('/get_playlists')
@login_required
def get_playlists():
    """
    Get the playlists for the current user.
    """
    playlists = Playlist.query.filter_by(listener_id=current_user.id).all()
    return jsonify({'playlists': [{'id': p.playlist_id, 'title': p.playlist_title} for p in playlists]})


@app.route("/add_to_playlist", methods=["POST"])
@login_required
def add_to_playlist():
    """
    Add a song to a playlist.
    """
    song_id = request.form.get("song_id")
    playlist_id = request.form.get("playlist_id")
    new_playlist_name = request.form.get("new_playlist_name")

    if playlist_id == "create":
        if not new_playlist_name:
            flash('Playlist name cannot be empty.', 'danger')
            return redirect(request.referrer)

        new_playlist = Playlist(playlist_title=new_playlist_name, playlist_creation_date=datetime.now(), listener_id=current_user.id)
        db.session.add(new_playlist)
        db.session.commit()
        playlist_id = new_playlist.playlist_id

    existing_entry = PlaylistSong.query.filter_by(playlist_id=playlist_id, song_id=song_id).first()
    if existing_entry:
        flash('The song is already in the playlist.', 'danger')
    else:
        new_entry = PlaylistSong(playlist_id=playlist_id, song_id=song_id)
        db.session.add(new_entry)
        db.session.commit()
        flash('Song added to the playlist.', 'success')

    return redirect(request.referrer)


@app.route('/my_playlists')
@login_required
def my_playlists():
    """
    Display the playlists for the current user.
    """
    playlists = Playlist.query.filter_by(listener_id=current_user.id).all()
    for playlist in playlists:
        playlist.songs = [ps.song for ps in playlist.playlist_songs]
    notifications = get_notifications()
    return render_template('my_playlists.html', playlists=playlists, notifications=notifications)


@app.route('/delete_song_from_playlist', methods=['POST'])
@login_required
def delete_song_from_playlist():
    """
    Delete a song from a playlist.
    """
    song_id = request.form.get("song_id")
    playlist_id = request.form.get("playlist_id")

    entry = PlaylistSong.query.filter_by(playlist_id=playlist_id, song_id=song_id).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
        flash('Song removed from the playlist.', 'success')
    else:
        flash('Song not found in the playlist.', 'danger')

    return redirect(request.referrer or url_for('my_playlists'))


@app.route('/album/<int:album_id>/songs', methods=['GET'])
def album_songs(album_id):
    """
    Display the songs for the given album ID.
    """
    album = Album.query.get_or_404(album_id)
    notifications = get_notifications()
    artist = album.artist
    return render_template('album_songs.html', album=album,artist=artist, notifications=notifications)


def get_followers(artist):
    """
    Get the followers of an artist.
    """
    all_listeners = User.query.all()
    followers = [listener for listener in all_listeners if listener.is_following(artist)]
    return followers


@app.route('/create-event', methods=['GET', 'POST'])
def create_event():
    """
    Create a new event.
    """
    form = EventForm()
    if request.method == 'POST':
        if current_user.type != 'artist':
            flash('Only artists can create events!')
            return redirect(request.url)
        event_title = form.event_title.data
        event_date = form.event_date.data
        event_venue = form.event_venue.data
        event_artist = current_user.id
        description = form.description.data
        new_event = Event(
            event_title=event_title,
            artist_id=event_artist,
            event_date=event_date,
            event_venue=event_venue,
            description=description
        )
        artist = Artist.query.get(event_artist)
        artist.events.append(new_event)
        db.session.add(new_event)
        db.session.commit()
        id = new_event.event_id
        message = f"{artist.artist_stagename} has created a new event: {event_title} on {event_date}"
        for follower in get_followers(artist):
            notification = Notification(user_id=follower.id, content=message, event_id=id, event=new_event)
            db.session.add(notification)
        db.session.commit()
        flash(f'Event {event_title} created successfully!')
        return redirect(request.url)
    notifications = get_notifications()
    return render_template('create_event.html', form=form, notifications=notifications)

@app.route('/view-events/<int:artist_id>', methods=['GET'])
def view_events(artist_id):
    """
    View the events for the given artist ID.
    """
    events = Event.query.filter_by(artist_id=artist_id).order_by(Event.event_date).all()
    artist = Artist.query.get_or_404(artist_id)
    notifications = get_notifications()
    return render_template('view_events.html', artist_name=artist.artist_stagename, events=events, notifications=notifications)


@app.route('/view-event/<int:event_id>', methods=['GET'])
def view_event(event_id):
    """
    View the details of a specific event.
    """
    artist_id = request.args.get('artist_id', None)
    if artist_id is None:
        abort(404)

    event = Event.query.get_or_404(event_id)
    artist = Artist.query.get_or_404(artist_id)
    notifications = get_notifications()
    return render_template('view_event.html', event=event, artist=artist, notifications=notifications)


@app.route('/rsvp/<int:event_id>', methods=['POST'])
def rsvp(event_id):
    """
    RSVP to an event.
    """
    event = Event.query.get_or_404(event_id)
    user_id = current_user.id
    user_event = UserEvent.query.filter_by(user_id=user_id, event_id=event_id).first()
    if not user_event:
        user_event = UserEvent(user_id=user_id, event_id=event_id)
        db.session.add(user_event)
        db.session.commit()
        flash(f'Successfully RSVPed to {event.event_title}.')
    else:
        flash(f'You have already RSVPed to {event.event_title}.')
    return redirect(request.referrer or url_for('view_events', artist_id=event.artist_id))

 

@app.route('/my-rsvp-events', methods=['GET'])
def my_rsvp_events():
    """
    Display the RSVPed events for the current user.
    """
    user_id = current_user.id
    user_events = UserEvent.query.filter_by(user_id=user_id).all()
    event_ids = [ue.event_id for ue in user_events]
    events = Event.query.filter(Event.event_id.in_(event_ids)).order_by(Event.event_date).all()
    notifications = get_notifications()
    return render_template('my_rsvp_events.html', events=events, notifications=notifications)


@app.route('/read-notification/<int:notification_id>', methods=['GET'])
@login_required
def read_notification(notification_id):
    """
    Mark a notification as read.
    """
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        abort(403)
    notification.read = True
    db.session.commit()

    return redirect(url_for('view_event', event_id=notification.event_id, artist_id=notification.event.artist_id))


def remove_expired_notifications():
    """
    Remove expired notifications from the database.
    """
    with app.app_context():
        now = datetime.utcnow()
        expired_notifications = Notification.query.filter(Notification.expiry_date < now).all()
        for notification in expired_notifications:
            db.session.delete(notification)
        db.session.commit()


def start_scheduler():
    """
    Start the background scheduler for removing expired notifications.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(remove_expired_notifications, 'interval', hours=6)
    scheduler.start()


if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True, port=5001)
