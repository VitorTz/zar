------------------------------------------------
----         [TzHar - Url Shortener]        ----
----              SCHEMA V1.0               ----
------------------------------------------------

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

------------------[URL CLICKS]------------------
-- Função para incrementar clicks atomicamente
CREATE OR REPLACE FUNCTION increment_url_clicks(p_url_id BIGINT)
RETURNS void AS $$
BEGIN
    UPDATE urls
    SET 
        clicks = clicks + 1,
        last_clicked_at = CURRENT_TIMESTAMP
    WHERE id = p_url_id;    
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
----               [TABLES]                 ----
------------------------------------------------

--------------------[USERS]---------------------
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


-------------[USER SESSIONS TOKENS]--------------
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


-------------[USER LOGIN ATTEMPTS]--------------
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


-----------------[DOMAINS URL]------------------
CREATE TABLE IF NOT EXISTS domains (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    url TEXT NOT NULL,
    url_hash BYTEA NOT NULL,
    is_secure BOOLEAN DEFAULT TRUE,
    CONSTRAINT chk_url CHECK (url ~ '^(https?://)([A-Za-z0-9-]+\.)+[A-Za-z]{2,}(/.*)?$'),    
    CONSTRAINT domains_unique_url_hash UNIQUE (url_hash)
);
CREATE INDEX IF NOT EXISTS idx_domains_url_hash ON domains USING hash(url_hash);


---------------------[URLS]----------------------
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
CREATE INDEX IF NOT EXISTS idx_urls_original_url_hash ON urls USING hash(original_url_hash);
CREATE INDEX IF NOT EXISTS idx_urls_created_at ON urls(created_at DESC) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_expires_at ON urls(expires_at) WHERE expires_at IS NOT NULL AND is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_clicks ON urls(clicks DESC) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_timestamps ON urls(created_at DESC, last_clicked_at DESC) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_active_clicks ON urls(id, clicks) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_domain_id ON urls(domain_id);


------------------[USER URLS]-------------------
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


-------------------[URL TAGS]-------------------
CREATE TABLE IF NOT EXISTS url_tags (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id UUID NOT NULL,
    name citext NOT NULL,
    color TEXT NOT NULL DEFAULT '#d8775a',
    descr TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT url_tags_unique_tag UNIQUE (user_id, name),
    CONSTRAINT chk_color_hex CHECK (color ~ '^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'),
    CONSTRAINT chk_name_length CHECK (length(name) BETWEEN 1 AND 256),
    FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_url_tags_user ON url_tags(user_id);
CREATE INDEX IF NOT EXISTS idx_url_tags_name_trgm ON url_tags  USING gin(name gin_trgm_ops);

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
CREATE INDEX IF NOT EXISTS idx_url_tag_relations_url ON url_tag_relations(url_id);
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
CREATE INDEX IF NOT EXISTS idx_url_analytics_url_date_country ON url_analytics(
    url_id, 
    clicked_at DESC, 
    country_code
) WHERE country_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_url_analytics_device_stats ON url_analytics(
    url_id, 
    device_type, 
    browser
) WHERE device_type IS NOT NULL;
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


------------------------------------------------
----         [MATERIALIZED VIEWS]           ----
------------------------------------------------

-------------------[DASHBOARD]------------------
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard AS
WITH 
-- Estatísticas de Usuários
user_stats AS (
    SELECT
        COUNT(*) as total_users,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as new_users_30d,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as new_users_7d,
        COUNT(*) FILTER (WHERE last_login_at >= NOW() - INTERVAL '30 days') as active_users_30d,
        COUNT(*) FILTER (WHERE last_login_at >= NOW() - INTERVAL '7 days') as active_users_7d,
        COUNT(*) FILTER (WHERE last_login_at >= NOW() - INTERVAL '1 day') as active_users_24h
    FROM users
),

-- Estatísticas de URLs
url_stats AS (
    SELECT
        COUNT(*) as total_urls,
        COUNT(*) FILTER (WHERE is_active = TRUE) as active_urls,
        COUNT(*) FILTER (WHERE is_active = FALSE) as inactive_urls,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as new_urls_30d,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as new_urls_7d,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 day') as new_urls_24h,
        COUNT(*) FILTER (WHERE expires_at IS NOT NULL AND expires_at < NOW()) as expired_urls,
        SUM(clicks) as total_clicks,
        SUM(clicks) FILTER (WHERE last_clicked_at >= NOW() - INTERVAL '30 days') as clicks_30d,
        SUM(clicks) FILTER (WHERE last_clicked_at >= NOW() - INTERVAL '7 days') as clicks_7d,
        SUM(clicks) FILTER (WHERE last_clicked_at >= NOW() - INTERVAL '1 day') as clicks_24h,
        AVG(clicks) FILTER (WHERE is_active = TRUE) as avg_clicks_per_url,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY clicks) as median_clicks
    FROM urls
),

