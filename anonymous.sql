SELECT *
FROM anon;

SELECT date_published
FROM anon;

SELECT count(*)
FROM anon;

SELECT
  source,
  count(source)
FROM anon
GROUP BY source
ORDER BY count(source)
  DESC;

SELECT
  date_published,
  count(date_published)
FROM anon
GROUP BY date_published
ORDER BY date_published
  DESC;

SELECT
  link,
  source,
  phrase,
  title,
  content,
  date_published
FROM anon
ORDER BY date_published
  DESC
LIMIT 100;

DELETE FROM anon
WHERE content NOT LIKE "%<b>%";

CREATE TABLE anon (
  source,
  phrase,
  title,
  link PRIMARY KEY ON CONFLICT IGNORE,
  content,
  date_published DATE
);

SELECT outlets.name
FROM anon
  LEFT OUTER JOIN outlets ON anon.source = outlets.url;

SELECT
  anon.source,
  outlets.name,
  anon.phrase,
  anon.title,
  anon.link,
  anon.content,
  anon.date_published
FROM anon
  LEFT OUTER JOIN outlets ON anon.source = outlets.url;

SELECT
  outlets.name,
  outlets.url
FROM outlets
ORDER BY outlets.name;

SELECT DISTINCT
  anon.source,
  outlets.name
FROM anon
  JOIN outlets ON anon.source = outlets.url
ORDER BY outlets.name;

SELECT DISTINCT anon.source
FROM anon;

SELECT
  anon.title,
  count(anon.title)
FROM anon
GROUP BY anon.title
ORDER BY count(anon.title)
  DESC;

SELECT
  anon.source,
  anon.content,
  count(anon.content)
FROM anon
GROUP BY anon.content
ORDER BY count(anon.content)
  DESC;

DELETE FROM anon
WHERE ROWID NOT IN (SELECT min(ROWID)
                    FROM anon
                    GROUP BY source, content);

DELETE FROM anon
WHERE ROWID NOT IN (SELECT min(ROWID)
                    FROM anon
                    GROUP BY source, title);

SELECT
  source,
  content,
  count(source)
FROM anon
GROUP BY source, content
ORDER BY count(source)
  DESC;

SELECT
  source,
  title,
  count(source)
FROM anon
GROUP BY source, title
ORDER BY count(source)
  DESC;

SELECT min(ROWID)
FROM anon
GROUP BY source, title;

SELECT
  source,
  title
FROM anon
GROUP BY source, title;

SELECT link
FROM anon
WHERE date_published = '2016-06-20';

SELECT *
FROM anon;

SELECT
  anon.source,
  outlets.name,
  anon.phrase,
  anon.title,
  anon.link,
  anon.content,
  anon.date_published
FROM anon
  LEFT OUTER JOIN outlets ON anon.source = outlets.url
ORDER BY date_published
  DESC
LIMIT 100, 10;


SELECT count(*)
FROM anon
  LEFT OUTER JOIN outlets ON anon.source = outlets.url
WHERE anon.source = 'www.nytimes.com';

SELECT count(*) FROM anon where source = 'www.nytimes.com';
