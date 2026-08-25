
-- 1) Monthly management KPI report
SELECT
    substr(InvoiceDate, 1, 7) AS month,
    ROUND(SUM(Revenue), 2) AS revenue_gbp,
    COUNT(DISTINCT InvoiceNo) AS orders,
    COUNT(DISTINCT CustomerID) AS customers,
    ROUND(SUM(Revenue) / COUNT(DISTINCT InvoiceNo), 2) AS average_order_value_gbp
FROM transactions
GROUP BY substr(InvoiceDate, 1, 7)
ORDER BY month;


-- 2) Highest-value markets outside the UK
SELECT
    Country,
    ROUND(SUM(Revenue), 2) AS revenue_gbp,
    COUNT(DISTINCT CustomerID) AS customers,
    COUNT(DISTINCT InvoiceNo) AS orders,
    ROUND(SUM(Revenue) / COUNT(DISTINCT CustomerID), 2) AS revenue_per_customer_gbp
FROM transactions
WHERE Country <> 'United Kingdom'
GROUP BY Country
HAVING COUNT(DISTINCT CustomerID) >= 10
ORDER BY revenue_gbp DESC
LIMIT 15;


-- 3) Customers with high historical value and long inactivity
WITH customer_value AS (
    SELECT
        CustomerID,
        MAX(date(InvoiceDate)) AS last_purchase,
        COUNT(DISTINCT InvoiceNo) AS orders,
        ROUND(SUM(Revenue), 2) AS lifetime_value_gbp
    FROM transactions
    GROUP BY CustomerID
)
SELECT *
FROM customer_value
WHERE orders >= 3
ORDER BY lifetime_value_gbp DESC
LIMIT 50;
