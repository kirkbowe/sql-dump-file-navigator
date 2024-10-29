-- MySQL dump 10.13  Distrib 8.0.23, for Linux (x86_64)
--
-- Host: localhost    Database: dvd_collection
-- ------------------------------------------------------
-- Server version	8.0.23

--
-- Table structure for table `movies`
--

CREATE TABLE `movies` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `genre` varchar(100) NOT NULL,
  `release_year` int NOT NULL,
  `director` varchar(255) NOT NULL,
  `rating` float NOT NULL,
  `duration` int NOT NULL,
  `language` varchar(100) NOT NULL,
  `country` varchar(100) NOT NULL,
  `budget` bigint NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `movies`
--

INSERT INTO `movies` (`id`, `title`, `genre`, `release_year`, `director`, `rating`, `duration`, `language`, `country`, `budget`) VALUES
(1, 'The Shawshank Redemption', 'Drama', 1994, 'Frank Darabont', 9.3, 142, 'English', 'USA', 25000000),
(2, 'The Godfather', 'Crime', 1972, 'Francis Ford Coppola', 9.2, 175, 'English', 'USA', 6000000),
(3, 'The Dark Knight', 'Action', 2008, 'Christopher Nolan', 9.0, 152, 'English', 'USA', 185000000),
(4, 'Pulp Fiction', 'Crime', 1994, 'Quentin Tarantino', 8.9, 154, 'English', 'USA', 8000000),
(5, 'The Lord of the Rings: The Return of the King', 'Fantasy', 2003, 'Peter Jackson', 8.9, 201, 'English', 'New Zealand', 94000000),
(6, 'Forrest Gump', 'Drama', 1994, 'Robert Zemeckis', 8.8, 142, 'English', 'USA', 55000000),
(7, 'Inception', 'Sci-Fi', 2010, 'Christopher Nolan', 8.8, 148, 'English', 'USA', 160000000),
(8, 'Fight Club', 'Drama', 1999, 'David Fincher', 8.8, 139, 'English', 'USA', 63000000),
(9, 'The Matrix', 'Sci-Fi', 1999, 'Lana Wachowski, Lilly Wachowski', 8.7, 136, 'English', 'USA', 63000000),
(10, 'Goodfellas', 'Crime', 1990, 'Martin Scorsese', 8.7, 146, 'English', 'USA', 25000000),
(11, 'The Empire Strikes Back', 'Sci-Fi', 1980, 'Irvin Kershner', 8.7, 124, 'English', 'USA', 18000000),
(12, 'The Lord of the Rings: The Fellowship of the Ring', 'Fantasy', 2001, 'Peter Jackson', 8.8, 178, 'English', 'New Zealand', 93000000),
(13, 'Star Wars', 'Sci-Fi', 1977, 'George Lucas', 8.6, 121, 'English', 'USA', 11000000),
(14, 'The Lord of the Rings: The Two Towers', 'Fantasy', 2002, 'Peter Jackson', 8.7, 179, 'English', 'New Zealand', 94000000),
(15, 'Interstellar', 'Sci-Fi', 2014, 'Christopher Nolan', 8.6, 169, 'English', 'USA', 165000000),
(16, 'Parasite', 'Thriller', 2019, 'Bong Joon Ho', 8.6, 132, 'Korean', 'South Korea', 11400000),
(17, 'The Green Mile', 'Drama', 1999, 'Frank Darabont', 8.6, 189, 'English', 'USA', 60000000),
(18, 'Gladiator', 'Action', 2000, 'Ridley Scott', 8.5, 155, 'English', 'USA', 103000000),
(19, 'The Lion King', 'Animation', 1994, 'Roger Allers, Rob Minkoff', 8.5, 88, 'English', 'USA', 45000000),
(20, 'The Silence of the Lambs', 'Thriller', 1991, 'Jonathan Demme', 8.6, 118, 'English', 'USA', 19000000);

--
-- Table structure for table `actors`
--

CREATE TABLE `actors` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `birth_year` int NOT NULL,
  `nationality` varchar(100) NOT NULL,
  `awards` int NOT NULL,
  `debut_year` int NOT NULL,
  `height` float NOT NULL,
  `net_worth` bigint NOT NULL,
  `gender` varchar(10) NOT NULL,
  `active_years` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `actors`
--

INSERT INTO `actors` (`id`, `name`, `birth_year`, `nationality`, `awards`, `debut_year`, `height`, `net_worth`, `gender`, `active_years`) VALUES
(1, 'Morgan Freeman', 1937, 'American', 5, 1964, 1.88, 250000000, 'Male', 57),
(2, 'Marlon Brando', 1924, 'American', 2, 1944, 1.75, 100000000, 'Male', 60),
(3, 'Christian Bale', 1974, 'British', 1, 1986, 1.83, 120000000, 'Male', 35),
(4, 'John Travolta', 1954, 'American', 1, 1972, 1.88, 250000000, 'Male', 49),
(5, 'Elijah Wood', 1981, 'American', 0, 1989, 1.68, 30000000, 'Male', 32),
(6, 'Tom Hanks', 1956, 'American', 2, 1980, 1.83, 400000000, 'Male', 41),
(7, 'Leonardo DiCaprio', 1974, 'American', 1, 1991, 1.83, 260000000, 'Male', 30),
(8, 'Brad Pitt', 1963, 'American', 1, 1987, 1.80, 300000000, 'Male', 34),
(9, 'Keanu Reeves', 1964, 'Canadian', 0, 1985, 1.86, 360000000, 'Male', 36),
(10, 'Robert De Niro', 1943, 'American', 2, 1963, 1.77, 500000000, 'Male', 58),
(11, 'Mark Hamill', 1951, 'American', 0, 1970, 1.75, 18000000, 'Male', 51),
(12, 'Ian McKellen', 1939, 'British', 1, 1961, 1.80, 55000000, 'Male', 60),
(13, 'Harrison Ford', 1942, 'American', 1, 1966, 1.85, 300000000, 'Male', 55),
(14, 'Viggo Mortensen', 1958, 'American', 0, 1985, 1.80, 30000000, 'Male', 36),
(15, 'Matthew McConaughey', 1969, 'American', 1, 1991, 1.82, 95000000, 'Male', 30),
(16, 'Song Kang-ho', 1967, 'South Korean', 0, 1996, 1.80, 20000000, 'Male', 25),
(17, 'Michael Clarke Duncan', 1957, 'American', 0, 1995, 1.96, 18000000, 'Male', 17),
(18, 'Russell Crowe', 1964, 'New Zealander', 1, 1985, 1.82, 95000000, 'Male', 36),
(19, 'James Earl Jones', 1931, 'American', 1, 1953, 1.87, 45000000, 'Male', 68),
(20, 'Anthony Hopkins', 1937, 'British', 2, 1960, 1.75, 160000000, 'Male', 61);