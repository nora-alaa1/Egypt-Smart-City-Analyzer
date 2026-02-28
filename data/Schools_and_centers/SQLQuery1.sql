CREATE TABLE City(
	City_ID INT PRIMARY KEY IDENTITY(1,1),
	City_Name VARCHAR(50),
)

CREATE TABLE School(
	School_ID INT PRIMARY KEY IDENTITY(1,1),
	School_NAME VARCHAR(100),
	City_ID INT,
	Type_of_School VARCHAR(50),
	students_count INT
)


CREATE TABLE Centers (
    center_id INT PRIMARY KEY IDENTITY(1,1),
	Center_Name varchar(100),
    City_ID INT,
    avg_price INT,
    students_count INT,
);


INSERT INTO City (City_Name) 
VALUES
('Sidi Gaber'),
('El Montazah'),
('El Mandara'),
('Kafr Abdu'),
('Borg El Arab'),
('Gleem'),
('Sidi Bishr'),
('Miami'),
('El Asafra'),
('Abu Youssef'),
('Bab El Hadid'),
('El Gomrok (Bahary)'),
('El Agamy'),
('Moharram Bek'),
('Louran'),
('Camp Shezar'),
('Mahatet El Raml'),
('Abis'),
('Abu Qir'),
('Ard El Sobhiya')

SELECT * FROM City

INSERT INTO School (School_NAME , City_ID, Type_of_School ,students_count)
VALUES
('New Sidi Gaber Language School',1 ,'Private', 1200),
('Sidi Gaber Primary School',1, 'Public', 800),
('Sidi Gaber Preparatory School',1, 'Public', 600),
('Sidi Gaber Secondary School',1, 'Public', 700),

('Pioneers International School',2, 'International', 900),
('Grand Language School',2, 'Private', 750),
('El Montazah Primary School',2, 'Public', 500),

('El Mandara International School',3, 'International', 650),
('EELS Schools',3, 'Private', 700),
('Mandara Secondary School',3, 'Public', 550),

('Schutz American School',4, 'International', 1000),
('Franciscan Sisters School',4, 'Private', 600),
('Taha Hussein Secondary School for Girls',4, 'Public', 400),

('Harvest International School',5, 'International', 850),
('Al Qayrawan Private School',5, 'Private', 500),
('Borg El Arab Primary School',5, 'Public', 450),

('Badr Gleem Private School',6, 'Private', 550),
('New Generation International Schools',6, 'International', 950),

('Ramses Private School',7, 'Private', 700),
('Sidi Bishr International School',7, 'International', 800),
('Aly Ibn Abi Taleb Preparatory School',7, 'Public', 500),

('Brilliance Academy Miami',8, 'International', 900),
('Miami College',8, 'Private', 650),

('Abou Youssef Private School',10, 'Private', 500),
('Wadi El Melouk Language School',10, 'Private', 600),
('Abu Youssef Primary School',10, 'Public', 350),

('El Bab El Hadid Primary School',11, 'Public', 300),
('Technical Institute for Science & Technology',11, 'Public', 400),

('Ahmed Lotfy El Sayed Experimental School',12, 'Public', 600),
('El Gomrok Primary School',12, 'Public', 350),

('El Hayah Private Schools',13, 'Private', 700),
('Alex West Language Schools',13, 'Private', 800),
('Qasr El Farida Educational Academy',13, 'Private', 650),

('El Thabat Private Primary School',14, 'Private', 500),
('Ibn Anas Experimental Language School',14, 'Public', 600),
('Moharram Bek Secondary School',14, 'Public', 450),

('Lycée Molière d’Alexandrie',15, 'International', 700),
('International British School of Alexandria',15, 'International', 950),
('El Nasr Girls College (EGC)',15, 'Private', 1200),

('Camp Shezar Primary School',16, 'Public', 400),

('El Raml School',17, 'Public', 600),

('Alexandria International Academy (AIA)',18, 'International', 850),
('Salahaldin International School (SIS)',18, 'International', 900),

('Franciscan Fathers Abu Qir School',19, 'Private', 500),
('Yathreb Private School Abu Qir',19, 'Private', 450),
('Abu Qir Primary School',19, 'Public', 350),

('Ard El Sobhiya Primary School',20, 'Public', 300);

SELECT * FROM School

INSERT INTO Centers (Center_Name, City_ID, avg_price, students_count)
VALUES
('Future Language Center', 1, 250, 400),   
('Elite Academy', 2, 300, 350),            
('Mandara Learning Hub', 3, 200, 280),     
('Kafr Abdu Training Center', 4, 350, 500),
('Borg El Arab Education Center', 5, 180, 250), 
('Gleem Academy', 6, 270, 320),            
('Sidi Bishr Center', 7, 220, 300),        
('Miami Study Center', 8, 250, 400),       
('Asafra Academy', 9, 230, 280),           
('Abu Youssef Center', 10, 200, 260),      
('Bab El Hadid Center', 11, 180, 200),     
('El Gomrok Academy', 12, 210, 240),       
('Agamy Learning Center', 13, 220, 300),   
('Moharram Bek Center', 14, 250, 350),     
('Louran Academy', 15, 400, 600),          
('Camp Shezar Center', 16, 200, 220),      
('El Raml Academy', 17, 230, 280),        
('Abis International Center', 18, 500, 700),
('Abu Qir Center', 19, 220, 300),          
('Sobhiya Study Hub', 20, 180, 200);     

SELECT * FROM Centers