-- Top 10 URLs mais clicadas
top_urls AS (
    SELECT
        jsonb_agg(
            jsonb_build_object(
                'short_code', short_code,
                'original_url', original_url,
                'clicks', clicks,
                'created_at', created_at
            ) ORDER BY clicks DESC
        ) as top_10_urls
    FROM (
        SELECT short_code, original_url, clicks, created_at
        FROM urls
        WHERE is_active = TRUE
        ORDER BY clicks DESC
        LIMIT 10
    ) t
),

-- Estatísticas de Analytics
analytics_stats AS (
    SELECT
        COUNT(*) as total_analytics_records,
        COUNT(*) FILTER (WHERE clicked_at >= NOW() - INTERVAL '30 days') as analytics_30d,
        COUNT(*) FILTER (WHERE clicked_at >= NOW() - INTERVAL '7 days') as analytics_7d,
        COUNT(*) FILTER (WHERE clicked_at >= NOW() - INTERVAL '1 day') as analytics_24h,
        COUNT(DISTINCT ip_address) as unique_visitors_all_time,
        COUNT(DISTINCT ip_address) FILTER (WHERE clicked_at >= NOW() - INTERVAL '30 days') as unique_visitors_30d,
        COUNT(DISTINCT country_code) FILTER (WHERE country_code IS NOT NULL) as countries_reached
    FROM url_analytics
),

-- Top 10 países por cliques
top_countries AS (
    SELECT
        jsonb_agg(
            jsonb_build_object(
                'country_code', country_code,
                'clicks', clicks,
                'percentage', ROUND((clicks * 100.0 / NULLIF(total_clicks, 0))::numeric, 2)
            ) ORDER BY clicks DESC
        ) as top_10_countries
    FROM (
        SELECT 
            country_code,
            COUNT(*) as clicks,
            SUM(COUNT(*)) OVER() as total_clicks
        FROM url_analytics
        WHERE country_code IS NOT NULL
        GROUP BY country_code
        ORDER BY clicks DESC
        LIMIT 10
    ) t
),

-- Estatísticas de dispositivos
device_stats AS (
    SELECT
        jsonb_build_object(
            'mobile', COUNT(*) FILTER (WHERE device_type = 'mobile'),
            'desktop', COUNT(*) FILTER (WHERE device_type = 'desktop'),
            'tablet', COUNT(*) FILTER (WHERE device_type = 'tablet'),
            'other', COUNT(*) FILTER (WHERE device_type NOT IN ('mobile', 'desktop', 'tablet') OR device_type IS NULL)
        ) as device_breakdown,
        COUNT(*) as total_with_device_info
    FROM url_analytics
    WHERE clicked_at >= NOW() - INTERVAL '30 days'
),

-- Top 5 browsers
browser_stats AS (
    SELECT
        jsonb_agg(
            jsonb_build_object(
                'browser', browser,
                'count', count
            ) ORDER BY count DESC
        ) as top_5_browsers
    FROM (
        SELECT 
            COALESCE(browser, 'Unknown') as browser,
            COUNT(*) as count
        FROM url_analytics
        WHERE clicked_at >= NOW() - INTERVAL '30 days'
          AND browser IS NOT NULL
        GROUP BY browser
        ORDER BY count DESC
        LIMIT 5
    ) t
),

