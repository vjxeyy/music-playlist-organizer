-- ---------------------------------------------------
-- Project: Music / Playlist Organiser
-- Database: music_db
-- ---------------------------------------------------
-- Running this script RESETS music_db: any existing data in it is deleted
-- and replaced with the sample songs and playlists below.

-- Create Database
DROP DATABASE IF EXISTS music_db;
CREATE DATABASE music_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE music_db;

-- ---------------------------------------------------
-- Table 1: Songs (Stores song details)
-- ---------------------------------------------------
CREATE TABLE Songs (
    song_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    artist VARCHAR(100) NOT NULL,
    album VARCHAR(100),
    genre VARCHAR(50),
    duration VARCHAR(10)              -- stored as 'm:ss', e.g. '3:20'
);

-- ---------------------------------------------------
-- Table 2: Playlists (Stores playlist names)
-- ---------------------------------------------------
CREATE TABLE Playlists (
    playlist_id INT AUTO_INCREMENT PRIMARY KEY,
    playlist_name VARCHAR(100) NOT NULL UNIQUE
);

-- ---------------------------------------------------
-- Table 3: PlaylistSongs (Links songs to playlists)
-- ---------------------------------------------------
-- The composite primary key stops the same song being added to a playlist twice.
-- ON DELETE CASCADE removes a song's playlist entries when the song is deleted;
-- without it, MySQL refuses to delete any song that is in a playlist.
CREATE TABLE PlaylistSongs (
    playlist_id INT,
    song_id INT,
    PRIMARY KEY (playlist_id, song_id),
    FOREIGN KEY (playlist_id) REFERENCES Playlists(playlist_id) ON DELETE CASCADE,
    FOREIGN KEY (song_id) REFERENCES Songs(song_id) ON DELETE CASCADE
);

-- ---------------------------------------------------
-- Insert Sample Songs (30 entries)
-- ---------------------------------------------------
INSERT INTO Songs (title, artist, album, genre, duration) VALUES
('Blinding Lights', 'The Weeknd', 'After Hours', 'Pop', '3:20'),
('Save Your Tears', 'The Weeknd', 'After Hours', 'Pop', '3:36'),
('Starboy', 'The Weeknd', 'Starboy', 'Pop', '3:50'),
('Paradise', 'Coldplay', 'Mylo Xyloto', 'Rock', '4:12'),
('Hymn for the Weekend', 'Coldplay', 'A Head Full of Dreams', 'Pop', '4:18'),
('Viva La Vida', 'Coldplay', 'Viva La Vida', 'Alternative', '4:02'),
('Fix You', 'Coldplay', 'X&Y', 'Rock', '4:55'),
('Shape of You', 'Ed Sheeran', 'Divide', 'Pop', '3:54'),
('Perfect', 'Ed Sheeran', 'Divide', 'Pop', '4:40'),
('Photograph', 'Ed Sheeran', 'X', 'Pop', '4:19'),
('Thinking Out Loud', 'Ed Sheeran', 'X', 'Soul', '4:41'),
('Believer', 'Imagine Dragons', 'Evolve', 'Rock', '3:24'),
('Thunder', 'Imagine Dragons', 'Evolve', 'Rock', '3:07'),
('Radioactive', 'Imagine Dragons', 'Night Visions', 'Alternative', '3:06'),
('Demons', 'Imagine Dragons', 'Night Visions', 'Alternative', '2:57'),
('Counting Stars', 'OneRepublic', 'Native', 'Pop Rock', '4:17'),
('Apologize', 'OneRepublic', 'Dreaming Out Loud', 'Pop', '3:28'),
('Secrets', 'OneRepublic', 'Waking Up', 'Pop', '3:44'),
('Levitating', 'Dua Lipa', 'Future Nostalgia', 'Pop', '3:23'),
('Don’t Start Now', 'Dua Lipa', 'Future Nostalgia', 'Disco', '3:03'),
('New Rules', 'Dua Lipa', 'Dua Lipa', 'Pop', '3:29'),
('Shivers', 'Ed Sheeran', '=', 'Pop', '3:27'),
('Stay', 'Justin Bieber', 'Justice', 'Pop', '2:21'),
('Peaches', 'Justin Bieber', 'Justice', 'R&B', '3:18'),
('Sorry', 'Justin Bieber', 'Purpose', 'Pop', '3:20'),
('Despacito', 'Luis Fonsi', 'Vida', 'Reggaeton', '3:47'),
('Senorita', 'Shawn Mendes', 'Shawn Mendes', 'Pop', '3:11'),
('Stitches', 'Shawn Mendes', 'Handwritten', 'Pop', '3:26'),
('Attention', 'Charlie Puth', 'Voicenotes', 'Pop', '3:28'),
('We Don’t Talk Anymore', 'Charlie Puth', 'Nine Track Mind', 'Pop', '3:37');

-- ---------------------------------------------------
-- Insert Sample Playlists (6 playlists)
-- ---------------------------------------------------
INSERT INTO Playlists (playlist_name) VALUES
('My Favorites'),
('Workout Vibes'),
('Study Chill'),
('Party Hits'),
('Romantic Mood'),
('Road Trip');

-- ---------------------------------------------------
-- Link Songs to Playlists
-- ---------------------------------------------------
INSERT INTO PlaylistSongs (playlist_id, song_id) VALUES
(1, 1), (1, 8), (1, 9), (1, 16), (1, 21),
(2, 4), (2, 12), (2, 13), (2, 19), (2, 25),
(3, 5), (3, 6), (3, 10), (3, 17), (3, 20),
(4, 2), (4, 14), (4, 22), (4, 26), (4, 29),
(5, 7), (5, 11), (5, 15), (5, 23), (5, 27),
(6, 3), (6, 18), (6, 24), (6, 28), (6, 30);
