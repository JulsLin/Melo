# from app import db
from datetime import datetime, timedelta
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from database import db

"""
User model representing a user in the system.

Attributes:
    id (int): The unique identifier for the user.
    username (str): The username of the user.
    password (str): The password of the user.
    user_type (str): The type of user (e.g., 'listener' or 'artist').
    date_join (datetime.datetime): The date and time when the user joined.
    user_email (str): The email address of the user.
    first_name (str): The first name of the user.
    last_name (str): The last name of the user.
    notifications (RelationshipProperty): Relationship to the user's notifications.
    type (str): The type of user for SQLAlchemy polymorphic identity.
    followed_ids (str): The IDs of the artists that the user is following.

Methods:
    is_following(artist): Checks if the user is following a specific artist.

"""


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    user_type = db.Column(db.String(10), nullable=False)
    date_join = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_email = db.Column(db.String(120), nullable=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    type = db.Column(db.String(50)) 
    followed_ids = db.Column(db.String(1000), default='')

    def is_following(self, artist):
        return str(artist.id) in self.followed_ids.split(',')
  
    ...
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type,
    }

    def is_following(self, artist):
        return str(artist.id) in self.followed_ids.split(',')
  
    ...

    def __repr__(self):
        return f'<User {self.username}>'


"""
Artist model representing an artist in the system.

Attributes:
    user_id (int): The user ID of the artist (foreign key to User model).
    artist_stagename (str): The stage name of the artist.
    artist_city (str): The city where the artist is located.
    artist_tags (str): Tags associated with the artist.
    artist_biography (str): The biography of the artist.
    albums (RelationshipProperty): Relationship to the artist's albums.
    events (RelationshipProperty): Relationship to the artist's events.

Methods:
    is_following(artist): Checks if the user is following a specific artist.
"""


class Artist(User):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    artist_stagename = db.Column(db.String(80), nullable=False)
    artist_city = db.Column(db.String(80), nullable=False)
    artist_tags = db.Column(db.String(80), nullable=False)
    artist_biography = db.Column(db.Text, nullable=True)
    albums = db.relationship('Album', backref='artist', lazy=True)
    events = db.relationship('Event', backref='artist', lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': 'artist',
    }

    def is_following(self, artist):
        return str(artist.id) in self.followed_ids.split(',')
    
    def __repr__(self):
        return f'<Artist {self.artist_stagename}>'
    

"""
Listener model representing a listener in the system.

Attributes:
    user_id (int): The user ID of the listener (foreign key to User model).

"""


class Listener(User):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'listener',
    }
    
    def __repr__(self):
        return f'<Listener {self.first_name} {self.last_name}>'
    

"""
Album model representing an artist album in the system.

Attributes:
    album_id (int): The unique identifier for the album.
    album_title (str): The title of the album.
    album_release_date (datetime.datetime): The release date of the album.
    artist_id (int): The artist ID of the album (foreign key to Artist model).
    songs (RelationshipProperty): Relationship to the album's songs.
    cover_art (str): The path to the cover art image of the album.

Methods:
    __repr__(): Returns a string representation of the album.
"""


class Album(db.Model):
    album_id = db.Column(db.Integer, primary_key=True)
    album_title = db.Column(db.String(80), nullable=False)
    album_release_date = db.Column(db.DateTime, nullable=False)
    
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.user_id'), nullable=False)
   
    songs = db.relationship('Song', backref='album', lazy=True)
    cover_art = db.Column(db.String(255), nullable=True)
    cover_name = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Album {self.album_title}>'


"""
Event model representing an event in the system.

Attributes:
    event_id (int): The unique identifier for the event.
    event_title (str): The title of the event.
    event_date (datetime.datetime): The date of the event.
    event_venue (str): The venue of the event.
    description (str): The description of the event.
    artist_id (int): The artist ID of the event (foreign key to Artist model).
    user_events (RelationshipProperty): Relationship to the user's events.

Methods:
    __repr__(): Returns a string representation of the event.
"""


