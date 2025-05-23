CREATE TABLE users (
	id INTEGER NOT NULL, 
	username VARCHAR(80) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(128) NOT NULL, role VARCHAR(20), 
	PRIMARY KEY (id), 
	UNIQUE (username), 
	UNIQUE (email)
);
CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
CREATE TABLE letters (
	id INTEGER NOT NULL, 
	header TEXT NOT NULL, 
	body TEXT NOT NULL, 
	PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS "office" (
	office_id INTEGER NOT NULL, 
	title VARCHAR(45), 
	office_precedence FLOAT, 
	office_body_id BIGINT NOT NULL, 
	PRIMARY KEY (office_id), 
	FOREIGN KEY(office_body_id) REFERENCES body (body_id)
);
CREATE TABLE IF NOT EXISTS "term" (
	termpersonid INTEGER NOT NULL, 
	termofficeid INTEGER NOT NULL, 
	start DATE, 
	"end" DATE, 
	ordinal VARCHAR(7), 
	PRIMARY KEY (termpersonid, termofficeid), 
	FOREIGN KEY(termofficeid) REFERENCES office (office_id), 
	FOREIGN KEY(termpersonid) REFERENCES person (personid)
);
CREATE TABLE IF NOT EXISTS "person" (
	personid INTEGER NOT NULL, 
	first VARCHAR(15), 
	last VARCHAR(30), 
	email VARCHAR(45), 
	phone VARCHAR(19), 
	apt VARCHAR(4), 
	PRIMARY KEY (personid), 
	CONSTRAINT uix_person_first_last UNIQUE (first, last)
);
CREATE TABLE IF NOT EXISTS "body" (
	"body_id"	INTEGER NOT NULL,
	"name"	VARCHAR(45) NOT NULL,
	"mission"	VARCHAR(512),
	"body_precedence"	FLOAT NOT NULL,
	PRIMARY KEY("body_id")
);
CREATE VIEW report_record AS

SELECT

    person.personid         AS person_id,

    person.first            AS first,

    person.last             AS last,

    person.email            AS email,

    person.phone            AS phone,

    person.apt              AS apt,

    term.start              AS start,

    term.end                AS end,

    term.ordinal            AS ordinal,

    term.termpersonid       AS term_person_id,

    term.termofficeid       AS term_office_id,

    office.office_id         AS office_id,

    office.title            AS title,

    office.office_precedence AS office_precedence,

    office.office_body_id     AS office_body_id,

    body.body_id             AS body_id,

    body.name               AS name,

    body.body_precedence     AS body_precedence

FROM

    term

JOIN

    office ON office.office_id = term.termofficeid

JOIN

    body ON body.body_id = office.office_body_id

JOIN

    person ON person.personid = term.termpersonid

ORDER BY

    body.body_precedence
/* report_record(person_id,"first","last",email,phone,apt,start,"end",ordinal,term_person_id,term_office_id,office_id,title,office_precedence,office_body_id,body_id,name,body_precedence) */;
