-------big 5 subsets aggregation-------

--list LVTS participants
select distinct(sender) from high_value_data_2016;

--Scotiabank
create table scotia as (
select *
from high_value_data_2016
where sender = 'NOSCCA'
)

create table scotia_2 as (
select *
from high_value_data_2017
where sender = 'NOSCCA'
)

--Royal Bank of Canada
create table royal_bank as (
select *
from high_value_data_2016
where sender = 'ROYCCA'
)

create table royal_bank_2 as (
select *
from high_value_data_2017
where sender = 'ROYCCA'
)

--CIBC
create table cibc as (
select *
from high_value_data_2016
where sender = 'CIBCCA'
)

create table cibc_2 as (
select *
from high_value_data_2017
where sender = 'CIBCCA'
)

--TD Bank
create table td_bank as (
select *
from high_value_data_2016
where sender = 'TDOMCA'
)

create table td_bank_2 as (
select *
from high_value_data_2017
where sender = 'TDOMCA'
)

--BMO
create table bmo_bank as (
select *
from high_value_data_2016
where sender = 'BOFMCA'
)

create table bmo_bank_2 as (
select *
from high_value_data_2017
where sender = 'BOFMCA'
)

------------------------------------------------------

-- 2016 data preprocessing (scotia)
SELECT amount, sender, TO_TIMESTAMP(date_time, 'YYYY-MM-DD HH24:MI:SS')::TIMESTAMP AS dateTime
INTO TEMP TABLE high_value_data_2016_cleaned
FROM scotia
ORDER BY datetime;

SELECT amount, sender, TO_TIMESTAMP(date_time, 'YYYY-MM-DD HH24:MI:SS')::TIMESTAMP AS dateTime
INTO TEMP TABLE high_value_data_2017_cleaned
FROM scotia_2
ORDER BY datetime;


-- 2016 data preprocessing (rbc)
SELECT amount, sender, TO_TIMESTAMP(date_time, 'YYYY-MM-DD HH24:MI:SS')::TIMESTAMP AS dateTime
INTO TEMP TABLE high_value_data_2016_cleaned
FROM royal_bank
ORDER BY datetime;

SELECT amount, sender, TO_TIMESTAMP(date_time, 'YYYY-MM-DD HH24:MI:SS')::TIMESTAMP AS dateTime
INTO TEMP TABLE high_value_data_2017_cleaned
FROM royal_bank_2
ORDER BY datetime;




-- 2016 data preprocessing (cibc)
SELECT amount, sender, TO_TIMESTAMP(date_time, 'YYYY-MM-DD HH24:MI:SS')::TIMESTAMP AS dateTime
INTO TEMP TABLE high_value_data_2016_cleaned
FROM cibc
ORDER BY datetime;

SELECT amount, sender, TO_TIMESTAMP(date_time, 'YYYY-MM-DD HH24:MI:SS')::TIMESTAMP AS dateTime
INTO TEMP TABLE high_value_data_2017_cleaned
FROM cibc_2
ORDER BY datetime;




-- 2016 data preprocessing (TD)
SELECT amount, sender, TO_TIMESTAMP(date_time, 'YYYY-MM-DD HH24:MI:SS')::TIMESTAMP AS dateTime
INTO TEMP TABLE high_value_data_2016_cleaned
FROM td_bank
ORDER BY datetime;

SELECT amount, sender, TO_TIMESTAMP(date_time, 'YYYY-MM-DD HH24:MI:SS')::TIMESTAMP AS dateTime
INTO TEMP TABLE high_value_data_2017_cleaned
FROM td_bank_2
ORDER BY datetime;




-- 2016/2017 data preprocessing (BMO)
SELECT amount, sender, TO_TIMESTAMP(date_time, 'YYYY-MM-DD HH24:MI:SS')::TIMESTAMP AS dateTime
INTO TEMP TABLE high_value_data_2016_cleaned
FROM bmo_bank
ORDER BY datetime;

SELECT amount, sender, TO_TIMESTAMP(date_time, 'YYYY-MM-DD HH24:MI:SS')::TIMESTAMP AS dateTime
INTO TEMP TABLE high_value_data_2017_cleaned
FROM bmo_bank_2
ORDER BY datetime;

----------------------------------------------------
drop table high_value_data_2016_cleaned;
drop table high_value_data_2017_cleaned;
drop table timeseries;
drop table timeseriesdata;
----------------------------------------------------

-- Create a time series datatable with each row being a minute
CREATE TEMP TABLE timeseries(
	datetime TIMESTAMP,
	amount DOUBLE PRECISION,
	sender VARCHAR
);

SELECT *
FROM timeseries;

WITH tempTimeSeries AS(
	SELECT *
	FROM generate_series('2016-01-01'::timestamp,						-- Date interval subject to change
						 '2018-01-01'::timestamp,						-- Date interval subject to change
						 '1 minute'::interval) AS datetime
)
INSERT INTO timeseries
SELECT datetime
FROM tempTimeSeries;

