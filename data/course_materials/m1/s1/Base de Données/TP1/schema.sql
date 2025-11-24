CREATE TABLE IF NOT EXISTS hotel
(
	numhotel INTEGER PRIMARY KEY ASC, 
	nom TEXT NOT NULL, 
	ville TEXT NOT NULL, 
	etoiles INTEGER,
	CONSTRAINT nom_ville_unique UNIQUE (nom, ville)
);

CREATE TABLE IF NOT EXISTS client
(
	numclient INTEGER PRIMARY KEY ASC, 
	nom TEXT NOT NULL, 
	prenom VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS chambre
(
	numchambre INTEGER NOT NULL, 
	numhotel INTEGER  NOT NULL, etage INTEGER, 
	"type" VARCHAR(15), 
	prixnuitht REAL NOT NULL, 
	CONSTRAINT pk_chambre PRIMARY KEY (numchambre, numhotel),
	CONSTRAINT fk_chambre_hotel FOREIGN KEY (numhotel) REFERENCES hotel(numhotel)
);

CREATE TABLE IF NOT EXISTS occupation
(
  numclient INTEGER NOT NULL,
  numhotel INTEGER NOT NULL,
  numchambre INTEGER NOT NULL,
  datedepart DATE, -- NULL si inconnue
  datearrivee DATE NOT NULL,
  numoccup INTEGER PRIMARY KEY ASC,
  CONSTRAINT fk_occupation_chambre FOREIGN KEY (numchambre, numhotel)
      REFERENCES chambre (numchambre, numhotel),
  CONSTRAINT fk_occupation_client FOREIGN KEY (numclient)
      REFERENCES client (numclient) ON DELETE CASCADE,
  CONSTRAINT fk_occupation_hotel FOREIGN KEY (numhotel)
      REFERENCES hotel (numhotel) ON DELETE CASCADE ,
  CONSTRAINT occupation_check CHECK (datearrivee < datedepart)
);

CREATE TABLE IF NOT EXISTS reservation 
(
  numresa INTEGER primary key asc,
  numclient INTEGER NOT NULL,
  numchambre INTEGER NOT NULL,
  numhotel INTEGER NOT NULL,
  datearrivee DATE NOT NULL,
  datedepart DATE NOT NULL,
  CONSTRAINT fk_resa_chambre FOREIGN KEY (numchambre, numhotel)
      REFERENCES chambre(numchambre, numhotel) ON DELETE CASCADE,
  CONSTRAINT fk_resa_client FOREIGN KEY (numclient)
      REFERENCES client(numclient) ON DELETE CASCADE,
  CONSTRAINT fk_resa_hotel FOREIGN KEY (numhotel)
      REFERENCES hotel (numhotel) ON DELETE CASCADE,
  CONSTRAINT reservation_check CHECK (datearrivee < datedepart)
) ;

PRAGMA foreign_keys = ON;

