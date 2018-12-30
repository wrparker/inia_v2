use seeder;
SELECT * INTO OUTFILE '/var/lib/mysql-files/publications.tsv'
    FIELDS TERMINATED BY '\t' OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
FROM publications;

SELECT * INTO OUTFILE '/var/lib/mysql-files/datasets.tsv'
    FIELDS TERMINATED BY '\t' OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
FROM datasets;

SELECT * INTO OUTFILE '/var/lib/mysql-files/genes.tsv'
    FIELDS TERMINATED BY '\t' OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
FROM genes;

