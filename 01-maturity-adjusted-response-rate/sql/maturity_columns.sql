/* ---------------------------------------------------------------------------
   The adjustment, as it lives in a warehouse.

   Both columns are COMPUTED, not persisted: they re-evaluate against GETDATE()
   on every read, so a campaign matures on its own overnight with nothing to
   rerun. The catch is that an import-mode BI model freezes them at refresh,
   so the model has to be refreshed before anyone reads the rate.
   --------------------------------------------------------------------------- */

ALTER TABLE dim_campaign ADD days_since_inhome AS
    (DATEDIFF(DAY, [inhome_date], CONVERT(DATE, GETDATE())));
GO

ALTER TABLE dim_campaign ADD maturity AS
    (CASE WHEN [inhome_date] IS NULL                                       THEN 'Not delivered'
          WHEN DATEDIFF(DAY,[inhome_date],CONVERT(DATE,GETDATE())) >= 60   THEN 'Mature'
          WHEN DATEDIFF(DAY,[inhome_date],CONVERT(DATE,GETDATE())) >= 30   THEN 'Mostly in'
          WHEN DATEDIFF(DAY,[inhome_date],CONVERT(DATE,GETDATE())) >= 14   THEN 'Half in'
          ELSE 'Too early' END);
GO

/* The share of a piece's response window that has elapsed. The thresholds are
   read off the observed curve - they are an approximation of it, not a model
   of it, because this has to be cheap enough to sit in a computed column. */
ALTER TABLE dim_campaign ADD expected_response_pct AS
    (CASE WHEN [inhome_date] IS NULL                                       THEN 0.000
          WHEN DATEDIFF(DAY,[inhome_date],CONVERT(DATE,GETDATE())) >= 60   THEN 1.000
          WHEN DATEDIFF(DAY,[inhome_date],CONVERT(DATE,GETDATE())) >= 45   THEN 0.924
          WHEN DATEDIFF(DAY,[inhome_date],CONVERT(DATE,GETDATE())) >= 30   THEN 0.842
          WHEN DATEDIFF(DAY,[inhome_date],CONVERT(DATE,GETDATE())) >= 21   THEN 0.771
          WHEN DATEDIFF(DAY,[inhome_date],CONVERT(DATE,GETDATE())) >= 14   THEN 0.620
          WHEN DATEDIFF(DAY,[inhome_date],CONVERT(DATE,GETDATE())) >=  7   THEN 0.337
          WHEN DATEDIFF(DAY,[inhome_date],CONVERT(DATE,GETDATE())) >=  3   THEN 0.114
          ELSE 0.020 END);
GO

/* Scoring both ways, side by side. */
SELECT  c.campaign_id,
        c.days_since_inhome,
        c.maturity,
        COUNT(*)                                            AS pieces,
        SUM(f.replied)                                      AS replies,
        CAST(SUM(f.replied) AS FLOAT) / COUNT(*)            AS raw_rate,
        CAST(SUM(f.replied) AS FLOAT)
            / NULLIF(SUM(c.expected_response_pct), 0)       AS adjusted_rate
FROM    fact_piece f
JOIN    dim_campaign c ON c.campaign_key = f.campaign_key
GROUP BY c.campaign_id, c.days_since_inhome, c.maturity
ORDER BY c.days_since_inhome;
