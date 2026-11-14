-- Datos iniciales para musica.db (tarea 2 del taller: 5 usuarios y 10 canciones).
-- Se puede ejecutar desde el editor SQL de DBeaver (conexión SQLite a musica.db).
-- Los usuarios usan INSERT OR IGNORE (correo único); las canciones se duplicarían
-- si se ejecuta dos veces.

BEGIN TRANSACTION;

INSERT OR IGNORE INTO usuario (nombre, correo, fecha_registro) VALUES
    ('Laura Gómez',     'laura.gomez@example.com',     '2026-11-10 09:15:00.000000'),
    ('Carlos Ramírez',  'carlos.ramirez@example.com',  '2026-11-10 14:42:00.000000'),
    ('Valentina Ruiz',  'valentina.ruiz@example.com',  '2026-11-11 08:05:00.000000'),
    ('Andrés Morales',  'andres.morales@example.com',  '2026-11-12 19:30:00.000000'),
    ('Camila Torres',   'camila.torres@example.com',   '2026-11-13 11:20:00.000000');

-- duracion en segundos
INSERT INTO cancion (titulo, artista, album, duracion, "año", genero, fecha_creacion) VALUES
    ('Bohemian Rhapsody',       'Queen',            'A Night at the Opera',        354, 1975, 'Rock',      '2026-11-10 10:00:00.000000'),
    ('Hotel California',        'Eagles',           'Hotel California',            391, 1976, 'Rock',      '2026-11-10 10:05:00.000000'),
    ('Billie Jean',             'Michael Jackson',  'Thriller',                    294, 1982, 'Pop',       '2026-11-10 10:10:00.000000'),
    ('Smells Like Teen Spirit', 'Nirvana',          'Nevermind',                   301, 1991, 'Grunge',    '2026-11-10 10:15:00.000000'),
    ('La Bicicleta',            'Carlos Vives',     'Vives',                       227, 2016, 'Vallenato', '2026-11-10 10:20:00.000000'),
    ('Hips Don''t Lie',         'Shakira',          'Oral Fixation, Vol. 2',       218, 2006, 'Pop',       '2026-11-10 10:25:00.000000'),
    ('De Música Ligera',        'Soda Stereo',      'Canción Animal',              213, 1990, 'Rock',      '2026-11-10 10:30:00.000000'),
    ('Despacito',               'Luis Fonsi',       'Vida',                        229, 2017, 'Reggaetón', '2026-11-10 10:35:00.000000'),
    ('So What',                 'Miles Davis',      'Kind of Blue',                562, 1959, 'Jazz',      '2026-11-10 10:40:00.000000'),
    ('Blinding Lights',         'The Weeknd',       'After Hours',                 200, 2019, 'Pop',       '2026-11-10 10:45:00.000000');

COMMIT;