-- Estatísticas de tags (COMPLETAMENTE CORRIGIDA)
tag_stats AS (
    WITH tag_usage AS (
        SELECT
            tag_id,
            COUNT(*) as usage_count
        FROM url_tag_relations
        GROUP BY tag_id
    ),
    url_counts AS (
        SELECT 
            url_id, 
            COUNT(*) as tag_count 
        FROM url_tag_relations 
        GROUP BY url_id
    ),
    top_tags_data AS (
        SELECT
            ut.id,
            ut.name,
            COALESCE(tu.usage_count, 0) as usage_count
        FROM url_tags ut
        LEFT JOIN tag_usage tu ON ut.id = tu.tag_id
        ORDER BY COALESCE(tu.usage_count, 0) DESC
        LIMIT 10
    )
    SELECT
        (SELECT COUNT(*) FROM url_tags) as total_tags,
        (SELECT COUNT(DISTINCT url_id) FROM url_tag_relations) as urls_with_tags,
        (SELECT COALESCE(AVG(tag_count), 0) FROM url_counts) as avg_tags_per_url,
        (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'name', name,
                    'usage_count', usage_count
                )
            )
            FROM top_tags_data
        ) as top_10_tags
),

-- Domínios mais populares (CORRIGIDO)
domain_stats AS (
    WITH domain_rankings AS (
        SELECT 
            u.domain_id,
            COUNT(*) as url_count,
            SUM(u.clicks) as total_clicks
        FROM urls u
        WHERE u.is_active = TRUE
        GROUP BY u.domain_id
        ORDER BY COUNT(*) DESC
        LIMIT 10
    )
    SELECT
        (SELECT COUNT(*) FROM domains) as total_domains,
        COALESCE(
            jsonb_agg(
                jsonb_build_object(
                    'domain', d.url,
                    'url_count', dr.url_count,
                    'total_clicks', dr.total_clicks
                ) ORDER BY dr.url_count DESC
            ),
            '[]'::jsonb
        ) as top_10_domains
    FROM domain_rankings dr
    INNER JOIN domains d ON dr.domain_id = d.id
),

-- Crescimento diário (últimos 30 dias)
daily_growth AS (
    SELECT
        jsonb_agg(
            jsonb_build_object(
                'date', daily_data.date::date,
                'new_urls', daily_data.new_urls,
                'new_users', daily_data.new_users,
                'clicks', daily_data.clicks
            ) ORDER BY daily_data.date
        ) as last_30_days
    FROM (
        SELECT 
            d.date::date as date,
            COALESCE(u.new_urls, 0) as new_urls,
            COALESCE(us.new_users, 0) as new_users,
            COALESCE(a.clicks, 0) as clicks
        FROM generate_series(
            CURRENT_DATE - INTERVAL '29 days',
            CURRENT_DATE,
            INTERVAL '1 day'
        ) AS d(date)
        LEFT JOIN (
            SELECT DATE(created_at) as date, COUNT(*) as new_urls
            FROM urls
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
        ) u ON d.date::date = u.date
        LEFT JOIN (
            SELECT DATE(created_at) as date, COUNT(*) as new_users
            FROM users
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
        ) us ON d.date::date = us.date
        LEFT JOIN (
            SELECT DATE(clicked_at) as date, COUNT(*) as clicks
            FROM url_analytics
            WHERE clicked_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(clicked_at)
        ) a ON d.date::date = a.date
    ) daily_data
),

-- Estatísticas de sessões ativas
session_stats AS (
    SELECT
        COUNT(*) as total_sessions,
        COUNT(*) FILTER (WHERE revoked = FALSE) as active_sessions,
        COUNT(*) FILTER (WHERE revoked = TRUE) as revoked_sessions,
        COUNT(DISTINCT user_id) FILTER (WHERE revoked = FALSE) as users_with_active_sessions,
        COALESCE(AVG(EXTRACT(EPOCH FROM (last_used_at - issued_at))/3600), 0) as avg_session_duration_hours
    FROM user_session_tokens
    WHERE expires_at > NOW()
),

-- Taxa de conversão (URLs criadas vs. URLs clicadas)
conversion_stats AS (
    SELECT
        COUNT(*) FILTER (WHERE clicks > 0) as urls_with_clicks,
        COUNT(*) as total_urls,
        COALESCE(ROUND((COUNT(*) FILTER (WHERE clicks > 0) * 100.0 / NULLIF(COUNT(*), 0))::numeric, 2), 0) as conversion_rate,
        COALESCE(ROUND((COUNT(*) FILTER (WHERE clicks >= 10) * 100.0 / NULLIF(COUNT(*), 0))::numeric, 2), 0) as urls_with_10plus_clicks_rate
    FROM urls
    WHERE is_active = TRUE
      AND created_at >= NOW() - INTERVAL '30 days'
)

