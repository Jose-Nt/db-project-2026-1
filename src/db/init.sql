-- ==========================================
-- CRIAÇÃO DE TABELAS
-- ==========================================

CREATE TABLE usuario 
( 
 cpf CHAR(11) PRIMARY KEY,  
 iddepartamento INT NOT NULL,  
 idtipo_usuario INT NOT NULL,  
 nome VARCHAR NOT NULL,  
 data_nasc DATE NOT NULL,
 senha VARCHAR NOT NULL,
 foto BYTEA NOT NULL
); 

CREATE TABLE local 
( 
 id_local SERIAL PRIMARY KEY,  
 idendereco INT NOT NULL,  
 nome VARCHAR NOT NULL
); 

CREATE TABLE evento 
( 
 id_evento SERIAL PRIMARY KEY,  
 idusuario CHAR(11) NOT NULL,  
 idlocal INT NOT NULL,  
 idpublico_alvo INT NOT NULL,  
 idcategoria INT NOT NULL,  
 titulo VARCHAR NOT NULL,  
 data DATE NOT NULL,  
 horario TIME NOT NULL,  
 descricao VARCHAR NOT NULL,
 limite_participantes INT NOT NULL DEFAULT 50
); 

CREATE TABLE participacao 
( 
 idusuario CHAR(11),  
 idevento INT,  
 data_inscricao DATE NOT NULL,
	
 PRIMARY KEY (idusuario, idevento)
); 

CREATE TABLE comentario 
( 
 id_comentario SERIAL PRIMARY KEY,  
 idusuario CHAR(11) NOT NULL,  
 idevento INT NOT NULL,  
 texto VARCHAR NOT NULL  
); 

CREATE TABLE categoria 
( 
 id_categoria SERIAL PRIMARY KEY,  
 nome VARCHAR NOT NULL  
); 

CREATE TABLE departamento 
( 
 id_departamento SERIAL PRIMARY KEY,  
 nome VARCHAR NOT NULL  
); 

CREATE TABLE endereco 
( 
 id_endereco SERIAL PRIMARY KEY,  
 referencia VARCHAR NOT NULL,  
 latitude FLOAT NOT NULL,  
 longitude FLOAT NOT NULL  
); 

CREATE TABLE publico_alvo 
( 
 id_publico SERIAL PRIMARY KEY,  
 nome VARCHAR NOT NULL  
); 

CREATE TABLE tipo_usuario 
( 
 id_tipo_usuario SERIAL PRIMARY KEY,  
 nome VARCHAR NOT NULL  
); 


-- ==========================================
-- ADIÇÃO DE CONSTRAINTS
-- ==========================================

ALTER TABLE usuario
ADD CONSTRAINT fk_usuario_departamento
FOREIGN KEY (iddepartamento)
REFERENCES departamento (id_departamento);

ALTER TABLE usuario
ADD CONSTRAINT fk_usuario_tipo_usuario
FOREIGN KEY (idtipo_usuario)
REFERENCES tipo_usuario (id_tipo_usuario);

ALTER TABLE local
ADD CONSTRAINT fk_local_endereco
FOREIGN KEY (idendereco)
REFERENCES endereco (id_endereco);

ALTER TABLE evento
ADD CONSTRAINT fk_evento_usuario
FOREIGN KEY (idusuario)
REFERENCES usuario (cpf);

ALTER TABLE evento
ADD CONSTRAINT fk_evento_local
FOREIGN KEY (idlocal)
REFERENCES local (id_local);

ALTER TABLE evento
ADD CONSTRAINT fk_evento_publico_alvo
FOREIGN KEY (idpublico_alvo)
REFERENCES publico_alvo (id_publico);

ALTER TABLE evento
ADD CONSTRAINT fk_evento_categoria
FOREIGN KEY (idcategoria)
REFERENCES categoria (id_categoria);

ALTER TABLE participacao
ADD CONSTRAINT fk_participacao_usuario
FOREIGN KEY (idusuario)
REFERENCES usuario (cpf);

ALTER TABLE participacao
ADD CONSTRAINT fk_participacao_evento
FOREIGN KEY (idevento)
REFERENCES evento (id_evento);

ALTER TABLE comentario
ADD CONSTRAINT fk_comentario_usuario
FOREIGN KEY (idusuario)
REFERENCES usuario (cpf);

ALTER TABLE comentario
ADD CONSTRAINT fk_comentario_evento
FOREIGN KEY (idevento)
REFERENCES evento (id_evento);


-- ==========================================
-- VIEWS
-- ==========================================

CREATE OR REPLACE VIEW vw_eventos_detalhados AS
SELECT
    e.id_evento,
    e.titulo,
    e.descricao,
    e.data,
    e.horario,
    e.idusuario,
    e.limite_participantes,
    u.nome AS nome_organizador,
    e.idcategoria,
    cat.nome AS categoria_nome,
    e.idpublico_alvo,
    pub.nome AS publico_alvo_nome,
    e.idlocal,
    l.idendereco,
    en.referencia,
    en.latitude,
    en.longitude,
    (SELECT COUNT(*) FROM participacao p WHERE p.idevento = e.id_evento) AS participantes
