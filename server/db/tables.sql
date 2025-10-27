------------------------------------------------
----          [Zar - Url Shortener]         ----
----              SCHEMA V2.0               ----
------------------------------------------------

------------------------------------------------
----                [DROPS]                 ----
------------------------------------------------
-- DROP TABLE IF EXISTS users CASCADE;
-- DROP TABLE IF EXISTS domains CASCADE;
-- DROP TABLE IF EXISTS urls CASCADE;
-- DROP TABLE IF EXISTS url_tags CASCADE;
-- DROP TABLE IF EXISTS url_tag_relations CASCADE;
-- DROP TABLE IF EXISTS url_analytics CASCADE;
-- DROP TABLE IF EXISTS logs CASCADE;
-- DROP TABLE IF EXISTS rate_limit_logs CASCADE;
-- DROP FUNCTION increment_url_clicks CASCADE;
------------------------------------------------
----             [EXTENSIONS]               ----
------------------------------------------------
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

------------------------------------------------
----              [FUNCTIONS]               ----
------------------------------------------------

-------------[GENERATE SHORT CODE]--------------
CREATE OR REPLACE FUNCTION generate_short_code(p_length INT DEFAULT 8)
RETURNS TEXT AS $$
DECLARE
    charset TEXT := 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-';
    new_short_code TEXT := '';
    i INT;
BEGIN
    LOOP
        new_short_code := '';
        FOR i IN 1..p_length LOOP
            new_short_code := new_short_code || substring(
                charset,
                FLOOR(random() * length(charset))::INT + 1,
                1
            );
        END LOOP;
        EXIT WHEN NOT EXISTS (SELECT 1 FROM urls WHERE urls.short_code = new_short_code);
    END LOOP;
    RETURN new_short_code;
END;
$$ LANGUAGE plpgsql;
------------------------------------------------
------------------------------------------------

------------------[URL CLICKS]------------------
-- Função para incrementar clicks atomicamente
CREATE OR REPLACE FUNCTION increment_url_clicks(p_url_id BIGINT)
RETURNS void AS $$
BEGIN
    UPDATE 
        urls
    SET 
        clicks = clicks + 1,
        last_clicked_at = NOW()
    WHERE 
        id = p_url_id;
END;
$$ LANGUAGE plpgsql;
------------------------------------------------

----------------[EXPIRED SESSIONS]--------------
-- Função para limpar sessões expiradas (manutenção)
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_session_tokens
    WHERE expires_at < NOW() - INTERVAL '7 days'
       OR (revoked = TRUE AND issued_at < NOW() - INTERVAL '30 days');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
------------------------------------------------

----------------[CLEANUP ANALYTICS]-------------
-- Função para limpar analytics antigos (manutenção)
CREATE OR REPLACE FUNCTION cleanup_old_analytics(months_to_keep INTEGER DEFAULT 12)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM url_analytics
    WHERE clicked_at < NOW() - (months_to_keep || ' months')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
------------------------------------------------

------------------------------------------------
----                 [USERS]                ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email CITEXT NOT NULL,
    p_hash BYTEA NOT NULL,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT users_unique_email_cstr UNIQUE (email),
    CONSTRAINT user_check_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