UPDATE timeseries
SET amount = 0, sender = 'no_transaction';

SELECT *
FROM timeseries
ORDER BY datetime DESC;

-- Merge transaction data with the time series data through concatenation. Ordered by datetime.
SELECT *
INTO TEMP TABLE timeseriesdata
FROM high_value_data_2016_cleaned
UNION ALL
SELECT *
FROM high_value_data_2017_cleaned
UNION ALL
SELECT amount, sender, datetime
FROM timeseries
ORDER BY datetime;

SELECT *
FROM timeseriesdata
ORDER BY datetime DESC;

-- Convert the dataset into 5 minutes intervals
WITH tempTable AS(
SELECT *, datetime::DATE AS date,
	EXTRACT(hour FROM date_trunc('hour', datetime)) AS hour_stamp
FROM timeseriesdata)
SELECT date, hour_stamp,
	   ((EXTRACT(minute FROM datetime) + hour_stamp * 60)::int / 5) + 1 AS fiveMinInterval,
		SUM(amount)	
INTO TABLE five_minutes_interval_data_16_17_bmo
FROM tempTable
GROUP BY date, hour_stamp, fiveMinInterval
ORDER BY date, hour_stamp, fiveMinInterval;



-----------------------------------------------------

-- Check the largest amounts
SELECT *
FROM high_value_data_2016
ORDER BY amount DESC
LIMIT 100;

-- Check distribution of amounts
WITH total_transactions AS(
SELECT COUNT(*) AS total_count, SUM(amount) AS total_amount
FROM high_value_data_2016),
part_transactions AS(
SELECT COUNT(*) AS part_count, SUM(amount) AS part_amount
FROM high_value_data_2016
WHERE amount >= 2147500)
SELECT *, (part_count::DOUBLE PRECISION / total_count::DOUBLE PRECISION) AS percentage_number,
		(part_amount::DOUBLE PRECISION / total_amount::DOUBLE PRECISION) AS percentage_amount
FROM total_transactions CROSS JOIN part_transactions;

-- Check unique senders
SELECT DISTINCT sender
FROM high_value_data_2016;

-- 2016 data preprocessing
SELECT amount, sender, TO_TIMESTAMP(date_time, 'YYYY-MM-DD HH24:MI:SS')::TIMESTAMP AS dateTime
INTO TEMP TABLE high_value_data_2016_cleaned
FROM high_value_data_2016
ORDER BY datetime;

SELECT *
FROM high_value_data_2016_cleaned;

-- 2017 data preprocessing
SELECT amount, sender, TO_TIMESTAMP(date_time, 'YYYY-MM-DD HH24:MI:SS')::TIMESTAMP AS dateTime
INTO TEMP TABLE high_value_data_2017_cleaned
FROM high_value_data_2017
ORDER BY datetime;

SELECT *
FROM high_value_data_2017_cleaned;

-- Create a time series datatable with each row being a minute
CREATE TEMP TABLE timeseries(
	datetime TIMESTAMP,
	amount DOUBLE PRECISION,
	sender VARCHAR
);

SELECT *
FROM timeseries;

WITH tempTimeSeries AS(
	SELECT *
	FROM generate_series('2016-01-01'::timestamp,						-- Date interval subject to change
						 '2018-01-01'::timestamp,						-- Date interval subject to change
						 '1 minute'::interval) AS datetime
)
INSERT INTO timeseries
SELECT datetime
FROM tempTimeSeries;

UPDATE timeseries
SET amount = 0, sender = 'no_transaction';

SELECT *
FROM timeseries
ORDER BY datetime DESC;

-- Merge transaction data with the time series data through concatenation. Ordered by datetime.
SELECT *
INTO TEMP TABLE timeseriesdata
FROM high_value_data_2016_cleaned
UNION ALL
SELECT *
FROM high_value_data_2017_cleaned
UNION ALL
SELECT amount, sender, datetime
FROM timeseries
ORDER BY datetime;

SELECT *
FROM timeseriesdata
ORDER BY datetime DESC;

-- Convert the dataset into 5 minutes intervals
WITH tempTable AS(
SELECT *, datetime::DATE AS date,
	EXTRACT(hour FROM date_trunc('hour', datetime)) AS hour_stamp
FROM timeseriesdata)
SELECT date, hour_stamp,
	   ((EXTRACT(minute FROM datetime) + hour_stamp * 60)::int / 5) + 1 AS fiveMinInterval,
		SUM(amount)	
INTO TABLE five_minutes_interval_data_16_17
FROM tempTable
GROUP BY date, hour_stamp, fiveMinInterval
ORDER BY date, hour_stamp, fiveMinInterval;

SELECT *
FROM five_minutes_interval_data_16_17;