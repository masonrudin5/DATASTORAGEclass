CREATE TABLE RottenMovies(
    MName VARCHAR(100) NOT NULL PRIMARY KEY,
    CriticScore INT,
    AudienceScore INT,
    ReleaseDate DATE
);

-- Notes: SELECT used in lab12.py to graph the average audience score for each release date in the past year
SELECT ReleaseDate, ROUND(AVG(AudienceScore), 1) AS AvgAudienceScore
FROM RottenMovies
WHERE AudienceScore IS NOT NULL
  AND ReleaseDate BETWEEN DATE_SUB(CURDATE(), INTERVAL 1 YEAR) AND CURDATE()
GROUP BY ReleaseDate
ORDER BY ReleaseDate;