------------------------------------------------
----         [USER SESSIONS TOKENS]         ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS user_session_tokens (
    refresh_token TEXT PRIMARY KEY,
    user_id UUID NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at TIMESTAMPTZ,
    device_name TEXT NOT NULL,
    device_ip INET NOT NULL,
    user_agent TEXT NOT NULL,
    last_used_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_user_session_user FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT user_session_tokens_unique_user_device UNIQUE (user_id, device_ip, user_agent),
    CONSTRAINT chk_expires_after_issued CHECK (expires_at > issued_at),
    CONSTRAINT chk_revoked_at_when_revoked CHECK ((revoked = FALSE AND revoked_at IS NULL) OR (revoked = TRUE AND revoked_at IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS idx_user_session_tokens_user ON user_session_tokens(user_id) WHERE revoked = FALSE;
CREATE INDEX IF NOT EXISTS idx_user_session_tokens_expires ON user_session_tokens(expires_at) WHERE revoked = FALSE;

------------------------------------------------
----         [USER LOGIN ATTEMPTS]          ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS user_login_attempts (
    user_id UUID PRIMARY KEY,
    attempts INT NOT NULL DEFAULT 0,
    last_failed_login TIMESTAMPTZ,
    locked_until TIMESTAMPTZ,
    last_successful_login TIMESTAMPTZ,
    CONSTRAINT fk_login_attempts_user FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT chk_attempts_non_negative CHECK (attempts >= 0),
    CONSTRAINT chk_attempts_reasonable CHECK (attempts <= 1000)
);

CREATE INDEX IF NOT EXISTS idx_login_attempts_locked ON user_login_attempts(locked_until) WHERE locked_until IS NOT NULL;

------------------------------------------------
----              [DOMAINS URL]             ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS domains (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    url TEXT NOT NULL,
    url_hash BYTEA NOT NULL,
    is_secure BOOLEAN DEFAULT TRUE,
    CONSTRAINT chk_url CHECK (url ~ '^(https?://)([A-Za-z0-9-]+\.)+[A-Za-z]{2,}(/.*)?$'),
    CONSTRAINT domains_unique_url UNIQUE (url_hash)
);

------------------------------------------------
----                 [URLS]                 ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS urls (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    short_code TEXT NOT NULL,
    domain_id BIGINT NOT NULL,
    original_url TEXT NOT NULL,
    original_url_hash BYTEA NOT NULL,
    clicks INTEGER DEFAULT 0 NOT NULL,
    last_clicked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    CONSTRAINT urls_chk_url CHECK (original_url ~ '^(https?://)([A-Za-z0-9-]+\.)+[A-Za-z]{2,}(/.*)?$'),
    CONSTRAINT urls_unique_short_code_cstr UNIQUE (short_code),
    CONSTRAINT chk_expires_after_created CHECK (expires_at IS NULL OR expires_at > created_at),
    CONSTRAINT chk_clicks_non_negative CHECK (clicks >= 0),
    FOREIGN KEY (domain_id) REFERENCES domains(id) ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_urls_original_url_hash ON urls(original_url_hash);
CREATE INDEX IF NOT EXISTS idx_urls_created_at ON urls(created_at DESC) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_expires_at ON urls(expires_at) WHERE expires_at IS NOT NULL AND is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_clicks ON urls(clicks DESC) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_timestamps ON urls(created_at DESC, last_clicked_at DESC) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_active_clicks ON urls(id, clicks) WHERE is_active = TRUE;


------------------------------------------------
----               [USER URLS]              ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS user_urls (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    url_id BIGINT NOT NULL,
    user_id UUID NOT NULL,
    is_favorite BOOLEAN DEFAULT FALSE,
    CONSTRAINT user_urls_unique_cstr UNIQUE (url_id, user_id),
    FOREIGN KEY (url_id) REFERENCES urls(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_user_urls_user_favorite ON user_urls(user_id, is_favorite);
CREATE INDEX IF NOT EXISTS idx_user_urls_url_id ON user_urls(url_id);

------------------------------------------------
----               [URL TAGS]               ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS url_tags (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id UUID NOT NULL,
    tag_color TEXT NOT NULL DEFAULT '#d8775a',
    tag_name citext NOT NULL,
    descr TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT url_tags_unique_tag UNIQUE (user_id, tag_name),
    CONSTRAINT chk_tag_color_hex CHECK (tag_color ~ '^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'),
    CONSTRAINT chk_tag_name_length CHECK (length(tag_name) BETWEEN 1 AND 64),
    FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_url_tags_user ON url_tags(user_id);

------------------------------------------------
----          [URL TAG RELATIONS]           ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS url_tag_relations (
    url_id BIGINT NOT NULL,
    tag_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (url_id, tag_id),
    FOREIGN KEY (url_id) REFERENCES urls(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES url_tags(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_url_tag_relations_tag ON url_tag_relations(tag_id);

------------------------------------------------
----             [URL ANALYTICS]            ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS url_analytics (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    url_id BIGINT NOT NULL,
    clicked_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    ip_address INET,
    country_code CHAR(2),
    city TEXT,
    user_agent TEXT,
    referer TEXT,
    device_type VARCHAR(20),
    browser VARCHAR(50),
    os VARCHAR(50),
    PRIMARY KEY (id, clicked_at),
    FOREIGN KEY (url_id) REFERENCES urls(id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE INDEX IF NOT EXISTS idx_url_analytics_url_id ON url_analytics(url_id, clicked_at DESC);
CREATE INDEX IF NOT EXISTS idx_url_analytics_date ON url_analytics(clicked_at DESC);
CREATE INDEX IF NOT EXISTS idx_url_analytics_country ON url_analytics(country_code) WHERE country_code IS NOT NULL;

------------------------------------------------
----                 [LOGS]                 ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    level VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    path TEXT,
    method VARCHAR(10),
    status_code INT,
    user_id UUID,
    stacktrace TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT chk_log_level CHECK (level IN ('DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'))
);

CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_user ON logs(user_id) WHERE user_id IS NOT NULL;


------------------------------------------------
----             [PERF LOGS]                ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS time_perf (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    perf_type TEXT NOT NULL,
    perf_subtype TEXT,
    execution_time DOUBLE PRECISION NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_time_perf_type ON time_perf(perf_type);
CREATE INDEX IF NOT EXISTS idx_time_perf_created_at ON time_perf(created_at);

------------------------------------------------
----           [RATE LIMIT LOGS]            ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS rate_limit_logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ip_address INET NOT NULL,
    path TEXT NOT NULL,
    method TEXT NOT NULL,
    attempts BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_attempt_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    window_start TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT rate_limit_logs_unique_cstr UNIQUE (ip_address, path, method, window_start)
);

CREATE INDEX IF NOT EXISTS idx_rate_limit_ip ON rate_limit_logs(ip_address, last_attempt_at DESC);
CREATE INDEX IF NOT EXISTS idx_rate_limit_cleanup ON rate_limit_logs(last_attempt_at);

------------------------------------------------
----              [TRIGGERS]                ----
------------------------------------------------

-----------------[SHORT CODE]-------------------
-- Cria automaticamente um short code para uma nova url
CREATE OR REPLACE FUNCTION auto_generate_short_code()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.short_code IS NULL THEN
        NEW.short_code := generate_short_code();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_auto_short_code
BEFORE INSERT ON urls
FOR EACH ROW
EXECUTE FUNCTION auto_generate_short_code();
------------------------------------------------


----------------[LOGIN ATTEMPTS]----------------

-- Cria um novo registro em user_login_attemps
CREATE OR REPLACE FUNCTION create_user_login_attempt()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_login_attempts (user_id)
    VALUES (NEW.id)
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'trg_create_user_login_attempt'
    ) THEN
        CREATE TRIGGER trg_create_user_login_attempt
        AFTER INSERT ON users
        FOR EACH ROW
        EXECUTE FUNCTION create_user_login_attempt();
    END IF;
END$$;
------------------------------------------------