class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True)
    event_title = db.Column(db.String(80), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    event_venue = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.user_id'))
    user_events = db.relationship('UserEvent', backref='event', lazy=True)

    def __repr__(self):
        return f'<Event {self.event_title}>'


"""
Song model representing a song in the system.

Attributes:
    song_id (int): The unique identifier for the song.
    song_title (str): The title of the song.
    length (int): The length of the song in seconds.
    album_id (int): The album ID of the song (foreign key to Album model).
    listener_songs (RelationshipProperty): Relationship to the listener's songs.
    playlist_songs (RelationshipProperty): Relationship to the playlist's songs.
    file_path (str): The path to the audio file of the song.

Methods:
    __repr__(): Returns a string representation of the song.
"""


class Song(db.Model):
    song_id = db.Column(db.Integer, primary_key=True)
    song_title = db.Column(db.String(80), nullable=False)
    length = db.Column(db.Integer, nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.album_id'))
    listener_songs = db.relationship('ListenerSong', backref='song', lazy=True)
    playlist_songs = db.relationship('PlaylistSong', backref='song', lazy=True)
    file_path = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Song {self.song_title}>'


"""
UserEvent model representing a relationship between a user and an event.

Attributes:
    user_id (int): The user ID (foreign key to User model).
    event_id (int): The event ID (foreign key to Event model).

Methods:
    __repr__(): Returns a string representation of the UserEvent relationship.
"""


class UserEvent(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.event_id'), primary_key=True)

    def __repr__(self):
        return f'<UserEvent user={self.user_id} event={self.event_id}>'


"""
Playlist model representing a playlist in the system.

Attributes:
    playlist_id (int): The unique identifier for the playlist.
    playlist_title (str): The title of the playlist.
    playlist_creation_date (datetime.datetime): The creation date of the playlist.
    listener_id (int): The listener ID of the playlist (foreign key to Listener model).
    playlist_songs (RelationshipProperty): Relationship to the playlist's songs.

Methods:
    __repr__(): Returns a string representation of the playlist.
"""


class Playlist(db.Model):
    playlist_id = db.Column(db.Integer, primary_key=True)
    playlist_title = db.Column(db.String(80), nullable=False)
    playlist_creation_date = db.Column(db.DateTime, nullable=False)

    listener_id = db.Column(db.Integer, db.ForeignKey('listener.user_id'))
    playlist_songs = db.relationship('PlaylistSong', backref='playlist', lazy=True)

    def __repr__(self):
        return f'<Playlist {self.playlist_title}>'


"""
ListenerSong model representing a relationship between a listener and a song.

Attributes:
    song_id (int): The song ID (foreign key to Song model).
    listener_id (int): The listener ID (foreign key to Listener model).

Methods:
    __repr__(): Returns a string representation of the ListenerSong relationship.
"""  


class ListenerSong(db.Model):
    song_id = db.Column(db.Integer, db.ForeignKey('song.song_id'), primary_key=True)
    
    listener_id = db.Column(db.Integer, db.ForeignKey('listener.user_id'), primary_key=True)

    def __repr__(self):
        return f'<ListenerSong listener={self.user_name} song={self.song_id}>'


"""
PlaylistSong model representing a relationship between a playlist and a song.

Attributes:
    song_id (int): The song ID (foreign key to Song model).
    playlist_id (int): The playlist ID (foreign key to Playlist model).

Methods:
    __repr__(): Returns a string representation of the PlaylistSong relationship.
"""


class PlaylistSong(db.Model):
    song_id = db.Column(db.Integer, db.ForeignKey('song.song_id'), primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.playlist_id'), primary_key=True)

    def __repr__(self):
        return f'<PlaylistSong playlist={self.playlist_id} song={self.song_id}>'


"""
Notification model representing a notification in the system.

Attributes:
    id (int): The unique identifier for the notification.
    user_id (int): The user ID of the notification (foreign key to User model).
    content (str): The content of the notification.
    timestamp (datetime.datetime): The timestamp when the notification was created.
    expiry_date (datetime.datetime): The expiry date of the notification.
    read (bool): Indicates whether the notification has been read.
    event_id (int): The event ID of the notification (foreign key to Event model).
    event (RelationshipProperty): Relationship to the event associated with the notification.

Methods:
    __repr__(): Returns a string representation of the notification.
"""   


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow()+timedelta(days=14))
    read = db.Column(db.Boolean, nullable=False, default=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.event_id'), nullable=True)
    event = db.relationship('Event', backref=db.backref('notifications', lazy=True))

    def __repr__(self):
        return f'<Notification {self.content}>'

