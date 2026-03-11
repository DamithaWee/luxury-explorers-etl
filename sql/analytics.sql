-- =======================================================
-- QUERY 1: Top 3 Cleanest Restaurants per Borough
-- =======================================================
WITH RankedRestaurants AS (
    SELECT 
        l.borough,
        r.name AS restaurant_name,
        r.category,
        ROUND(AVG(f.score), 2) AS avg_score,
        COUNT(f.inspection_id) AS total_inspections,
        RANK() OVER(PARTITION BY l.borough ORDER BY AVG(f.score) ASC) as safety_rank
    FROM presentation.fact_inspection f
    JOIN presentation.dim_restaurant r ON f.restaurant_id = r.restaurant_id
    JOIN presentation.dim_location l ON f.location_id = l.location_id
    GROUP BY l.borough, r.name, r.category
    HAVING COUNT(f.inspection_id) >= 3 -- Only count established restaurants
)
SELECT * FROM RankedRestaurants 
WHERE safety_rank <= 3;

-- =======================================================
-- QUERY 2: Most High-Risk Cuisines by Critical Violation Ratio
-- =======================================================
WITH CuisineRiskStats AS (
    SELECT 
        r.category AS cuisine_type,
        COUNT(f.inspection_id) AS total_inspections,
        SUM(CASE WHEN f.critical_flag = 'Critical' THEN 1 ELSE 0 END) AS critical_violations
    FROM presentation.fact_inspection f
    JOIN presentation.dim_restaurant r ON f.restaurant_id = r.restaurant_id
    GROUP BY r.category
)
SELECT 
    cuisine_type,
    total_inspections,
    critical_violations,
    ROUND((critical_violations::DECIMAL / total_inspections) * 100, 2) AS critical_violation_rate_pct
FROM CuisineRiskStats
WHERE total_inspections > 100
ORDER BY critical_violation_rate_pct DESC
LIMIT 10;

-- =======================================================
-- QUERY 3: Year-over-Year Trend of Critical Violations
-- =======================================================
SELECT 
    EXTRACT(YEAR FROM inspection_date) AS inspection_year,
    EXTRACT(MONTH FROM inspection_date) AS inspection_month,
    COUNT(inspection_id) AS total_critical_violations,
    ROUND(AVG(score), 2) AS monthly_average_score
FROM presentation.fact_inspection
WHERE critical_flag = 'Critical'
GROUP BY EXTRACT(YEAR FROM inspection_date), EXTRACT(MONTH FROM inspection_date)
ORDER BY inspection_year DESC, inspection_month DESC;

-- =======================================================
-- QUERY 4: Top 10 Worst-Performing Cuisines by Avg Score
-- =======================================================
SELECT 
    r.category AS cuisine_type,
    ROUND(AVG(f.score), 2) AS average_inspection_score,
    COUNT(f.inspection_id) AS total_inspections
FROM presentation.fact_inspection f
JOIN presentation.dim_restaurant r 
    ON f.restaurant_id = r.restaurant_id
GROUP BY r.category
HAVING COUNT(f.inspection_id) > 50 -- Filter out statistical anomalies
ORDER BY average_inspection_score DESC
LIMIT 10;

-- =======================================================
-- QUERY 5: Monthly Inspection Volume
-- =======================================================
SELECT 
    TO_CHAR(inspection_date, 'YYYY-MM') AS inspection_month,
    COUNT(inspection_id) AS total_inspections
FROM presentation.fact_inspection
GROUP BY TO_CHAR(inspection_date, 'YYYY-MM')
ORDER BY inspection_month DESC;

-- =======================================================
-- QUERY 6: Average Score Breakdown by Borough (Location)
-- =======================================================
SELECT 
    l.borough,
    ROUND(AVG(f.score), 2) AS average_score,
    COUNT(DISTINCT f.restaurant_id) AS unique_restaurants_inspected
FROM presentation.fact_inspection f
JOIN presentation.dim_location l 
    ON f.location_id = l.location_id
GROUP BY l.borough
ORDER BY average_score DESC;

