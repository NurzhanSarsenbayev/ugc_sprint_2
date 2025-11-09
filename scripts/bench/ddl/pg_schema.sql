CREATE TABLE IF NOT EXISTS ratings (
  film_id  UUID NOT NULL,
  user_id  UUID NOT NULL,
  score    SMALLINT NOT NULL CHECK (score BETWEEN 1 AND 10),
  PRIMARY KEY (film_id, user_id)
);

-- Индексы под частые запросы
CREATE INDEX IF NOT EXISTS idx_ratings_user ON ratings(user_id);
-- для быстрой агрегации по фильму PostgreSQL берёт по PK (film_id, user_id),
-- при необходимости можно добавить (film_id, score)
