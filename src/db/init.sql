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
 senha VARCHAR NOT NULL
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
 descricao VARCHAR NOT NULL  
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
-- PROCEDURES / FUNCTIONS
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
    p_id_categoria INT
) LANGUAGE plpgsql AS $$
DECLARE
    v_id_endereco INT;
    v_id_local INT;
BEGIN
    INSERT INTO endereco (referencia, latitude, longitude)
    VALUES (p_referencia, p_latitude, p_longitude) RETURNING id_endereco INTO v_id_endereco;

    INSERT INTO local (idendereco, nome)
    VALUES (v_id_endereco, p_titulo) RETURNING id_local INTO v_id_local;

    INSERT INTO evento (idusuario, idlocal, idpublico_alvo, idcategoria, titulo, data, horario, descricao)
    VALUES (p_id_usuario, v_id_local, p_id_publico_alvo, p_id_categoria, p_titulo, p_data, p_horario, p_descricao);
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

    IF NEW.data = CURRENT_DATE AND NEW.horario < CURRENT_TIME THEN
        RAISE EXCEPTION 'Não é possível criar ou atualizar um evento para um horário que já passou hoje.';
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

INSERT INTO usuario (cpf, iddepartamento, idtipo_usuario, nome, data_nasc, senha) VALUES
('11111111111', 1, 1, 'Joao Souza', '2000-01-01', 'senha123'),
('22222222222', 4, 3, 'Ana Lima', '1995-05-10', 'senha123'),
('33333333333', 1, 2, 'José Fonseca', '2000-05-10', 'senha123'),
('44444444444', 2, 4, 'Maria Silva', '1985-05-10', 'senha123'),
('55555555555', 5, 5, 'Carlos Rocha', '1975-05-10', 'senha123'),
('66666666666', 3, 1, 'Ricardo Rocha', '1975-05-10', 'senha123'),
('77777777777', 4, 1, 'Julia Silva', '1975-05-10', 'senha123'),
('88888888888', 1, 1, 'Samara Feitosa', '1975-05-10', 'senha123'),
('99999999999', 7, 5, 'Isabela Souza', '1975-05-10', 'senha123');


-- ==========================================
-- EVENTOS DE EXEMPLO
-- ==========================================

CALL create_full_event(
    'Carona para a rodoviária',                                 -- p_titulo
    'Vou com um fiat argo branco, três vagas no carro',         -- p_descricao
    'Entrada do ICC norte',                                     -- p_referencia
    -15.7625,                                                   -- p_latitude
    -47.8707,                                                   -- p_longitude
    '19:00:00',                                                 -- p_horario
    CURRENT_DATE,                                               -- p_data
    '11111111111',                                              -- p_id_usuario
    4,                                                          -- p_id_publico_alvo (Comunidade acadêmica)
    2                                                           -- p_id_categoria (Carona)
);

CALL create_full_event(
    'Carona para Taguatinga',                                                       
    'Indo para Taguatinga, vou com um vw gol cinza, 4 vagas no carro ainda.',
    'Início do estacionamento do BSAN',                                                           
    -15.7574,                                                  
    -47.8707,                                                 
    '19:00:00',                                                 
    CURRENT_DATE,                                               
    '22222222222',                                             
    4,                                                          
    2                                                           
);

CALL create_full_event(
    'HH da Aplicada',                               
    'HH da Aplicada, vai até às 21hrs. DJ ao vivo com funk anos 90!',        
    'Escadaria do ICC sul',                                    
    -15.7641,                                                   
    -47.8684,                                               
    '18:00:00',                                                 
    CURRENT_DATE,                                              
    '33333333333',                                              
    1,                                                          
    1                                                          
);

CALL create_full_event(
    'Vôlei',                               
    'Vôlei aqui para quem quiser participar, vai até às 18hrs. Não precisa trazer equipamento e nem ter experiência.',        
    'Grama à direita da escadaria do ICC norte, sentido BCE.',                                    
    -15.7626,                                                   
    -47.8692,                                               
    '16:00:00',                                                 
    CURRENT_DATE,                                              
    '44444444444',                                              
    5,                                                          
    3                                                         
);

CALL create_full_event(
    'Coffee Break no IQ',                              
    'Vai rolar um coffee break no IQ depois de um evento sobre química quântica. Só chegar no final do evento!',
    'Térreo do IQ, à direita da entrada.',                                  
    -15.7686,                                                
    -47.8649,                                                  
    '20:00:00',                                              
    CURRENT_DATE,                                               
    '55555555555',                                            
    4,                                                         
    5                                                           
);

CALL create_full_event(
    'Bar pós prova de OAC',                              
    'Última prova do semestre, final da tortura. Quem quiser ir só aparecer',
    'Aqui no Mendes, mesma quadra do moes',                                  
    -15.7537,                                                
    -47.8813,                                                  
    '20:00:00',                                              
    CURRENT_DATE,                                               
    '44444444444',                                            
    4,                                                         
    1                                                          
);


-- ==========================================
-- COMENTÁRIOS DE EXEMPLO
-- ==========================================

INSERT INTO comentario (idusuario, idevento, texto) VALUES
('55555555555', 1, 'Opa, ainda tem vaga? Preciso ir pra rodoviária também!'),
('11111111111', 1, 'Tem sim, só duas pessoas confirmaram presença...'), 
('11111111111', 3, 'A reitoria n tinha proibido dentro do ICC?'), 
('33333333333', 3, 'Sim, porém liberaram de novo!'), 
('44444444444', 4, 'Legal!! É semanal? Ou vai ter só esse agr?'),
('44444444444', 2, 'Vão ir até qual parte de taguatinga?'),
('22222222222', 2, 'Vamos chegar até tag centro mais ou menos'),
('44444444444', 2, 'Ahh blz, vou ir tbm então'),
('44444444444', 4, 'A gente pretende que seja semanal ou mensal pelo menos. Mas vai depender de quantas pessoas vão aparecer');


-- ==========================================
-- PARTICIPAÇÕES DE EXEMPLO
-- ==========================================

INSERT INTO participacao (idusuario, idevento, data_inscricao) VALUES
('22222222222', 1, CURRENT_DATE),
('33333333333', 1, CURRENT_DATE),
('11111111111', 3, CURRENT_DATE),
('22222222222', 3, CURRENT_DATE),
('55555555555', 4, CURRENT_DATE),
('77777777777', 4, CURRENT_DATE),
('88888888888', 4, CURRENT_DATE),
('99999999999', 4, CURRENT_DATE),
('66666666666', 4, CURRENT_DATE);