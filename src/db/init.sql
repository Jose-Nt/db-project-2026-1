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

-- ==========================================
-- INSERTS FOR DEMONSTRATION
-- ==========================================

INSERT INTO usuario (cpf, iddepartamento, idtipo_usuario, nome, data_nasc, senha) VALUES
('11111111111', 1, 1, 'Joao Aluno Teste', '2000-01-01', 'senha123'),
('22222222222', 3, 2, 'Maria Servidora Teste', '1985-05-10', 'senha456');

INSERT INTO endereco (referencia, latitude, longitude) VALUES
('Perto do ICC Norte', -15.7630, -47.8710),
('Em frente a BCE', -15.7615, -47.8725),
('Ao lado do RU', -15.7655, -47.8735),
('Na grama da FAU', -15.7600, -47.8690),
('No Patinódromo', -15.7670, -47.8700);

INSERT INTO local (idendereco, nome) VALUES
(1, 'Revisão de Cálculo I'),
(2, 'Palestra sobre IA'),
(3, 'Futsal Semanal'),
(4, 'Happy Hour da Prograd'),
(5, 'Grupo de Estudos de BD');

INSERT INTO evento (idusuario, idlocal, idpublico_alvo, idcategoria, titulo, data, horario, descricao) VALUES
('11111111111', 1, 1, 8, 'Revisão de Cálculo I', CURRENT_DATE, '14:00:00', 'Grupo para revisar a matéria para a P1 de Cálculo I.');

INSERT INTO evento (idusuario, idlocal, idpublico_alvo, idcategoria, titulo, data, horario, descricao) VALUES
('22222222222', 2, 4, 2, 'Palestra sobre IA', CURRENT_DATE, '10:00:00', 'Palestra com especialista sobre o futuro da Inteligência Artificial.');

INSERT INTO evento (idusuario, idlocal, idpublico_alvo, idcategoria, titulo, data, horario, descricao) VALUES
('11111111111', 3, 1, 6, 'Futsal Semanal', CURRENT_DATE + 1, '17:00:00', 'Futsal aberto para todos os níveis, venha jogar!');

INSERT INTO evento (idusuario, idlocal, idpublico_alvo, idcategoria, titulo, data, horario, descricao) VALUES
('22222222222', 4, 2, 1, 'Happy Hour da Prograd', CURRENT_DATE + 2, '18:00:00', 'Confraternização dos servidores da Prograd.');

INSERT INTO evento (idusuario, idlocal, idpublico_alvo, idcategoria, titulo, data, horario, descricao) VALUES
('11111111111', 5, 1, 8, 'Grupo de Estudos de BD', CURRENT_DATE, '16:00:00', 'Vamos nos juntar para estudar para o projeto de Banco de Dados.');