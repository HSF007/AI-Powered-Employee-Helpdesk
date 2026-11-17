
-- AI-Powered Employee Helpdesk - Demonstration Queries
--   psql -U postgres -d helpdesk -f database/queries.sql
-- IF ABOVE COMMAND DOESN'T WORK TRY
-- "C:\Program Files\PostgreSQL\<VERSION>\bin\psql.exe" -U psql -U postgres -d helpdesk -f database/queries.sql
-- For example which worked for me:
-- "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U psql -U postgres -d helpdesk -f database/queries.sql


-- Q1. Tickets with requester details and latest status
--     JOIN requesters + LATERAL join to the most recent
--     status entry in the activity log

SELECT
    t.id                 AS ticket_id,
    t.title,
    r.display_name       AS requester,
    r.contact,
    r.department,
    t.category,
    t.priority,
    t.status             AS current_status,
    ls.new_status        AS latest_logged_status,
    ls.performed_by      AS status_set_by,
    ls.created_at        AS status_set_at
FROM tickets t
JOIN requesters r ON r.id = t.requester_id
LEFT JOIN LATERAL (
    SELECT a.new_status, a.performed_by, a.created_at
    FROM ticket_activity a
    WHERE a.ticket_id = t.id
      AND a.activity_type IN ('CREATED', 'STATUS_CHANGE')
    ORDER BY a.created_at DESC, a.id DESC
    LIMIT 1
) ls ON TRUE
ORDER BY t.created_at DESC;


-- Q2. Support work queue: open High-priority tickets
--     (same filter the React work queue uses)

SELECT t.id, t.title, r.display_name AS requester, r.department,
       t.category, t.priority, t.status, t.created_at
FROM tickets t
JOIN requesters r ON r.id = t.requester_id
WHERE t.status <> 'Resolved'
  AND t.priority = 'High'
ORDER BY t.created_at;


-- Q3. Dashboard counts (aggregate + GROUP BY)

-- by status
SELECT status, COUNT(*) AS ticket_count
FROM tickets
GROUP BY status
ORDER BY CASE status WHEN 'New' THEN 1 WHEN 'In Progress' THEN 2 ELSE 3 END;

-- by priority (unconfirmed shown as 'Unassigned')
SELECT COALESCE(priority, 'Unassigned') AS priority, COUNT(*) AS ticket_count
FROM tickets
GROUP BY COALESCE(priority, 'Unassigned')
ORDER BY ticket_count DESC;

-- status x priority matrix in one row per status
SELECT
    status,
    COUNT(*) FILTER (WHERE priority = 'High')   AS high,
    COUNT(*) FILTER (WHERE priority = 'Medium') AS medium,
    COUNT(*) FILTER (WHERE priority = 'Low')    AS low,
    COUNT(*) FILTER (WHERE priority IS NULL)    AS unassigned,
    COUNT(*)                                    AS total
FROM tickets
GROUP BY status;


-- Q4. Open tickets per department (JOIN + GROUP BY)
SELECT r.department,
       COUNT(t.id) FILTER (WHERE t.status <> 'Resolved') AS open_tickets,
       COUNT(t.id)                                       AS all_tickets
FROM requesters r
LEFT JOIN tickets t ON t.requester_id = r.id
GROUP BY r.department
ORDER BY open_tickets DESC;


-- Q5. AI quality: acceptance and usefulness rates
SELECT
    COUNT(*)                                             AS total_reviews,
    COUNT(*) FILTER (WHERE action = 'ACCEPTED')          AS accepted,
    COUNT(*) FILTER (WHERE action = 'CORRECTED')         AS corrected,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_useful) / NULLIF(COUNT(*), 0), 1) AS useful_pct
FROM ai_feedback;


-- Q6. AI suggestion vs human-confirmed values per ticket
--     (shows AI advice is stored separately from decisions)

SELECT
    t.id                      AS ticket_id,
    t.title,
    s.suggested_category      AS ai_category,
    t.category                AS confirmed_category,
    s.suggested_priority      AS ai_priority,
    t.priority                AS confirmed_priority,
    f.action                  AS staff_decision,
    f.is_useful,
    f.staff_name
FROM tickets t
JOIN LATERAL (
    SELECT * FROM ai_suggestions s
    WHERE s.ticket_id = t.id
    ORDER BY s.created_at DESC, s.id DESC
    LIMIT 1
) s ON TRUE
LEFT JOIN ai_feedback f ON f.suggestion_id = s.id
ORDER BY t.id;


-- Q7. Full history of one ticket (the reopened printer, #9)
SELECT a.created_at, a.activity_type, a.old_status, a.new_status,
       a.old_value, a.new_value, a.note, a.performed_by
FROM ticket_activity a
WHERE a.ticket_id = 9
ORDER BY a.created_at, a.id;