-- Agregação final
SELECT
    NOW() as last_updated,
    
    -- Usuários
    jsonb_build_object(
        'total', us.total_users,
        'new_30d', us.new_users_30d,
        'new_7d', us.new_users_7d,
        'active_30d', us.active_users_30d,
        'active_7d', us.active_users_7d,
        'active_24h', us.active_users_24h
    ) as users,
    
    -- URLs
    jsonb_build_object(
        'total', url.total_urls,
        'active', url.active_urls,
        'inactive', url.inactive_urls,
        'expired', url.expired_urls,
        'new_30d', url.new_urls_30d,
        'new_7d', url.new_urls_7d,
        'new_24h', url.new_urls_24h,
        'avg_clicks', ROUND(COALESCE(url.avg_clicks_per_url, 0)::numeric, 2),
        'median_clicks', COALESCE(url.median_clicks, 0)
    ) as urls,
    
    -- Cliques
    jsonb_build_object(
        'total', COALESCE(url.total_clicks, 0),
        'last_30d', COALESCE(url.clicks_30d, 0),
        'last_7d', COALESCE(url.clicks_7d, 0),
        'last_24h', COALESCE(url.clicks_24h, 0)
    ) as clicks,
    
    -- Analytics
    jsonb_build_object(
        'total_records', an.total_analytics_records,
        'records_30d', an.analytics_30d,
        'records_7d', an.analytics_7d,
        'records_24h', an.analytics_24h,
        'unique_visitors_all_time', an.unique_visitors_all_time,
        'unique_visitors_30d', an.unique_visitors_30d,
        'countries_reached', an.countries_reached
    ) as analytics,
    
    -- Top URLs
    COALESCE(tu.top_10_urls, '[]'::jsonb) as top_urls,
    
    -- Geografia
    jsonb_build_object(
        'top_countries', COALESCE(tc.top_10_countries, '[]'::jsonb)
    ) as geography,
    
    -- Dispositivos e Browsers
    jsonb_build_object(
        'devices', COALESCE(ds.device_breakdown, '{"mobile":0,"desktop":0,"tablet":0,"other":0}'::jsonb),
        'browsers', COALESCE(bs.top_5_browsers, '[]'::jsonb)
    ) as client_info,
    
    -- Tags
    jsonb_build_object(
        'total_tags', COALESCE(ts.total_tags, 0),
        'urls_with_tags', COALESCE(ts.urls_with_tags, 0),
        'avg_tags_per_url', ROUND(COALESCE(ts.avg_tags_per_url, 0)::numeric, 2),
        'top_tags', COALESCE(ts.top_10_tags, '[]'::jsonb)
    ) as tags,
    
    -- Domínios
    jsonb_build_object(
        'total_domains', COALESCE(dm.total_domains, 0),
        'top_domains', COALESCE(dm.top_10_domains, '[]'::jsonb)
    ) as domains,
    
    -- Crescimento diário
    COALESCE(dg.last_30_days, '[]'::jsonb) as daily_growth,
    
    -- Sessões
    jsonb_build_object(
        'total', ss.total_sessions,
        'active', ss.active_sessions,
        'revoked', ss.revoked_sessions,
        'users_with_sessions', ss.users_with_active_sessions,
        'avg_duration_hours', ROUND(COALESCE(ss.avg_session_duration_hours, 0)::numeric, 2)
    ) as sessions,
    
    -- Conversão
    jsonb_build_object(
        'urls_with_clicks', cs.urls_with_clicks,
        'total_urls_30d', cs.total_urls,
        'conversion_rate', cs.conversion_rate,
        'urls_10plus_rate', cs.urls_with_10plus_clicks_rate
    ) as conversion

FROM user_stats us
CROSS JOIN url_stats url
CROSS JOIN analytics_stats an
CROSS JOIN top_urls tu
CROSS JOIN top_countries tc
CROSS JOIN device_stats ds
CROSS JOIN browser_stats bs
CROSS JOIN tag_stats ts
CROSS JOIN domain_stats dm
CROSS JOIN daily_growth dg
CROSS JOIN session_stats ss
CROSS JOIN conversion_stats cs;

-- Índices para a materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_dashboard_last_updated ON mv_dashboard(last_updated);

-- Função para refresh automático
CREATE OR REPLACE FUNCTION refresh_dashboard_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard;
END;
$$ LANGUAGE plpgsql;


SELECT refresh_dashboard_stats();
