-- =====================================================
-- AI-Powered Employee Helpdesk - Database Schema
-- Run with: psql -U postgres -d helpdesk -f database/schema.sql
-- Safe to re-run: drops tables first (deletes all data!)
-- =====================================================

DROP TABLE IF EXISTS ai_feedback CASCADE;
DROP TABLE IF EXISTS ai_suggestions CASCADE;
DROP TABLE IF EXISTS ticket_activity CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS requesters CASCADE;

-- -----------------------------------------------------
-- 1. Requesters: employees who raise tickets
-- -----------------------------------------------------
CREATE TABLE requesters (
    id            SERIAL PRIMARY KEY,
    display_name  VARCHAR(100) NOT NULL CHECK (length(trim(display_name)) > 0),
    contact       VARCHAR(150) NOT NULL UNIQUE CHECK (length(trim(contact)) > 0),
    department    VARCHAR(100),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------
-- 2. Tickets: the human-confirmed values live here
--    (AI suggestions are stored separately)
-- -----------------------------------------------------
CREATE TABLE tickets (
    id            SERIAL PRIMARY KEY,
    requester_id  INTEGER NOT NULL REFERENCES requesters(id),
    title         VARCHAR(200) NOT NULL CHECK (length(trim(title)) > 0),
    description   TEXT NOT NULL CHECK (length(trim(description)) > 0),
    category      VARCHAR(20)
                  CHECK (category IN ('Hardware', 'Software', 'Network', 'Access', 'Other')),
    priority      VARCHAR(10)
                  CHECK (priority IN ('Low', 'Medium', 'High')),
    status        VARCHAR(20) NOT NULL DEFAULT 'New'
                  CHECK (status IN ('New', 'In Progress', 'Resolved')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- category / priority can be NULL until support staff confirm them

-- -----------------------------------------------------
-- 3. Ticket activity: full history, never overwritten
-- -----------------------------------------------------
CREATE TABLE ticket_activity (
    id             SERIAL PRIMARY KEY,
    ticket_id      INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    activity_type  VARCHAR(20) NOT NULL
                   CHECK (activity_type IN ('CREATED', 'STATUS_CHANGE', 'PRIORITY_CHANGE',
                                            'CATEGORY_CHANGE', 'COMMENT')),
    old_status     VARCHAR(20) CHECK (old_status IN ('New', 'In Progress', 'Resolved')),
    new_status     VARCHAR(20) CHECK (new_status IN ('New', 'In Progress', 'Resolved')),
    old_value      VARCHAR(50),   -- for priority/category changes
    new_value      VARCHAR(50),
    note           TEXT,          -- support comment or action description
    performed_by   VARCHAR(100) NOT NULL DEFAULT 'system',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------
-- 4. AI suggestions: advisory only, never the confirmed values
-- -----------------------------------------------------
CREATE TABLE ai_suggestions (
    id                     SERIAL PRIMARY KEY,
    ticket_id              INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    suggested_category     VARCHAR(20) NOT NULL
                           CHECK (suggested_category IN ('Hardware', 'Software', 'Network', 'Access', 'Other')),
    suggested_priority     VARCHAR(10) NOT NULL
                           CHECK (suggested_priority IN ('Low', 'Medium', 'High')),
    reason                 TEXT NOT NULL,
    troubleshooting_steps  JSONB NOT NULL,   -- e.g. ["Check batteries", "Re-pair receiver"]
    model_name             VARCHAR(50) NOT NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------
-- 5. AI feedback: staff accept/correct + useful or not
-- -----------------------------------------------------
CREATE TABLE ai_feedback (
    id              SERIAL PRIMARY KEY,
    suggestion_id   INTEGER NOT NULL REFERENCES ai_suggestions(id) ON DELETE CASCADE,
    ticket_id       INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    action          VARCHAR(10) NOT NULL CHECK (action IN ('ACCEPTED', 'CORRECTED')),
    is_useful       BOOLEAN NOT NULL,
    final_category  VARCHAR(20) NOT NULL
                    CHECK (final_category IN ('Hardware', 'Software', 'Network', 'Access', 'Other')),
    final_priority  VARCHAR(10) NOT NULL
                    CHECK (final_priority IN ('Low', 'Medium', 'High')),
    staff_name      VARCHAR(100) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------
-- Indexes (speed up filters in the support work queue)
-- -----------------------------------------------------
CREATE INDEX idx_tickets_status       ON tickets(status);
CREATE INDEX idx_tickets_priority     ON tickets(priority);
CREATE INDEX idx_tickets_category     ON tickets(category);
CREATE INDEX idx_tickets_requester    ON tickets(requester_id);
CREATE INDEX idx_activity_ticket      ON ticket_activity(ticket_id, created_at);
CREATE INDEX idx_suggestions_ticket   ON ai_suggestions(ticket_id);
CREATE INDEX idx_feedback_suggestion  ON ai_feedback(suggestion_id);