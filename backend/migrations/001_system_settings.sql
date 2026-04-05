-- Configurações globais (singleton). Id fixo = 1.
-- Seguro em banco existente: CREATE IF NOT EXISTS + insert só se faltar linha.

CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER NOT NULL PRIMARY KEY,
    initial_ranking INTEGER NOT NULL
);

-- Opcional: valor inicial persistido (alinhado ao fallback da aplicação quando não há linha).
INSERT INTO system_settings (id, initial_ranking)
SELECT 1, 1000
WHERE NOT EXISTS (SELECT 1 FROM system_settings WHERE id = 1);
