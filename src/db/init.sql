-- ==========================================
-- CREATE TABLES
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
-- CONSTRAINTS
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
-- INSERTS IN STATIC TABLES
-- ==========================================

INSERT INTO publico_alvo (nome) VALUES
('Estudantes'),
('Servidores'),
('Comunidade externa'),
('Comunidade acadêmica'),
('Geral');

INSERT INTO categoria (nome) VALUES
('HH'),
('Palestra'),
('Workshop'),
('Carona'),
('Coffee Break'),
('Esporte'),
('Game'),
('Geral');

INSERT INTO departamento (nome) VALUES
('CIC'),
('MAT'),
('FT'),
('IF'),
('IB');

INSERT INTO tipo_usuario (nome) VALUES
('Aluno'),
('Servidor'),
('Comunidade externa');

INSERT INTO endereco (referencia, latitude, longitude) VALUES
('A definir', -15.7601, -47.8701), -- ICC Norte
('A definir', -15.7602, -47.8702), -- ICC Sul
('A definir', -15.7603, -47.8703), -- ICC Centro
('A definir', -15.7604, -47.8704), -- Arena
('A definir', -15.7605, -47.8705), -- Estacionamento CEUBinho
('A definir', -15.7606, -47.8706), -- Estacionamento UDFinho
('A definir', -15.7607, -47.8707), -- IB
('A definir', -15.7608, -47.8708), -- PJC
('A definir', -15.7609, -47.8709), -- PAT
('A definir', -15.7610, -47.8710), -- BSAS
('A definir', -15.7611, -47.8711); -- BSAS (segunda entrada)

INSERT INTO local (idendereco, nome) VALUES
(1, 'ICC Norte'),
(2, 'ICC Sul'),
(3, 'ICC Centro'),
(4, 'Arena'),
(5, 'Estacionamento CEUBinho'),
(6, 'Estacionamento UDFinho'),
(7, 'IB'),
(8, 'PJC'),
(9, 'PAT'),
(10, 'BSAS'),
(11, 'BSAS');