FROM evento e
JOIN usuario u ON e.idusuario = u.cpf
JOIN categoria cat ON e.idcategoria = cat.id_categoria
JOIN publico_alvo pub ON e.idpublico_alvo = pub.id_publico
JOIN local l ON e.idlocal = l.id_local
JOIN endereco en ON l.idendereco = en.id_endereco;


-- ==========================================
-- PROCEDURES
-- ==========================================

CREATE OR REPLACE PROCEDURE create_full_event(
    p_titulo VARCHAR,
    p_descricao VARCHAR,
    p_referencia VARCHAR,
    p_latitude FLOAT,
    p_longitude FLOAT,
    p_horario TIME,
    p_data DATE,
    p_id_usuario CHAR(11),
    p_id_publico_alvo INT,
    p_id_categoria INT,
    p_limite_participantes INT
) LANGUAGE plpgsql AS $$
DECLARE
    v_id_endereco INT;
    v_id_local INT;
    v_id_evento INT;
BEGIN
    INSERT INTO endereco (referencia, latitude, longitude)
    VALUES (p_referencia, p_latitude, p_longitude) RETURNING id_endereco INTO v_id_endereco;

    INSERT INTO local (idendereco, nome)
    VALUES (v_id_endereco, p_titulo) RETURNING id_local INTO v_id_local;

    -- Cria o evento e pega o ID gerado
    INSERT INTO evento (idusuario, idlocal, idpublico_alvo, idcategoria, titulo, data, horario, descricao, limite_participantes)
    VALUES (p_id_usuario, v_id_local, p_id_publico_alvo, p_id_categoria, p_titulo, p_data, p_horario, p_descricao, p_limite_participantes)
    RETURNING id_evento INTO v_id_evento;

    -- MÁGICA AQUI: O criador do evento é inserido automaticamente como o primeiro participante!
    INSERT INTO participacao (idusuario, idevento, data_inscricao)
    VALUES (p_id_usuario, v_id_evento, CURRENT_DATE);
END;
$$;


-- ==========================================
-- TRIGGERS
-- ==========================================

CREATE OR REPLACE FUNCTION check_event_date()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.data < CURRENT_DATE THEN
        RAISE EXCEPTION 'Não é possível criar ou atualizar um evento para uma data no passado.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_check_event_date
BEFORE INSERT OR UPDATE ON evento
FOR EACH ROW
EXECUTE FUNCTION check_event_date();


-- ==========================================
-- INSERTS EM TABELAS ESTÁTICAS
-- ==========================================

INSERT INTO publico_alvo (nome) VALUES
('Estudantes'),
('Servidores'),
('Comunidade externa'),
('Comunidade acadêmica'),
('Livre');

INSERT INTO categoria (nome) VALUES
('HH'),
('Carona'),
('Esporte'),
('Palestra'),
('Coffee Break'),
('Workshop'),
('Game'),
('Livre');

INSERT INTO departamento (nome) VALUES
('Instituto de Ciências Exatas'),
('Instituto de Artes'),
('Instituto de Ciência Política'),
('Instituto de Ciências Biológicas'),
('Instituto de Ciências Humanas'),
('Instituto de Ciências Sociais'),
('Instituto de Física'),
('Instituto de Geociências'),
('Instituto de Letras'),
('Instituto de Psicologia'),
('Instituto de Química'),
('Instituto de Relações Internacionais');

INSERT INTO tipo_usuario (nome) VALUES
('Aluno Graduação'),
('Aluno Pós-Graduação'),
('Professor'),
('Servidor'),
('Comunidade externa');


-- ==========================================
-- USUÁRIOS DE EXEMPLO
-- ==========================================

INSERT INTO usuario (cpf, iddepartamento, idtipo_usuario, nome, data_nasc, senha, foto) VALUES
('11111111111', 1, 1, 'Joao Souza', '2000-01-01', 'senha123', E'\\000'),
('22222222222', 4, 3, 'Ana Lima', '1995-05-10', 'senha123', E'\\000'),
('33333333333', 1, 2, 'José Fonseca', '2000-05-10', 'senha123', E'\\000'),
('44444444444', 2, 4, 'Maria Silva', '1985-05-10', 'senha123', E'\\000'),
('55555555555', 5, 5, 'Carlos Rocha', '1975-05-10', 'senha123', E'\\000'),
('66666666666', 3, 1, 'Ricardo Rocha', '1975-05-10', 'senha123', E'\\000'),
('77777777777', 4, 1, 'Julia Silva', '1975-05-10', 'senha123', E'\\000'),
('88888888888', 1, 1, 'Samara Feitosa', '1975-05-10', 'senha123', E'\\000'),
('99999999999', 7, 5, 'Isabela Souza', '1975-05-10', 'senha123', E'\\000');