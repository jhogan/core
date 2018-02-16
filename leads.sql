create table leads(
    id int(6) unsigned auto_increment primary key,
    name varchar(255),
    email varchar(255),
    subject varchar(255),
    message text,
    emailed_at datetime default null 
)
