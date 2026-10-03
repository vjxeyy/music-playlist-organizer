-- ---------------------------------------------------
-- Project: Music / Playlist Organiser
-- Example Queries (run after music_db.sql)
-- ---------------------------------------------------
USE music_db;

-- 1. Display all songs
SELECT * FROM Songs;

-- 2. Display all playlists
SELECT * FROM Playlists ORDER BY playlist_id;

-- 3. Show all songs in "Workout Vibes"
SELECT s.title, s.artist
FROM Songs s
JOIN PlaylistSongs ps ON s.song_id = ps.song_id
WHERE ps.playlist_id = 2;

-- 4. Search songs by genre 'Pop'
SELECT title, artist FROM Songs WHERE genre = 'Pop';

-- 5. Find all songs by 'Coldplay'
SELECT title, album FROM Songs WHERE artist = 'Coldplay';

-- 6. Count total songs by each artist
SELECT artist, COUNT(*) AS total_songs FROM Songs GROUP BY artist;

-- 7. List all albums and how many songs they have
SELECT album, COUNT(*) AS total_songs FROM Songs GROUP BY album;

-- Queries 8, 9 and 11 compare duration as text. That gives the right answer
-- while every song is shorter than 10 minutes ('9:59' sorts after '10:00').

-- 8. Find the longest song in the database
SELECT title, artist, duration FROM Songs ORDER BY duration DESC LIMIT 1;

-- 9. Find songs shorter than 3:30
SELECT title, artist, duration FROM Songs WHERE duration < '3:30';

-- 10. Show songs in 'Romantic Mood' playlist
SELECT s.title, s.artist
FROM Songs s
JOIN PlaylistSongs ps ON s.song_id = ps.song_id
WHERE ps.playlist_id = 5;

-- 11. Show all Pop songs with duration > 4 minutes
SELECT title, artist, duration FROM Songs WHERE genre = 'Pop' AND duration > '4:00';

-- 12. Display total number of songs in database
SELECT COUNT(*) AS total_songs FROM Songs;
